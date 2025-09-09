# messaging/urls.py
from django.urls import path
from . import views  # Import views correctly

app_name = 'messaging'

urlpatterns = [
    # Auth routes
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboard
    path("", views.dashboard_home, name="dashboard_home"),

    # Messaging routes
    path("messages/", views.messages_home, name="messages_home"),
    path("send-ui/", views.send_ui_message, name="send_ui_message"),
    path("upload/", views.upload_recipients_view, name="upload_recipients_view"),
    path("schedule/", views.schedule_message_view, name="schedule_message"),
]
