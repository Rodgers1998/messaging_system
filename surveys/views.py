# surveys/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Survey, SurveyQuestion, SurveyResponse, SurveyAnswer
from beneficiaries.models import Beneficiary
from django.contrib.auth.decorators import login_required

@login_required
def survey_home(request):
    # For now, just redirect to survey_list
    return redirect('surveys:survey_list')

@login_required
def survey_list(request):
    surveys = Survey.objects.all()
    return render(request, 'survey_list.html', {'surveys': surveys})

@login_required
def take_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id)
    beneficiary = request.user.beneficiary  # assuming User linked to Beneficiary
    
    # Get or create a SurveyResponse for this user & survey
    response, created = SurveyResponse.objects.get_or_create(survey=survey, beneficiary=beneficiary)

    # Find next unanswered question
    answered_question_ids = response.answers.values_list('question_id', flat=True)
    next_question = survey.questions.exclude(id__in=answered_question_ids).order_by('order').first()

    if not next_question:
        # All questions answered, show completion
        return render(request, 'survey_complete.html', {'survey': survey})

    if request.method == 'POST':
        answer = request.POST.get('answer')
        if next_question.question_type == 'TEXT':
            SurveyAnswer.objects.create(
                response=response,
                question=next_question,
                text_answer=answer
            )
        elif next_question.question_type == 'CHOICE':
            choice = next_question.choices.filter(id=answer).first()
            if choice:
                SurveyAnswer.objects.create(
                    response=response,
                    question=next_question,
                    choice_answer=choice
                )
        return redirect('surveys:take_survey', survey_id=survey.id)

    # GET request - show question form
    context = {
        'survey': survey,
        'question': next_question,
    }
    return render(request, 'take_survey.html', context)
