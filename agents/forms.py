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
#####AGENT#####

class AgentRegisterForm(UserCreationForm):
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
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Agent.objects.filter(agentuser__user__username=username).exists():
            raise ValidationError('Username already exists.')
        return username

      
class AgentLoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']



class AgentBusinessRegistrationForm(forms.Form):
    business_name = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
    owner_email = forms.CharField(max_length=100)
    owner_first_name = forms.CharField(max_length=100)
    owner_last_name = forms.CharField(max_length=100)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
  

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match")

    def clean_business_name(self):
        business_name = self.cleaned_data.get('business_name')
        if Business.objects.filter(name=business_name).exists():
            raise ValidationError('Business name already registered.')
        
        return business_name
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Business.objects.filter(name=username).exists():
            raise ValidationError('Phine already registered.')
        return username