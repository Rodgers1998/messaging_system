import pandas as pd
import logging
import json
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.core.paginator import Paginator

from .forms import RegisterForm, BulkUploadForm, MessageForm
from beneficiaries.models import Beneficiary
from messaging.models import Message
from messaging.services.messaging_service import send_message

logger = logging.getLogger(__name__)

# ---------- Auth Views ----------
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard_home")
    else:
        form = RegisterForm()
    return render(request, "messaging/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("dashboard_home")
    else:
        form = AuthenticationForm()
    return render(request, "messaging/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("messaging:login")


# ---------- Dashboard ----------
@login_required
def dashboard_home(request):
    """Dashboard with KPIs, charts, and messages table"""

    group_by = request.GET.get("group_by", "month")  # day/week/month

    # Truncate period for aggregation
    if group_by == "day":
        trunc = TruncDay("sent_at")
        delta = timedelta(days=1)
    elif group_by == "week":
        trunc = TruncWeek("sent_at")
        delta = timedelta(weeks=1)
    else:
        trunc = TruncMonth("sent_at")
        delta = timedelta(days=30)

    # KPIs
    total_messages = Message.objects.count()
    sent_messages = Message.objects.filter(status="SENT").count()
    failed_messages = Message.objects.filter(status="FAILED").count()
    pending_messages = Message.objects.filter(status="PENDING").count()

    # Trend: messages over time
    messages_qs = Message.objects.filter(sent_at__isnull=False)
    messages_over_time = (
        messages_qs
        .annotate(period=trunc)
        .values("period", "status")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    # Generate continuous period list
    if messages_over_time:
        start = messages_over_time[0]["period"].date()
        end = messages_over_time[len(messages_over_time)-1]["period"].date()
    else:
        start = date.today() - delta
        end = date.today()

    labels = []
    current = start
    while current <= end:
        labels.append(current.strftime("%Y-%m-%d"))
        current += delta

    # Prepare trend data with zero-filling
    sent_data, failed_data = [], []
    for label in labels:
        sent_count = sum(
            m["count"] for m in messages_over_time
            if m["period"].strftime("%Y-%m-%d") == label and m["status"] == "SENT"
        )
        failed_count = sum(
            m["count"] for m in messages_over_time
            if m["period"].strftime("%Y-%m-%d") == label and m["status"] == "FAILED"
        )
        sent_data.append(sent_count)
        failed_data.append(failed_count)

    # Channel breakdown with zero-filling
    channel_stats = messages_qs.values("channel", "status").annotate(count=Count("id"))
    all_channels = set(c["channel"] for c in channel_stats if c["channel"])
    channel_labels = sorted(all_channels)
    channel_sent, channel_failed, channel_pending = [], [], []

    for ch in channel_labels:
        channel_sent.append(sum(c["count"] for c in channel_stats if c["channel"] == ch and c["status"] == "SENT"))
        channel_failed.append(sum(c["count"] for c in channel_stats if c["channel"] == ch and c["status"] == "FAILED"))
        channel_pending.append(sum(c["count"] for c in channel_stats if c["channel"] == ch and c["status"] == "PENDING"))

    # Recent messages table
    search_query = request.GET.get("q", "")
    messages_table = Message.objects.all()
    if search_query:
        messages_table = messages_table.filter(content__icontains=search_query)
    paginator = Paginator(messages_table.order_by("-sent_at"), 10)
    page_number = request.GET.get("page")
    messages_page = paginator.get_page(page_number)

    return render(request, "home.html", {
        # KPIs
        "total_messages": total_messages,
        "sent_messages": sent_messages,
        "failed_messages": failed_messages,
        "pending_messages": pending_messages,

        # Chart.js data
        "chart_labels": json.dumps(labels),
        "sent_data": json.dumps(sent_data),
        "failed_data": json.dumps(failed_data),
        "channel_labels": json.dumps(channel_labels),
        "channel_sent": json.dumps(channel_sent),
        "channel_failed": json.dumps(channel_failed),
        "channel_pending": json.dumps(channel_pending),

        # Messages table
        "messages": messages_page,
        "search_query": search_query,
        "group_by": group_by,
    })


# ---------- Messaging ----------
@login_required
def messages_home(request):
    messages_list = Message.objects.all().order_by("-sent_at")[:50]
    beneficiaries = Beneficiary.objects.all()
    return render(request, "messages.html", {
        "messages_list": messages_list,   # renamed: avoid overwriting Django flash messages
        "beneficiaries": beneficiaries,
        "message_form": MessageForm(),
        "upload_form": BulkUploadForm(),
    })


@login_required
def send_ui_message(request):
    if request.method != "POST":
        return redirect("messaging:messages_home")

    form = MessageForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Please correct the errors in the form.")
        return redirect("messaging:messages_home")

    content = form.cleaned_data["content"]
    channel = form.cleaned_data["channel"].upper()
    media = form.cleaned_data.get("media")
    media_url = form.cleaned_data.get("media_url")
    beneficiary = form.cleaned_data["recipient"]
    scheduled_for = form.cleaned_data.get("scheduled_for")

    if scheduled_for:
        if timezone.is_naive(scheduled_for):
            scheduled_for = timezone.make_aware(scheduled_for, timezone.get_current_timezone())
        if scheduled_for <= timezone.now():
            messages.error(request, "Scheduled time must be in the future.")
            return redirect("messaging:messages_home")

    personalized_content = content.replace("{{1}}", beneficiary.name)
    message = Message.objects.create(
        recipient=beneficiary,
        content=personalized_content,
        channel=channel,
        media=media if media else None,
        media_url=media_url,
        status="PENDING",
        scheduled_for=scheduled_for,
    )

    if not scheduled_for:
        try:
            logger.info(f"Sending message to {beneficiary.phone_number} via {channel}")
            success, response = send_message(message)
            logger.info(f"Send result: success={success}, response={response}")
            if success:
                message.status = "SENT"
                message.sent_at = timezone.now()
                message.save()
                messages.success(request, f"Message sent successfully to {beneficiary.name}.")
            else:
                message.status = "FAILED"
                message.save()
                messages.error(request, f"Failed to send message to {beneficiary.name}.")
        except Exception as e:
            logger.exception(f"Failed to send message to {beneficiary.phone_number}")
            message.status = "FAILED"
            message.save()
            messages.error(request, f"Error while sending message to {beneficiary.name}.")
    else:
        messages.success(request, "Message scheduled successfully.")

    return redirect("messaging:messages_home")


@login_required
def upload_recipients_view(request):
    if request.method != "POST":
        return redirect("messaging:messages_home")

    form = BulkUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Invalid file upload.")
        return redirect("messaging:messages_home")

    file = form.cleaned_data.get("file")
    content = form.cleaned_data.get("content")
    channel = form.cleaned_data.get("channel").upper()
    media = form.cleaned_data.get("media")
    media_url = form.cleaned_data.get("media_url")

    try:
        data = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    except Exception as e:
        logger.error(f"File read error: {str(e)}")
        messages.error(request, "Could not read file. Ensure it's a valid CSV/Excel.")
        return redirect("messaging:messages_home")

    created_count, sent_count, failed_count = 0, 0, 0
    for _, row in data.iterrows():
        name = str(row.get("name", "")).strip()
        phone = str(row.get("phone_number", "")).strip()
        if not phone:
            continue

        beneficiary, created = Beneficiary.objects.get_or_create(
            phone_number=phone,
            defaults={"name": name or "Recipient"},
        )
        if created:
            created_count += 1

        if content:
            personalized_content = content.replace("{{1}}", beneficiary.name)
            message = Message.objects.create(
                recipient=beneficiary,
                content=personalized_content,
                channel=channel,
                media=media if media else None,
                media_url=media_url,
                status="PENDING",
            )
            try:
                success, response = send_message(message)
                if success:
                    message.status = "SENT"
                    message.sent_at = timezone.now()
                    message.save()
                    sent_count += 1
                else:
                    message.status = "FAILED"
                    message.save()
                    failed_count += 1
            except Exception as e:
                logger.exception(f"Failed to send message to {beneficiary.phone_number}")
                message.status = "FAILED"
                message.save()
                failed_count += 1

    if content:
        messages.success(
            request,
            f"Uploaded {created_count} new recipients. Sent: {sent_count}, Failed: {failed_count}.",
        )
    else:
        messages.success(request, f"Successfully uploaded {created_count} new recipients.")

    return redirect("messaging:messages_home")


@login_required
def schedule_message_view(request):
    return render(request, "schedule_message.html")