from django import forms
from django.core.exceptions import ValidationError
from users.models import PayscanUser
from businesses.models import Business
from agents.models import Agent
from payscan.models import Transaction

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate




class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Pin", strip=False, widget=forms.PasswordInput)
