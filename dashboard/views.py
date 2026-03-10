# dashboard/views.py
import json
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, Coalesce
from django.db.models import Value
from django.utils.timezone import now
from messaging.models import Message
from beneficiaries.models import Beneficiary

def dashboard_home(request):
    # Summary stats
    total_messages = Message.objects.count()
    sent_messages = Message.objects.filter(status='SENT').count()
    failed_messages = Message.objects.filter(status='FAILED').count()
    pending_messages = Message.objects.filter(status='PENDING').count()
    total_beneficiaries = Beneficiary.objects.count()

    # Search
    search_query = request.GET.get("q", "")
    messages_list = Message.objects.annotate(
        order_time=Coalesce('sent_at', 'scheduled_for', Value(now()))
    ).order_by('-order_time')

    if search_query:
        messages_list = messages_list.filter(content__icontains=search_query)

    # Pagination
    paginator = Paginator(messages_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Analytics grouping
    group_by = request.GET.get("group_by", "month")
    if group_by == "day":
        trunc_func = TruncDay("sent_at")
    elif group_by == "week":
        trunc_func = TruncWeek("sent_at")
    else:
        trunc_func = TruncMonth("sent_at")

    analytics = (
        Message.objects.filter(sent_at__isnull=False)
        .annotate(period=trunc_func)
        .values("period", "status")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    chart_labels_raw = sorted(list(set([
        a["period"].strftime("%Y-%m-%d") for a in analytics
    ])))

    sent_data = []
    failed_data = []
    for label in chart_labels_raw:
        sent_data.append(next(
            (a["count"] for a in analytics
             if a["period"].strftime("%Y-%m-%d") == label and a["status"] == "SENT"), 0
        ))
        failed_data.append(next(
            (a["count"] for a in analytics
             if a["period"].strftime("%Y-%m-%d") == label and a["status"] == "FAILED"), 0
        ))

    context = {
        'total_messages': total_messages,
        'sent_messages': sent_messages,
        'failed_messages': failed_messages,
        'pending_messages': pending_messages,
        'total_beneficiaries': total_beneficiaries,
        'messages': page_obj,
        'search_query': search_query,
        'group_by': group_by,

        # Serialized for Chart.js — must be JSON strings
        'chart_labels': json.dumps(chart_labels_raw),
        'sent_data': json.dumps(sent_data),
        'failed_data': json.dumps(failed_data),
    }

    return render(request, 'home.html', context)