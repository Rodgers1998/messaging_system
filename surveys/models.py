# surveys/models.py
from django.db import models
from beneficiaries.models import Beneficiary

class Survey(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class SurveyQuestion(models.Model):
    QUESTION_TYPES = [
        ('TEXT', 'Text'),
        ('CHOICE', 'Multiple Choice'),
    ]
    survey = models.ForeignKey(Survey, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='TEXT')
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.survey.title} Q{self.order + 1}: {self.text}"

class SurveyChoice(models.Model):
    question = models.ForeignKey(SurveyQuestion, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.question.text} - {self.text}"

class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response by {self.beneficiary.name} for {self.survey.title}"

class SurveyAnswer(models.Model):
    response = models.ForeignKey(SurveyResponse, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    # For TEXT questions
    text_answer = models.TextField(blank=True, null=True)
    # For CHOICE questions (store selected choice)
    choice_answer = models.ForeignKey(SurveyChoice, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Answer to Q{self.question.order + 1} by {self.response.beneficiary.name}"
