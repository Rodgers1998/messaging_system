from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime

from .forms import RegisterForm
from beneficiaries.models import Beneficiary
from messaging.models import Message
from messaging.services.messaging_service import send_message

# ---------- Auth Views ----------

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard_home')
    else:
        form = RegisterForm()
    return render(request, "messaging/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard_home')
    else:
        form = AuthenticationForm()
    return render(request, "messaging/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect('messaging:login')


# ---------- Dashboard View ----------

@login_required
def dashboard_home(request):
    return render(request, "messaging/home.html")


# ---------- Messaging Views ----------

@login_required
def messages_home(request):
    messages_list = Message.objects.all().order_by('-sent_at')[:50]
    return render(request, 'messages.html', {'messages': messages_list})


@login_required
def send_ui_message(request):
    if request.method == "POST":
        content = request.POST.get("content")
        channel = request.POST.get("channel")
        recipient_ids_raw = request.POST.get("recipient_ids")
        scheduled_for_raw = request.POST.get("scheduled_for")

        if not all([content, channel, recipient_ids_raw]):
            messages.error(request, "All fields except scheduled time are required.")
            return redirect('messaging:messages_home')

        recipient_ids = [rid.strip() for rid in recipient_ids_raw.split(",") if rid.strip().isdigit()]
        beneficiaries = Beneficiary.objects.filter(id__in=recipient_ids)

        if not beneficiaries.exists():
            messages.error(request, "No valid beneficiaries found.")
            return redirect('messaging:messages_home')

        scheduled_for = None
        if scheduled_for_raw:
            try:
                scheduled_for = datetime.strptime(scheduled_for_raw, "%Y-%m-%dT%H:%M")
                scheduled_for = timezone.make_aware(scheduled_for, timezone.get_current_timezone())
                if scheduled_for <= timezone.now():
                    messages.error(request, "Scheduled time must be in the future.")
                    return redirect('messaging:messages_home')
            except ValueError:
                messages.error(request, "Invalid scheduled time format.")
                return redirect('messaging:messages_home')

        for beneficiary in beneficiaries:
            message = Message.objects.create(
                recipient=beneficiary,
                content=content,
                channel=channel,
                status="PENDING",
                scheduled_for=scheduled_for
            )
            if not scheduled_for:
                send_message(message)

        messages.success(request, "Messages sent or scheduled successfully.")
        return redirect('messaging:messages_home')

    return redirect('messaging:messages_home')


@login_required
def schedule_message_view(request):
    return render(request, 'schedule_message.html')
