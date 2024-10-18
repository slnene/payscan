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




class RegisterForm(forms.Form):
    email = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
    first_name =forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    otp = forms.CharField(max_length=6, required=True)
  
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match")
        

class DepositForm(forms.Form):
    amount = forms.DecimalField()

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError('Amount must be greater than SZL 0.00')
        return amount
    

class WithdrawForm(forms.Form):
    amount = forms.DecimalField()

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError('Amount must be greater than SZL 0.00')
        if self.balance is not None and amount > self.balance:
            raise ValidationError('Insufficient Funds')
        return amount

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
        if self.balance is not None and amount > self.balance:
            raise ValidationError('Insufficient Funds')
        return amount


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)
