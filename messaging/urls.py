from django.urls import path
from . import views  # Import views correctly

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard_home, name="dashboard_home"),  # Corrected name
    path("messages/", views.messages_home, name="messages_home"),  # Separate messaging view
    path("send-ui/", views.send_ui_message, name="send_ui_message"),
    path("schedule/", views.schedule_message_view, name="schedule_message"),
]
