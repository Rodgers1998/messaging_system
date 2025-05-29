from django.shortcuts import render, redirect
from beneficiaries.models import Beneficiary
from messaging.models import Message
from messaging.services.messaging_service import send_message
from django.contrib import messages
from django.utils import timezone
from datetime import datetime

def messages_home(request):
    # Show last 50 messages sorted by sent date descending
    messages_list = Message.objects.all().order_by('-sent_at')[:50]
    return render(request, 'messages.html', {'messages': messages_list})

def send_ui_message(request):
    if request.method == "POST":
        content = request.POST.get("content")
        channel = request.POST.get("channel")
        recipient_ids_raw = request.POST.get("recipient_ids")
        scheduled_for_raw = request.POST.get("scheduled_for")

        # Validate required fields except scheduled_for
        if not all([content, channel, recipient_ids_raw]):
            messages.error(request, "All fields except scheduled time are required.")
            return redirect('messaging:messages_home')


        # Parse and clean recipient ids
        recipient_ids = [rid.strip() for rid in recipient_ids_raw.split(",") if rid.strip().isdigit()]
        beneficiaries = Beneficiary.objects.filter(id__in=recipient_ids)

        if not beneficiaries.exists():
            messages.error(request, "No valid beneficiaries found.")
            return redirect('messaging:messages_home')


        scheduled_for = None
        if scheduled_for_raw:
            try:
                # Expect datetime-local input format: 'YYYY-MM-DDTHH:MM'
                scheduled_for = datetime.strptime(scheduled_for_raw, "%Y-%m-%dT%H:%M")
                # Convert naive datetime to aware using current timezone
                scheduled_for = timezone.make_aware(scheduled_for, timezone.get_current_timezone())
                if scheduled_for <= timezone.now():
                    messages.error(request, "Scheduled time must be in the future.")
                    return redirect('messaging:messages_home')

            except ValueError:
                messages.error(request, "Invalid scheduled time format.")
                return redirect('messaging:messages_home')


        # Create messages and either send immediately or schedule
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


def schedule_message_view(request):
    # Render a page for scheduling messages if needed
    return render(request, 'schedule_message.html')
