from django.shortcuts import render
from django.core.paginator import Paginator
from messaging.models import Message
from beneficiaries.models import Beneficiary
from django.db.models.functions import Coalesce
from django.db.models import Value
from django.utils.timezone import now

def dashboard_home(request):
    # Summary stats
    total_messages = Message.objects.count()
    sent_messages = Message.objects.filter(status='SENT').count()
    pending_messages = Message.objects.filter(status='PENDING').count()
    total_beneficiaries = Beneficiary.objects.count()

    # Order messages: recently sent first
    # Fallback to scheduled_for or created time if sent_at is null
    messages_list = (
        Message.objects
        .annotate(order_time=Coalesce('sent_at', 'scheduled_for', Value(now())))
        .order_by('-order_time')
    )

    # Paginate - 50 messages per page
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'total_messages': total_messages,
        'sent_messages': sent_messages,
        'pending_messages': pending_messages,
        'total_beneficiaries': total_beneficiaries,
        'messages': page_obj,
    }

    return render(request, 'home.html', context)
