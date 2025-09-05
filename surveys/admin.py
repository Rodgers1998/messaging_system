from django.contrib import admin
from .models import Survey, Question, Choice, Response, Answer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "survey", "question_type")
    list_filter = ("survey", "question_type")
    search_fields = ("text",)
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question")
    search_fields = ("text",)


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question", "answer_text")


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("survey", "beneficiary", "submitted_at")
    list_filter = ("survey", "submitted_at")
    search_fields = ("beneficiary__name", "survey__title")
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("question", "answer_text", "response")
    search_fields = ("answer_text", "question__text")
