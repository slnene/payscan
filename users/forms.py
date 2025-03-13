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
import re

class RegisterForm(forms.Form):
    email = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100, help_text="Enter your phone number in E.164 format (e.g., +26812345678).")  # Phone number
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)

    def clean_username(self):
        username = self.cleaned_data.get('username')
          
        if Business.objects.filter(name=username).exists():
            raise ValidationError('Phone Number already exists.')
    
        # Regex pattern for E.164 phone number format
        pattern = r'^\+268\d{8}$'
        if not re.match(pattern, username):
            raise ValidationError("Phone number must be in E.164 format (e.g., +26812345678).")
        return username

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

class PaymentForm(forms.Form):
    business = forms.ModelChoiceField(queryset=Business.objects.all())
    amount = forms.DecimalField()

    def __init__(self, *args, **kwargs):
        self.balance = kwargs.pop('balance', None)
        super(PaymentForm, self).__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError('Amount must be greater than SZL 0.00')
       
        return amount


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)
