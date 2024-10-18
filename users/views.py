from decimal import Decimal, InvalidOperation
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect

from users.models import PayscanUser
from businesses.models import Business
from agents.models import Agent
from payscan.models import Transaction

from django.contrib.auth.decorators import login_required
from .forms import RegisterForm,DepositForm,WithdrawForm,PaymentForm,LoginForm

from django.http import HttpResponse
from django.http import JsonResponse
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

import os
from django.core.files import File
from django.conf import settings
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.colormasks import RadialGradiantColorMask
from qrcode.image.styles.colormasks import SquareGradiantColorMask
from qrcode.image.styles.colormasks import HorizontalGradiantColorMask
from qrcode.image.styles.colormasks import VerticalGradiantColorMask
from qrcode.image.styles.colormasks import ImageColorMask
from PIL import Image
import os
from django.core.files import File
from django.conf import settings
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image
from PIL import Image, ImageDraw, ImageFont
from PIL import Image, ImageDraw, ImageFont
import uuid
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
import random
import string
from payscan.twilio import*

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Generate and send OTP
            otp = generate_otp()
            phone_number = form.cleaned_data['username']  # Assuming username is phone number
            send_otp(phone_number, otp)
            request.session['otp'] = otp
            request.session['form_data'] = form.cleaned_data

            return redirect('verify_otp')  # Redirect to OTP verification page

    else:
        form = RegisterForm()

    return render(request, 'users/register.html', {'form': form})

def verify_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        if otp == request.session.get('otp'):
            # Complete registration
            form_data = request.session.get('form_data')
            user = User.objects.create_user(
                email=form_data['email'],
                username=form_data['username'],
                first_name=form_data['first_name'],
                last_name=form_data['last_name'],
                password=form_data['password1']
            )
            PayscanUser.objects.create(user=user)
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid OTP')

    return render(request, 'users/verify_otp.html')





    
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    try:
        payscan_user = PayscanUser.objects.get(user=request.user)
        transactions = Transaction.objects.filter(payer=payscan_user).order_by('-timestamp')
        return render(request, 'users/dashboard.html', {'balance': payscan_user.balance ,'transactions': transactions})
    except PayscanUser.DoesNotExist:
        return render(request, 'users/login.html')
    
    
    
@login_required
def transaction_history(request):
    payscan_user = PayscanUser.objects.get(user=request.user)
    transactions = Transaction.objects.filter(user=payscan_user).order_by('-timestamp')
    return render(request, 'payscan/dashboard.html', {'transactions': transactions})

@login_required
def deposit(request):
    payscan_user = PayscanUser.objects.filter(user=request.user).first()
    if payscan_user is None:
        return render(request, 'payscan/deposit.html', {'form': DepositForm(), 'error': 'User does not exist'})

    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payscan_user.balance += amount
            payscan_user.save()
            Transaction.objects.create(payer=payscan_user, amount=amount, transaction_type='deposit')
            return redirect('/afterlogin')
    else:
        form = DepositForm()
    return render(request, 'payscan/deposit.html', {'form': form})

@login_required
def withdraw(request):
    payscan_user = PayscanUser.objects.filter(user=request.user).first()
    if payscan_user is None:
        return render(request, 'payscan/deposit.html', {'form': DepositForm(), 'error': 'User does not exist'})

    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            payscan_user.balance -= amount
            payscan_user.save()
            Transaction.objects.create(payer=payscan_user, amount=amount, transaction_type='withdraw')
            return redirect('/afterlogin')
    else:
        form = WithdrawForm()
    return render(request, 'payscan/withdraw.html', {'form': form})


