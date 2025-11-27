from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User



class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username"}
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )

class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "role", "phone_number", "email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class UserUpdateForm(UserChangeForm):
    password = None  # Exclude password field for update form by default

    class Meta:
        model = User
        fields = ("username", "role", "phone_number", "email", "first_name", "last_name", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
