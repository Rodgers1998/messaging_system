from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    path('', views.survey_home, name='survey_home'),      # home redirects to list
    path('list/', views.survey_list, name='survey_list'), # list all surveys
    path('take/<int:survey_id>/', views.take_survey, name='take_survey'),
]
