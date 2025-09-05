from django.db import models
from beneficiaries.models import Beneficiary


class Survey(models.Model):
    """A survey definition (e.g. WhatsApp Gender & Name Survey)."""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    """Questions belonging to a survey."""
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
    """Choices for multiple-choice questions."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.question.text} - {self.text}"


class Response(models.Model):
    """A survey response from a beneficiary."""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="responses")
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name="responses")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response by {self.beneficiary.name} to {self.survey.title}"


class Answer(models.Model):
    """An answer to a specific question in a response."""
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.question.text} - {self.answer_text}"
