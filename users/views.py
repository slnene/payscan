from decimal import Decimal, InvalidOperation
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect

from users.models import PayscanUser
from businesses.models import Business
from agents.models import Agent
from payscan.models import Transaction

from django.contrib.auth.decorators import login_required
from .forms import RegisterForm,PaymentForm,LoginForm

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
import random
import string
from payscan.utils import send_pin,generate_pin
from payscan.momo_api import*
from django.contrib import messages
from uni.client import UniClient
from uni.exception import UniException

client = UniClient("NHxLRh7E7psscG1GtFaN2j", "23F32EQ6EK6TgLSvMvtzuje3krA4D9a")

print(get_random_secret_key())



##################################### USERS / REGISTRAION AND DASHBOARD ###############################

from firebase_admin import auth, firestore

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = username
            if not phone_number.startswith('+'):
                phone_number = f'+268{phone_number}'
            pin = generate_pin()
            send_pin(phone_number, pin)
            password = pin  # Default pin as password

            # Create user in Firebase Auth
            firebase_user = auth.create_user(
                email=email,
                email_verified=False,
                phone_number=phone_number,
                password=password,
                display_name=f'{first_name} {last_name}',
                disabled=False
            )

            # Save user data to Firebase Firestore
            db = firestore.client()
            user_ref = db.collection('users').document(firebase_user.uid)
            user_ref.set({
                'email': email,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone_number,
                'default_pin': pin,
                'priority': 1,
                'balance': 0
            })
            django_user = User.objects.create_user(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            PayscanUser.objects.create(user=django_user, default_pin=pin, priority=1)

            request.session['pin'] = pin
            request.session['form_data'] = form.cleaned_data
            print(f'PIN: {pin}')
            messages.success(request, 'Registration successful! Login with default PIN and reset your PIN on first login.')
            return redirect('login')
        else:
            print("Form errors:", form.errors)
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def reset_pin(request):
    if request.method == 'POST':
        pin = request.POST.get('new_pin')
        user = request.user
        user.set_password(pin)  # Reset the user's PIN in Django
        user.save()

        messages.success(request, 'PIN reset successful!')
        return redirect('login')
    return render(request, 'payscan/reset_pin.html')





def register1(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username =form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            password = form.cleaned_data['password1']
                            
            user=User.objects.create_user(email=email, username=username, first_name=first_name, last_name=last_name, password=password)          
            PayscanUser.objects.create(user=user)
            return redirect('login')     
    else:
            # Handle the case where the passwords do not match
        form = RegisterForm()            
    return render(request, 'users/register.html', {'form': form})


@login_required
def dashboard(request):
    try:
        payscan_user = PayscanUser.objects.select_related('user').get(user=request.user)
        transactions = Transaction.objects.filter(payer=payscan_user).select_related('business').order_by('-timestamp')
        momo_balance = get_balance()  # Get the MoMo balance
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(request, 'users/dashboard.html', {'transactions': transactions, 'balance': momo_balance})
        return render(request, 'users/dashboard.html', {'balance': momo_balance, 'transactions': transactions})
    except PayscanUser.DoesNotExist:
        return render(request, 'users/login.html')

@login_required
def get_transactions(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        payscan_user = PayscanUser.objects.get(user=request.user)
        transactions = Transaction.objects.filter(payer=payscan_user).order_by('-timestamp')
        data = {
            'transactions': list(transactions.values())
        }
        return JsonResponse(data)

    
    

########################################### USERS / MAKING PAYMENTS ######################################################



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
def confirm_payment(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    payscan_user = PayscanUser.objects.get(user=request.user)
    
    amount_str = request.GET.get('amount', '0.00')  # Default to '0.00' if amount is not provided

    # Ensure the amount_str is a valid decimal string
    try:
        amount = Decimal(amount_str)
    except InvalidOperation:
        print(f"Invalid amount format: {amount_str}")
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
                    commission_amount = Decimal('2.00')

                # Initialize Collections
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

                transaction = Transaction.objects.create(
                    payer=payscan_user,
                    business=business,
                    amount=amount,
                    transaction_type='payment',
                    agent=business.agent,
                    commission=commission_amount,
                    external_id=external_id
                )

                if response.status_code == 202:  # Payment request successfully initiated
                    transaction.status = 'success'
                    transaction.save()
                    payscan_user.balance -= amount
                    payscan_user.save()
                    business.balance += amount
                    business.save()

                    if business.agent:
                        business.agent.balance += commission_amount
                        business.agent.save()
                    
                    messages.success(request, 'Payment successful')
                    return redirect('payment_success', transaction_id=transaction.id)
                else:
                    transaction.status = 'failed'
                    transaction.save()
                    messages.error(request, 'Payment failed')
                    return redirect('payment_error')

    else:
        form = PaymentForm(balance=payscan_user.balance)
    return render(request, 'users/confirm_payment.html', {'form': form, 'business': business, 'amount': amount})


def payment_error(request):
    
    return render(request, 'users/payment_error.html' )


@login_required
def payment_success(request, transaction_id):
    transaction = Transaction.objects.get(id=transaction_id)
    return render(request, 'users/payment_success.html', {'transaction': transaction})

@login_required
def payment_momo(request, business_id):
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

                transaction = Transaction.objects.create(
                    payer=payscan_user,
                    business=business,
                    amount=amount,
                    transaction_type='payment',
                    external_id=external_id
                )

                if response.status_code == 202:  # Payment request successfully initiated
                    transaction.status = 'success'
                    transaction.save()
                    messages.success(request, 'Payment successful')
                    return redirect('payment_success', transaction_id=transaction.id)
                else:
                    transaction.status = 'failed'
                    transaction.save()
                    messages.error(request, 'Payment failed')
                    return redirect('payment_error')  # Redirect to error page

    else:
        form = PaymentForm(balance=payscan_user.balance)

    return render(request, 'users/payment.html', {'form': form, 'business': business})

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





######################################  USERS / DEPOSITS AND WITHDRAWALS ##############################################
                        

