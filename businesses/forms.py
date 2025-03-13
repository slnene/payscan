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






#########business########9

class BusinessRegistrationForm(forms.Form):
    email = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)  # Phone number
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    business_name = forms.CharField(max_length=100)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        business_name = cleaned_data.get('business_name')

        # Check if the user already owns a business
        if self.user:
            payscan_user = PayscanUser.objects.get(user=self.user)
            if Business.objects.filter(owner=payscan_user).exists():
                raise forms.ValidationError("Phone number can only be registered to one business")

        return cleaned_data

    
    
    
class BusinessRegistrationForm_2(forms.Form):
    business_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your business name'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        business_name = cleaned_data.get('business_name')

        # Check if the user already owns a business
        if self.user:
            payscan_user = PayscanUser.objects.get(user=self.user)
            if Business.objects.filter(owner=payscan_user).exists():
                raise forms.ValidationError("Phone number can only be registered to one business")

        return cleaned_data


class BusinessLoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']



class BusinessPaymentForm(forms.Form):
    business = forms.ModelChoiceField(queryset=Business.objects.all())
    amount = forms.DecimalField()

    def __init__(self, *args, **kwargs):
        self.balance = kwargs.pop('balance', None)
        super(BusinessPaymentForm, self).__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError('Amount must be greater than SZL 0.00')
        if self.balance is not None and amount > self.balance:
            raise ValidationError('Insufficient Funds')
        return amount

class BusinessWithdrawForm(forms.Form):
    amount = forms.DecimalField()

    def __init__(self, *args, **kwargs):
        self.balance = kwargs.pop('balance', None)
        super(BusinessWithdrawForm, self).__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError('Amount must be greater than SZL 0.00')
        if self.balance is not None and amount > self.balance:
            raise ValidationError('Insufficient Funds')
        return amount

class RecievePaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def __init__(self, *args, **kwargs):
        self.balance = kwargs.pop('balance', None)
        super(BusinessPaymentForm, self).__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError('Amount must be greater than SZL 0.00')
        if self.balance is not None and amount > self.balance:
            raise ValidationError('Insufficient Funds')
        return amount



class BusinessTransportRegistrationForm(UserCreationForm):
    business_name = forms.CharField(max_length=255)
    corridor_start = forms.CharField(max_length=100, label="Corridor Start")
    corridor_end = forms.CharField(max_length=100, label="Corridor End")
    number_plate = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
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
            raise ValidationError('Business name already exists.')
        
        return business_name
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Business.objects.filter(name=username).exists():
            raise ValidationError('Username already exists.')
        return username