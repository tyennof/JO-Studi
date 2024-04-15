from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.forms import PasswordInput

from accounts.models import CustomUser


class ContactForm(forms.Form):
    email = forms.EmailField(label="Email")
    subject = forms.CharField(label="Objet", max_length=40)
    text = forms.CharField(label="Message", max_length=2000, widget=forms.Textarea)


class SignUpForm(UserCreationForm):

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email"]


class SignInForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=PasswordInput())
