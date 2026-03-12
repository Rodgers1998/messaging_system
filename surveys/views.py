# surveys/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from beneficiaries.models import Beneficiary
from .models import Survey, Question, Choice, Response, Answer
from messaging.utils.infobip import (
    send_whatsapp_via_infobip,
    send_whatsapp_template_via_infobip,
    send_sms_via_infobip,
    _format_phone,
)


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _send_message(channel: str, phone: str, text: str, template_name: str = None, template_data: dict = None):
    """Unified send — routes to SMS, WhatsApp text, or WhatsApp template."""
    if channel == "SMS":
        return send_sms_via_infobip(phone, text)
    elif channel == "WHATSAPP_TEMPLATE":
        return send_whatsapp_template_via_infobip(
            phone,
            template_name=template_name or "survey_invite",
            template_data=template_data or {},
        )
    else:  # default WHATSAPP
        return send_whatsapp_via_infobip(phone, text)


def send_next_question(response: Response, phone: str):
    """Send the next unanswered question via the response's channel."""
    next_answer = response.answers.filter(
        answer_text__isnull=True
    ).order_by('id').first()

    if not next_answer:
        _send_message(response.channel, phone, "✅ You have completed the survey. Thank you!")
        return

    question = next_answer.question
    if question.question_type == "TEXT":
        msg = f"{question.text}\n\nReply with your answer."
    elif question.question_type == "CHOICE":
        choices = list(question.choices.all().order_by('id'))
        msg = f"{question.text}\n\n"
        for idx, c in enumerate(choices, start=1):
            msg += f"{idx}) {c.text}\n"
        msg += "\nReply with the number of your choice."
    else:
        msg = question.text

    _send_message(response.channel, phone, msg)


# ─────────────────────────────────────────────
#  Views
# ─────────────────────────────────────────────