def choose_wallet(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    return render(request, 'users/choose_wallet.html', {'business': business})

@login_required
def confirm_payment(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    payscan_user = PayscanUser.objects.get(user=request.user)
    
    amount_str = request.GET.get('amount', '0.00')  # Default to '0.00' if amount is not provided

    # Ensure the amount_str is a valid decimal string
    try:
        amount = Decimal(amount_str)
    except InvalidOperation:
        # Log the error for debugging purposes
        print(f"Invalid amount format: {amount_str}")
        # Set a default value if conversion fails
        amount = Decimal('0.00')
        
    if request.method == 'POST':
        form = PaymentForm(request.POST, balance=payscan_user.balance)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if payscan_user.balance >= amount:
                if amount < Decimal('20.00'):
                    commission_amount = Decimal('0.10')
                elif Decimal('20.00') <= amount < Decimal('50.00'):
                    commission_amount = Decimal('0.20')
                elif Decimal('50.00') <= amount < Decimal('100.00'):
                    commission_amount = Decimal('0.30')
                elif Decimal('100.00') <= amount < Decimal('200.00'):
                    commission_amount = Decimal('0.50')
                elif Decimal('200.00') <= amount < Decimal('500.00'):
                    commission_amount = Decimal('0.70')
                elif Decimal('500.00') <= amount:
                    commission_amount = Decimal('02.00')



                agent = business.agent

                payscan_user.balance -= amount
                payscan_user.save()

                business.balance += (amount)
                business.save()

                if agent:
                    agent.balance += commission_amount
                    agent.save()
                    
                if business:
                    transaction = Transaction.objects.create(
                        payer=payscan_user,
                        business=business,  # Ensure this field is set
                        amount=amount,
                        transaction_type='payment',
                        agent=agent,
                        commission=commission_amount
                    )
                    return redirect('payment_success', transaction_id=transaction.id)
                else:
                    # Handle the case where the business object is None
                    messages.error(request, "Business not found.")
                    return redirect('payment_error')

                
    else:
        form = PaymentForm(balance=payscan_user.balance)
    return render(request, 'users/confirm_payment.html', {'form': form, 'business': business,  'amount': amount})



def choose_wallet_dynamic(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    amount_str = request.GET.get('amount', '0.00')  # Default to '0.00' if amount is not provided

    # Ensure the amount_str is a valid decimal string
    try:
        amount = Decimal(amount_str)
    except InvalidOperation:
        # Log the error for debugging purposes
        print(f"Invalid amount format: {amount_str}")
        # Set a default value if conversion fails
        amount = Decimal('0.00')

    return render(request, 'users/choose_wallet_dynamic.html', {'business': business, 'amount': amount})


def choose_deposit(request):
    payscan_user = PayscanUser.objects.get(user=request.user)
    return render(request, 'users/choose_deposit.html')

def choose_withdraw(request):
    payscan_user = PayscanUser.objects.get(user=request.user)
    return render(request, 'users/choose_withdraw.html')



def payment_momo(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    return render(request, 'users/payment_momo.html', {'business': business})



@login_required
def payment(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    payscan_user = PayscanUser.objects.get(user=request.user)
    if request.method == 'POST':
        form = PaymentForm(request.POST, balance=payscan_user.balance)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if payscan_user.balance >= amount:
                if amount < Decimal('20.00'):
                    commission_amount = Decimal('0.10')
                elif Decimal('20.00') <= amount < Decimal('50.00'):
                    commission_amount = Decimal('0.20')
                elif Decimal('50.00') <= amount < Decimal('100.00'):
                    commission_amount = Decimal('0.30')
                elif Decimal('100.00') <= amount < Decimal('200.00'):
                    commission_amount = Decimal('0.50')
                elif Decimal('200.00') <= amount < Decimal('500.00'):
                    commission_amount = Decimal('0.70')
                elif Decimal('500.00') <= amount:
                    commission_amount = Decimal('02.00')



                agent = business.agent

                payscan_user.balance -= amount
                payscan_user.save()

                business.balance += (amount)
                business.save()

                if agent:
                    agent.balance += commission_amount
                    agent.save()
                    
                if business:
                    transaction = Transaction.objects.create(
                        payer=payscan_user,
                        business=business,  # Ensure this field is set
                        amount=amount,
                        transaction_type='payment',
                        agent=agent,
                        commission=commission_amount
                    )
                    return redirect('payment_success', transaction_id=transaction.id)
                else:
                    # Handle the case where the business object is None
                    messages.error(request, "Business not found.")
                    return redirect('payment_error')

                
    else:
        form = PaymentForm(balance=payscan_user.balance)
    return render(request, 'users/payment.html', {'form': form, 'business': business})


@login_required
def payment_success(request, transaction_id):
    transaction = Transaction.objects.get(id=transaction_id)
    return render(request, 'payscan/payment_success.html', {'transaction': transaction})




import requests
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from myapp.models import Transaction, PayscanUser, Business
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from myapp.forms import PaymentForm

class Collections:
    def __init__(self, subscription_key, user_id, api_key, environment):
        self.subscription_key = subscription_key
        self.user_id = user_id
        self.api_key = api_key
        self.environment = environment
        self.base_url = 'https://sandbox.momodeveloper.mtn.com/collection' if environment == 'sandbox' else 'https://momodeveloper.mtn.com/collection'

    def get_access_token(self):
        url = f"{self.base_url}/token/"
        headers = {
            'Authorization': f'Basic {self.api_key}',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        response = requests.post(url, headers=headers)
        return response.json().get('access_token')

    def request_to_pay(self, amount, currency, external_id, payer, payer_message, payee_note):
        url = f"{self.base_url}/v1_0/requesttopay"
        headers = {
            'Authorization': f'Bearer {self.get_access_token()}',
            'X-Reference-Id': external_id,
            'X-Target-Environment': self.environment,
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        data = {
            'amount': str(amount),
            'currency': currency,
            'externalId': external_id,
            'payer': payer,
            'payerMessage': payer_message,
            'payeeNote': payee_note,
        }
        response = requests.post(url, headers=headers, json=data)
        return response

@login_required
def make_payment(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    payscan_user = PayscanUser.objects.get(user=request.user)

    if request.method == 'POST':
        form = PaymentForm(request.POST, balance=payscan_user.balance)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if payscan_user.balance >= amount:
                collections = Collections(
                    settings.MOMOAPI['collections']['sandbox']['subscription_key'],
                    settings.MOMOAPI['collections']['sandbox']['user_id'],
                    settings.MOMOAPI['collections']['sandbox']['api_key'],
                    settings.MOMOAPI['collections']['sandbox']['environment']
                )

                external_id = "some_unique_external_id"  # Generate a unique external ID for the transaction
                payer_message = 'Payment for services'
                payee_note = 'Payment for services'

                response = collections.request_to_pay(
                    amount=amount,
                    currency='EUR',
                    external_id=external_id,
                    payer={'party_id_type': 'MSISDN', 'party_id': payscan_user.user.username},
                    payer_message=payer_message,
                    payee_note=payee_note
                )

                if response.status_code == 202:  # Payment request successfully initiated
                    transaction = Transaction.objects.create(
                        payer=payscan_user,
                        business=business,
                        amount=amount,
                        transaction_type='payment',
                        external_id=external_id
                    )
                    payscan_user.balance -= amount
                    payscan_user.save()
                    business.balance += amount
                    business.save()
                    messages.success(request, 'Payment successful')
                    return redirect('payment_success', transaction_id=transaction.id)
                else:
                    messages.error(request, 'Payment failed')
                    return redirect('payment_error')

    else:
        form = PaymentForm(balance=payscan_user.balance)

    return render(request, 'users/payment.html', {'form': form, 'business': business})













from django.contrib import messages
from .utils import initiate_momo_payment, transfer_to_business

@login_required
def payment_momo(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    payscan_user = PayscanUser.objects.get(user=request.user)
    unique_id = uuid.uuid4()
    if request.method == 'POST':
        form = PaymentForm(request.POST, balance=payscan_user.balance)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if payscan_user.balance >= amount:
                if amount < Decimal('20.00'):
                    commission_amount = Decimal('0.10')
                elif Decimal('20.00') <= amount < Decimal('50.00'):
                    commission_amount = Decimal('0.20')
                elif Decimal('50.00') <= amount < Decimal('100.00'):
                    commission_amount = Decimal('0.30')
                elif Decimal('100.00') <= amount < Decimal('200.00'):
                    commission_amount = Decimal('0.50')
                elif Decimal('200.00') <= amount < Decimal('500.00'):
                    commission_amount = Decimal('0.70')
                elif Decimal('500.00') <= amount:
                    commission_amount = Decimal('2.00')

                agent = business.agent

                # Initiate payment via MTN MoMo
                external_id = f"txn_{business_id}_{payscan_user.user.username}"
                momo_response = initiate_momo_payment(amount, payscan_user.user.username, external_id)
                if momo_response.get('status') == 'success':
                    payscan_user.balance -= amount
                    payscan_user.save()

                    business.balance += amount
                    business.save()

                    if agent:
                        agent.balance += commission_amount
                        agent.save()

                    # Transfer money to the business
                    transfer_response = transfer_to_business(amount, business)
                    if transfer_response.get('status') == 'success':
                        transaction = Transaction.objects.create(
                            payer=payscan_user,
                            business=business,
                            amount=amount,
                            transaction_type='payment',
                            agent=agent,
                            commission=commission_amount
                        )
                        return redirect('payment_success', transaction_id=transaction.id)
                    else:
                        messages.error(request, "Failed to transfer money to the business.")
                        return redirect('payment_error9')
                else:
                    messages.error(request, "Failed to initiate payment via MTN MoMo.")
                    return redirect('payment_error')
    else:
        form = PaymentForm(balance=payscan_user.balance)
    return render(request, 'users/payment_momo.html', {'form': form, 'business': business})


def payment_error(request):
    
    return render(request, 'users/payment_error.html' )





class Collections:
    def __init__(self, subscription_key, user_id, api_key, environment):
        self.subscription_key = subscription_key
        self.user_id = user_id
        self.api_key = api_key
        self.environment = environment
        self.base_url = 'https://sandbox.momodeveloper.mtn.com/collection' if environment == 'sandbox' else 'https://momodeveloper.mtn.com/collection'

    def get_access_token(self):
        url = f"{self.base_url}/token/"
        headers = {
            'Authorization': f'Basic {self.api_key}',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        response = requests.post(url, headers=headers)
        return response.json().get('access_token')

    def request_to_pay(self, amount, currency, external_id, payer, payer_message, payee_note):
        url = f"{self.base_url}/v1_0/requesttopay"
        headers = {
            'Authorization': f'Bearer {self.get_access_token()}',
            'X-Reference-Id': external_id,
            'X-Target-Environment': self.environment,
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        data = {
            'amount': str(amount),
            'currency': currency,
            'externalId': external_id,
            'payer': payer,
            'payerMessage': payer_message,
            'payeeNote': payee_note,
        }
        response = requests.post(url, headers=headers, json=data)
        return response

@login_required
def make_payment(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    payscan_user = PayscanUser.objects.get(user=request.user)

    if request.method == 'POST':
        form = PaymentForm(request.POST, balance=payscan_user.balance)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if payscan_user.balance >= amount:
                collections = Collections(
                    settings.MOMOAPI['collections']['sandbox']['subscription_key'],
                    settings.MOMOAPI['collections']['sandbox']['user_id'],
                    settings.MOMOAPI['collections']['sandbox']['api_key'],
                    settings.MOMOAPI['collections']['sandbox']['environment']
                )

                external_id = "some_unique_external_id"  # Generate a unique external ID for the transaction
                payer_message = 'Payment for services'
                payee_note = 'Payment for services'

                response = collections.request_to_pay(
                    amount=amount,
                    currency='EUR',
                    external_id=external_id,
                    payer={'party_id_type': 'MSISDN', 'party_id': payscan_user.user.username},
                    payer_message=payer_message,
                    payee_note=payee_note
                )

                if response.status_code == 202:  # Payment request successfully initiated
                    transaction = Transaction.objects.create(
                        payer=payscan_user,
                        business=business,
                        amount=amount,
                        transaction_type='payment',
                        external_id=external_id
                    )
                    payscan_user.balance -= amount
                    payscan_user.save()
                    business.balance += amount
                    business.save()
                    messages.success(request, 'Payment successful')
                    return redirect('payment_success', transaction_id=transaction.id)
                else:
                    messages.error(request, 'Payment failed')
                    return redirect('payment_error')

    else:
        form = PaymentForm(balance=payscan_user.balance)

    return render(request, 'users/payment.html', {'form': form, 'business': business})
