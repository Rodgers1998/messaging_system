from django.urls import path
from . import views

app_name = "survey"

urlpatterns = [
    path("", views.survey_setup, name="survey_home"),
    path("setup/", views.survey_setup, name="setup"),
    path("start/", views.start_survey, name="start"),
    path("test-send/", views.send_test, name="test_send"),
    path("whatsapp/webhook/", views.whatsapp_webhook, name="whatsapp_webhook"),  # from earlier
]