@login_required
def survey_setup(request):
    beneficiaries = Beneficiary.objects.all().order_by('id')
    surveys = Survey.objects.prefetch_related("questions__choices").all().order_by('id')

    survey_id = request.GET.get("survey_id")
    selected_survey = None
    if survey_id:
        try:
            selected_survey = surveys.get(id=survey_id)
        except Survey.DoesNotExist:
            selected_survey = surveys.first()
    else:
        selected_survey = surveys.first()

    # Filter responses by selected survey
    qs = Response.objects.select_related("beneficiary", "survey").prefetch_related(
        "answers__question__choices"
    ).order_by('-submitted_at')

    if selected_survey:
        qs = qs.filter(survey=selected_survey)

    q = request.GET.get('q')
    if q:
        qs = qs.filter(
            Q(beneficiary__phone_number__icontains=q) |
            Q(beneficiary__name__icontains=q)
        )

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Pre-compute response stats (Django templates can't do counters in loops)
    enriched_responses = []
    for r in page_obj.object_list:
        answers = list(r.answers.all())
        total = len(answers)
        answered = sum(1 for a in answers if a.answer_text)
        unanswered = total - answered
        display_name = r.beneficiary.name if r.beneficiary else "Test"
        for a in answers:
            if "name" in a.question.text.lower() and a.answer_text:
                display_name = a.answer_text
                break
        enriched_responses.append({
            "response": r,
            "phone": r.beneficiary.phone_number if r.beneficiary else "—",
            "name": display_name,
            "channel": r.channel,
            "unanswered": unanswered,
            "total": total,
            "done": unanswered == 0,
            "submitted_at": r.submitted_at,
        })

    return render(request, "survey_setup.html", {
        "beneficiaries": beneficiaries,
        "surveys": surveys,
        "selected_survey": selected_survey,
        "enriched_responses": enriched_responses,
        "page_obj": page_obj,
    })


@login_required
@require_http_methods(["POST"])
def start_survey(request):
    survey_id = request.POST.get("survey_id")
    ids = request.POST.getlist("recipients")
    channel = request.POST.get("channel", "WHATSAPP").upper()
    template_name = request.POST.get("template_name", "").strip()

    if not survey_id or not ids:
        messages.error(request, "Select a survey and at least one beneficiary.")
        return redirect("survey:setup")

    if channel == "WHATSAPP_TEMPLATE" and not template_name:
        messages.error(request, "Please enter your approved WhatsApp template name.")
        return redirect("survey:setup")

    try:
        survey = Survey.objects.prefetch_related("questions__choices").get(id=survey_id)
    except Survey.DoesNotExist:
        messages.error(request, "Selected survey does not exist.")
        return redirect("survey:setup")

    sent_count = 0
    for b in Beneficiary.objects.filter(id__in=ids):
        response, _ = Response.objects.get_or_create(
            survey=survey,
            beneficiary=b,
            channel=channel,
        )
        for question in survey.questions.all():
            Answer.objects.get_or_create(response=response, question=question)

        # Send intro message
        intro = f"Hello {b.name}, you have been invited to answer the *{survey.title}* survey. Please reply to each question."

        if channel == "WHATSAPP_TEMPLATE":
            # Use approved template for the intro — bypasses 24hr window
            send_whatsapp_template_via_infobip(
                b.phone_number,
                template_name=template_name,
                template_data={"body": {"placeholders": [b.name, survey.title]}},
            )
        else:
            _send_message(channel, b.phone_number, intro)

        # Send first question
        send_next_question(response, b.phone_number)
        sent_count += 1

    messages.success(request, f"Survey sent to {sent_count} beneficiary(s) via {channel}.")
    return redirect("survey:setup")


@login_required
@require_http_methods(["POST"])
def send_test(request):
    msisdn = request.POST.get("test_msisdn", "").strip()
    survey_id = request.POST.get("survey_id")
    channel = request.POST.get("channel", "WHATSAPP").upper()

    if not msisdn or not survey_id:
        messages.error(request, "Provide a phone number and select a survey.")
        return redirect("survey:setup")

    msisdn = _format_phone(msisdn)

    try:
        survey = Survey.objects.prefetch_related("questions__choices").get(id=survey_id)
    except Survey.DoesNotExist:
        messages.error(request, "Selected survey does not exist.")
        return redirect("survey:setup")

    test_beneficiary, _ = Beneficiary.objects.get_or_create(
        phone_number=msisdn,
        defaults={"name": "Test User"}
    )

    response, created = Response.objects.get_or_create(
        survey=survey,
        beneficiary=test_beneficiary,
        channel=channel,
    )
    if created:
        for question in survey.questions.all():
            Answer.objects.get_or_create(response=response, question=question)

    _send_message(channel, msisdn, f"👋 Hello, this is a TEST of *{survey.title}*. Please answer each question:")
    send_next_question(response, msisdn)

    messages.success(request, f"Test survey sent to {msisdn} via {channel}.")
    return redirect("survey:setup")


# ─────────────────────────────────────────────
#  Webhooks — shared processing logic
# ─────────────────────────────────────────────

def _process_survey_reply(msisdn_raw: str, text: str, channel: str):
    """
    Shared logic for processing an incoming reply from either SMS or WhatsApp.
    Returns a (status_string, http_status_code) tuple.
    """
    msisdn = _format_phone(msisdn_raw)

    # Look up beneficiary
    try:
        beneficiary = Beneficiary.objects.get(phone_number=msisdn)
    except Beneficiary.DoesNotExist:
        try:
            beneficiary = Beneficiary.objects.get(phone_number=msisdn.lstrip("+"))
        except Beneficiary.DoesNotExist:
            _send_message(channel, msisdn, "Sorry, we couldn't find your details. Please contact SHOFCO.")
            return "beneficiary_not_found", 404

    # Find latest active response for this channel
    response = Response.objects.filter(
        beneficiary=beneficiary,
        channel=channel,
        answers__answer_text__isnull=True,
    ).prefetch_related(
        'answers__question__choices'
    ).order_by('-id').first()

    if not response:
        _send_message(channel, msisdn, "✅ You have no active surveys at the moment. Thank you!")
        return "no_active_survey", 200

    current_answer = response.answers.filter(
        answer_text__isnull=True
    ).order_by('id').first()

    if not current_answer:
        _send_message(channel, msisdn, "✅ You have already completed this survey. Thank you!")
        return "already_completed", 200

    question = current_answer.question

    # Validate and save answer
    if question.question_type == "CHOICE":
        try:
            choice_number = int(text.strip())
            choices = list(question.choices.all().order_by('id'))
            if 1 <= choice_number <= len(choices):
                current_answer.answer_text = choices[choice_number - 1].text
            else:
                _send_message(channel, msisdn, f"⚠️ Please reply with a number between 1 and {len(choices)}.")
                return "invalid_choice", 200
        except ValueError:
            _send_message(channel, msisdn, "⚠️ Please reply with the number of your choice (e.g. 1, 2, 3).")
            return "invalid_input", 200
    else:
        current_answer.answer_text = text.strip()

    current_answer.save()
    response.submitted_at = timezone.now()
    response.save(update_fields=["submitted_at"])

    send_next_question(response, msisdn)
    return "ok", 200


@csrf_exempt
def whatsapp_webhook(request):
    """Receives incoming WhatsApp replies from Infobip."""
    if request.method == "GET":
        return HttpResponse("Webhook active", status=200)
    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        results = payload.get("results", [])
        if not results:
            return JsonResponse({"status": "no_results"}, status=200)

        message = results[0]
        msisdn = message.get("from", "")
        text = message.get("message", {}).get("text", {}).get("body", "").strip()

        if not (msisdn and text):
            return JsonResponse({"error": "Invalid payload"}, status=400)

        status, code = _process_survey_reply(msisdn, text, channel="WHATSAPP")
        return JsonResponse({"status": status}, status=code if code != 404 else 200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def sms_webhook(request):
    """
    Receives incoming SMS replies from Infobip.
    Register this URL in: Infobip → Channels → SMS → your sender → Incoming messages webhook
    URL: https://your-domain.com/surveys/sms/webhook/

    Infobip SMS incoming payload:
    {
      "results": [{
        "from": "254712345678",
        "to": "SHOFCOKENYA",
        "message": { "text": "1" },
        ...
      }]
    }
    """
    if request.method == "GET":
        return HttpResponse("SMS Webhook active", status=200)
    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        results = payload.get("results", [])
        if not results:
            return JsonResponse({"status": "no_results"}, status=200)

        message = results[0]
        msisdn = message.get("from", "")
        # Infobip SMS payload uses same structure as WhatsApp
        text = (
            message.get("message", {}).get("text", "")
            or message.get("text", "")   # fallback for some payload variants
        ).strip()

        if not (msisdn and text):
            return JsonResponse({"error": "Invalid payload"}, status=400)

        status, code = _process_survey_reply(msisdn, text, channel="SMS")
        return JsonResponse({"status": status}, status=code if code != 404 else 200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)