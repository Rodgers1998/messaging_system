from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Message
import os
import mimetypes


# ---------- Auth Forms ----------
class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your email"
        })
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter username"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter password"
        })
    )


# ---------- Messaging Forms ----------
class MessageForm(forms.ModelForm):
    """Form for sending a single message (with optional media & scheduling)."""

    scheduled_for = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            "type": "datetime-local",
            "class": "form-control"
        }),
        help_text="Leave blank to send immediately."
    )

    class Meta:
        model = Message
        fields = ["recipient", "content", "channel", "media", "scheduled_for"]
        widgets = {
            "recipient": forms.Select(attrs={"class": "form-select"}),
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Type your message here...",
                "rows": 3
            }),
            "channel": forms.Select(attrs={"class": "form-select"}),
            "media": forms.ClearableFileInput(attrs={"class": "form-control"})
        }

    def clean_scheduled_for(self):
        scheduled = self.cleaned_data.get("scheduled_for")

        # If no schedule provided, default to now
        if not scheduled:
            return timezone.now()

        # Prevent scheduling in the past
        if scheduled < timezone.now():
            raise forms.ValidationError("Scheduled time must be in the future.")
        return scheduled


class BulkUploadForm(forms.Form):
    """Form for uploading CSV/Excel file with recipients and messages."""

    file = forms.FileField(
        help_text="Upload a CSV or Excel file with at least name and phone_number.",
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control",
            "accept": ".csv,.xls,.xlsx"
        })
    )
    channel = forms.ChoiceField(
        choices=Message.CHANNEL_CHOICES,
        initial="SMS",  # default
        widget=forms.Select(attrs={"class": "form-select"})
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "placeholder": "Default message to all recipients (optional)...",
            "rows": 3
        }),
        required=False
    )
    media = forms.FileField(
        required=False,
        help_text="Optional media attachment",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            mime, _ = mimetypes.guess_type(file.name)

            if ext not in [".csv", ".xls", ".xlsx"]:
                raise forms.ValidationError("Only CSV or Excel files are allowed.")

            if mime and not (
                mime.startswith("text")
                or mime.startswith("application/vnd.ms-excel")
                or mime.startswith("application/vnd.openxmlformats")
            ):
                raise forms.ValidationError("Invalid file type uploaded. Please upload a valid CSV or Excel file.")
        return file

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        content = cleaned_data.get("content")

        if not file and not content:
            raise forms.ValidationError("You must upload a file or provide a default message.")

        return cleaned_data
