# surveys/models.py
from django.db import models
from beneficiaries.models import Beneficiary


class Survey(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = [
        ("TEXT", "Text Input"),
        ("CHOICE", "Multiple Choice"),
    ]
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default="TEXT")

    def __str__(self):
        return f"{self.survey.title} - {self.text}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.question.text} - {self.text}"


class Response(models.Model):
    CHANNEL_CHOICES = [
        ("SMS", "SMS"),
        ("WHATSAPP", "WhatsApp"),
        ("WHATSAPP_TEMPLATE", "WhatsApp Template"),
    ]
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="responses")
    beneficiary = models.ForeignKey(
        Beneficiary, on_delete=models.CASCADE, related_name="responses",
        null=True, blank=True  # allow null for test sends
    )
    # Track which channel this response came through
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="WHATSAPP")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        name = self.beneficiary.name if self.beneficiary else "Test"
        return f"Response by {name} to {self.survey.title} via {self.channel}"


class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.question.text} - {self.answer_text}"