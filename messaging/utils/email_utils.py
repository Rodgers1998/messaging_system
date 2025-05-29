from django.core.mail import send_mail

def send_email_message(to_email, content):
    try:
        send_mail(
            subject="SHOFCO Survey Invitation",
            message=content,
            from_email="noreply@shofco.org",  # 🔁 Customize as needed
            recipient_list=[to_email],
            fail_silently=False,
        )
        return True, "EMAIL_SENT"
    except Exception as e:
        return False, str(e)
