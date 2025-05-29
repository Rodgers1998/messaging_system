from django.urls import path
from .views import messages_home, send_ui_message, schedule_message_view

urlpatterns = [
    path('', messages_home, name='messages_home'),
    path('send-ui/', send_ui_message, name='send_ui_message'),
    path('schedule/', schedule_message_view, name='schedule_message'),
]
