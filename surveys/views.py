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
from messaging.utils.infobip import send_whatsapp_via_infobip


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

    qs = Response.objects.select_related("beneficiary", "survey").prefetch_related("answers__question").order_by('-submitted_at')
    q = request.GET.get('q')
    if q:
        qs = qs.filter(
            Q(beneficiary__phone_number__icontains=q) |
            Q(beneficiary__name__icontains=q)
        )

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, "survey_setup.html", {
        "beneficiaries": beneficiaries,
        "surveys": surveys,
        "selected_survey": selected_survey,
        "responses": page_obj.object_list,
        "page_obj": page_obj,
    })


@login_required
@require_http_methods(["POST"])
def start_survey(request):
    survey_id = request.POST.get("survey_id")
    ids = request.POST.getlist("recipients")

    if not survey_id or not ids:
        messages.error(request, "Select a survey and at least one beneficiary.")
        return redirect("survey:setup")

    try:
        survey = Survey.objects.prefetch_related("questions__choices").get(id=survey_id)
    except Survey.DoesNotExist:
        messages.error(request, "Selected survey does not exist.")
        return redirect("survey:setup")

    for b in Beneficiary.objects.filter(id__in=ids):
        response, _ = Response.objects.get_or_create(survey=survey, beneficiary=b)

        # Initialize all answers as blank if not already created
        for question in survey.questions.all():
            Answer.objects.get_or_create(response=response, question=question)

        # Send intro + first question
        send_whatsapp_via_infobip(
            b.phone_number,
            f"👋 Hello {b.name}, please answer the following survey questions for {survey.title}:"
        )
        send_next_question(response, b.phone_number)

    messages.success(request, "Survey sent to selected beneficiaries.")
    return redirect("survey:setup")


@login_required
@require_http_methods(["POST"])
def send_test(request):
    msisdn = request.POST.get("test_msisdn", "").strip()
    survey_id = request.POST.get("survey_id")
    if not msisdn or not survey_id:
        messages.error(request, "Provide a phone number and select a survey.")
        return redirect("survey:setup")

    try:
        survey = Survey.objects.prefetch_related("questions__choices").get(id=survey_id)
    except Survey.DoesNotExist:
        messages.error(request, "Selected survey does not exist.")
        return redirect("survey:setup")

    response = Response.objects.create(survey=survey, beneficiary=None)
    for question in survey.questions.all():
        Answer.objects.create(response=response, question=question)

    send_whatsapp_via_infobip(
        msisdn,
        f"👋 Hello, please answer the following survey questions for {survey.title}:"
    )
    send_next_question(response, msisdn)

    messages.success(request, f"Test survey sent to {msisdn}.")
    return redirect("survey:setup")


def send_next_question(response, msisdn):
    """Send the next unanswered question"""
    next_answer = response.answers.filter(answer_text__isnull=True).order_by('id').first()
    if not next_answer:
        send_whatsapp_via_infobip(msisdn, "✅ You’ve completed the survey. Thank you!")
        return

    question = next_answer.question
    if question.question_type == "TEXT":
        msg = f"{question.text}\n\nReply with your answer."
    elif question.question_type == "CHOICE":
        choices = list(question.choices.all().order_by('id'))
        msg = f"{question.text}\n"
        for idx, c in enumerate(choices, start=1):
            msg += f"{idx}) {c.text}\n"
        msg += "\nReply with the number of your choice."
    else:
        msg = question.text

    send_whatsapp_via_infobip(msisdn, msg)


@csrf_exempt
def whatsapp_webhook(request):
    if request.method != "POST":
        return HttpResponse("Webhook active", status=200)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        message = payload.get("results", [])[0]
        msisdn = message.get("from", "")
        text = message.get("message", {}).get("text", {}).get("body", "").strip()

        if not (msisdn and text):
            return JsonResponse({"error": "Invalid payload"}, status=400)

        try:
            beneficiary = Beneficiary.objects.get(phone_number=msisdn)
        except Beneficiary.DoesNotExist:
            return JsonResponse({"error": "Beneficiary not found"}, status=404)

        # Get the latest active survey for this beneficiary
        response = Response.objects.filter(
            beneficiary=beneficiary
        ).prefetch_related('answers__question', 'answers__question__choices').order_by('-id').first()

        if not response:
            send_whatsapp_via_infobip(msisdn, "✅ You have no active surveys. Thank you!")
            return JsonResponse({"status": "no_active_survey"})

        # Get the next unanswered answer
        current_answer = response.answers.filter(answer_text__isnull=True).order_by('id').first()
        if not current_answer:
            send_whatsapp_via_infobip(msisdn, "✅ You’ve already completed this survey. Thank you!")
            return JsonResponse({"status": "completed"})

        question = current_answer.question

        # Save answer
        if question.question_type == "CHOICE":
            try:
                choice_number = int(text)
                choices = list(question.choices.all().order_by('id'))
                if 1 <= choice_number <= len(choices):
                    current_answer.answer_text = choices[choice_number - 1].text
                else:
                    send_whatsapp_via_infobip(msisdn, "⚠️ Invalid choice. Reply with a valid number.")
                    return JsonResponse({"status": "invalid_choice"})
            except ValueError:
                send_whatsapp_via_infobip(msisdn, "⚠️ Invalid input. Reply with the number of your choice.")
                return JsonResponse({"status": "invalid_choice"})
        else:
            current_answer.answer_text = text

        current_answer.save()

        # Update response timestamp
        response.submitted_at = timezone.now()
        response.save()

        # Send next question
        send_next_question(response, msisdn)
        return JsonResponse({"status": "ok"})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
