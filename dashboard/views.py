from django.shortcuts import render
from django.core.paginator import Paginator
from messaging.models import Message
from beneficiaries.models import Beneficiary

def dashboard_home(request):
    # Summary stats
    total_messages = Message.objects.count()
    sent_messages = Message.objects.filter(status='SENT').count()
    pending_messages = Message.objects.filter(status='PENDING').count()
    total_beneficiaries = Beneficiary.objects.count()

    # Query all messages ordered by sent_at descending
    messages_list = Message.objects.all().order_by('-sent_at')

    # Paginate messages - 50 per page
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'total_messages': total_messages,
        'sent_messages': sent_messages,
        'pending_messages': pending_messages,
        'total_beneficiaries': total_beneficiaries,
        'messages': page_obj,  # pass the paginated page object to the template
    }

    return render(request, 'home.html', context)
