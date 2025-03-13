from decimal import Decimal
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from users.models import PayscanUser
from businesses.models import Business
from agents.models import Agent
from payscan.models import Transaction

from django.contrib.auth.decorators import login_required
from .forms import BusinessRegistrationForm_2, BusinessRegistrationForm,BusinessLoginForm,BusinessPaymentForm,BusinessWithdrawForm,BusinessTransportRegistrationForm
from django.http import HttpRequest, HttpResponse
from django.http import JsonResponse
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files import File
from django.conf import settings
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
from payscan.momo_api import*
from django.contrib import messages
from payscan.utils import send_pin,generate_pin
from uni.client import UniClient
from uni.exception import UniException
from django.http import JsonResponse
from django.core import serializers

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core import serializers
import logging
from datetime import datetime
from payscan.utils import hex_to_rgb

##################################### BUSINESS / REGISTRAION AND DASHBOARD ###############################

@login_required
def business_dashboard(request):
    try:
        payscan_user = PayscanUser.objects.get(user=request.user)
        if not Business.objects.filter(owner=payscan_user).exists():
            return redirect('registration_error')
        business = Business.objects.select_related('owner').get(owner=payscan_user)
        transactions = Transaction.objects.filter(business=business).select_related('payer', 'business').order_by('-timestamp')
        qr_code_url = business.qr_code.url if business.qr_code else None
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(request, 'businesses/transactions.html', {'transactions': transactions})
        return render(request, 'businesses/business_dashboard.html', {
            'business': business,
            'transactions': transactions,
            'qr_code_url': qr_code_url,
        })
    except PayscanUser.DoesNotExist:
        return redirect('login_business')

logger = logging.getLogger(__name__)

@login_required
def get_transactions(request):
    try:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            payscan_user = PayscanUser.objects.get(user=request.user)
            business = Business.objects.get(owner=payscan_user)
            transactions = Transaction.objects.filter(business=business).order_by('-timestamp')
            
            data = [
                {
                    'id': transaction.id,
                    'payer': transaction.payer.user.first_name,
                    'amount': transaction.amount,
                    'transaction_type': transaction.transaction_type,
                    'timestamp': transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
                for transaction in transactions
            ]
            return JsonResponse({'transactions': data})
        else:
            logger.error("Request is not AJAX")
            return JsonResponse({'error': 'Invalid request'}, status=400)
    except PayscanUser.DoesNotExist:
        logger.error("PayscanUser does not exist for the current user")
        return JsonResponse({'error': 'User not found'}, status=404)
    except Business.DoesNotExist:
        logger.error("Business does not exist for the current PayscanUser")
        return JsonResponse({'error': 'Business not found'}, status=404)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return JsonResponse({'error': 'An error occurred'}, status=500)


@login_required
def filter_transactions(request):
    date_str = request.GET.get('date')
    date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.today().date()
    
    transactions = Transaction.objects.filter(timestamp__date=date)
    transactions_data = [
        {
            'id': transaction.id,
            'payer': transaction.payer.user.first_name,
            'amount': transaction.amount,
            'transaction_type': transaction.transaction_type,
            'timestamp': transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        for transaction in transactions
    ]
    
    return JsonResponse({'transactions': transactions_data})



def register_business(request):
    if request.method == 'POST':
        form = BusinessRegistrationForm(request.POST)
        if form.is_valid():
            business_name = form.cleaned_data['business_name']
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

            user = User.objects.create_user(
                email=email, 
                username=username, 
                first_name=first_name, 
                last_name=last_name, 
                password=password
            ) 
            
            payscan_user=PayscanUser.objects.create(user=user, default=pin)  # Save default PIN
            business = Business.objects.create(owner=payscan_user, name=business_name,priority=1)

            request.session['pin'] = pin
            request.session['business_id'] = business.id
            print(f'PIN: {pin}')

            # Generate QR code
            qr_code_url = f"{settings.SITE_URL}/choose_wallet/{business.id}/"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_code_url)
            qr.make(fit=True)

            background_color = hex_to_rgb("#e9d8d8")
            foreground_color = hex_to_rgb("#4d1616")
            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                color_mask=SolidFillColorMask(back_color=background_color, front_color=foreground_color)
            )

            logo_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'img', 'payscan-navlogo.png')
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                basewidth = 250
                wpercent = (basewidth / float(logo.size[0]))
                hsize = int((float(logo.size[1]) * float(wpercent)))
                logo = logo.resize((basewidth, hsize), Image.LANCZOS)
                pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
                qr_img.paste(logo, pos, mask=logo)

            font_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'fonts', 'arial.ttf')
            font = ImageFont.truetype(font_path, 20)
            draw = ImageDraw.Draw(qr_img)
            text_position = (10, 10)
            draw.text(text_position, business.name, font=font, fill=(0, 0, 0))

            qr_code_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'img', 'qrcodes', f'business_{business.name}_PHONE-{business.owner.user.username}_ID-{business.id}.png')
            os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
            qr_img.save(qr_code_path)

            with open(qr_code_path, "rb") as qr_file:
                business.qr_code.save(f"business_{business.name}_{business.owner.user.username}_{business.id}.png", File(qr_file))

            messages.success(request, 'Business Registration successful! Please log in and set your PIN.')
            return redirect('login')
        else:
            print("Form errors:", form.errors)
    else:
        form = BusinessRegistrationForm()
    return render(request, 'businesses/register_business.html', {'form': form})

@login_required
def reset_pin(request):
    if request.method == 'POST':
        pin = request.POST.get('new_pin')
        user = request.user
        user.set_password(pin)  # Reset the user's PIN
        user.save()
        messages.success(request, 'PIN reset successful!')
        return redirect('login')
    return render(request, 'payscan/reset_pin.html')



@login_required
def register_business_2(request):
    if request.method == 'POST':
        form = BusinessRegistrationForm_2(request.POST, user=request.user)
        if form.is_valid():
            business_name = form.cleaned_data.get('business_name')
            payscan_user = PayscanUser.objects.get(user=request.user)
            business = Business.objects.create(owner=payscan_user, name=business_name)
            request.session['form_data'] = form.cleaned_data
            request.session['business_id'] = business.id
            
            # Generate QR code
            qr_code_url = f"{settings.SITE_URL}/choose_wallet/{business.id}/"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_code_url)
            qr.make(fit=True)
            
            background_color = hex_to_rgb("#e9d8d8")
            foreground_color = hex_to_rgb("#4d1616")
            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                color_mask=SolidFillColorMask(back_color=background_color, front_color=foreground_color)
            )
            
            logo_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'img', 'payscan-navlogo.png')
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                basewidth = 250
                wpercent = (basewidth / float(logo.size[0]))
                hsize = int((float(logo.size[1]) * float(wpercent)))
                logo = logo.resize((basewidth, hsize), Image.LANCZOS)
                pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
                qr_img.paste(logo, pos, mask=logo)
            
            font_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'fonts', 'arial.ttf')
            font = ImageFont.truetype(font_path, 20)
            draw = ImageDraw.Draw(qr_img)
            text_position = (10, 10)
            draw.text(text_position, business.name, font=font, fill=(0, 0, 0))
            
            qr_code_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'img', 'qrcodes', f'business_{business.name}_PHONE-{business.owner.user.username}_ID-{business.id}.png')
            os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
            qr_img.save(qr_code_path)
            
            with open(qr_code_path, "rb") as qr_file:
                business.qr_code.save(f"business_{business.name}_{business.owner.user.username}_{business.id}.png", File(qr_file))
            
            return redirect('afterlogin_business')
    else:
        form = BusinessRegistrationForm_2(user=request.user)
    return render(request, 'businesses/register_business_2.html', {'form': form})

@login_required
def check_business_ownership(request):
    if request.method == 'POST':
        payscan_user = PayscanUser.objects.get(user=request.user)
        if Business.objects.filter(owner=payscan_user).exists():
            return JsonResponse({'exists': True})
        else:
            return JsonResponse({'exists': False})
    return JsonResponse({'error': 'Invalid request'}, status=400)


def register_business_transport(request):
    if request.method == 'POST':
        form = BusinessTransportRegistrationForm(request.POST)
        if form.is_valid():
            business_name = form.cleaned_data.get('business_name')
            number_plate = form.cleaned_data.get('number_plate')
            corridor_start = form.cleaned_data['corridor_start']
            corridor_end = form.cleaned_data['corridor_end']
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

            user = User.objects.create_user(
                email=email, 
                username=username, 
                first_name=first_name, 
                last_name=last_name, 
                password=password
            )

            payscan_user = PayscanUser.objects.create(user=user, default_pin=pin)  # Save default PIN

            business = Business.objects.create(
                owner=payscan_user, 
                name=business_name,
                priority=1,
                number_plate=number_plate,
                corridor=f'{corridor_start} to {corridor_end}',  # Combine the two values
                default_pin=pin  # Set default PIN
            )

            request.session['pin'] = pin
            request.session['business_id'] = business.id
            print(f'PIN: {pin}')

            # Generate QR code
            qr_code_url = f"{settings.SITE_URL}/choose_wallet/{business.id}/"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_code_url)
            qr.make(fit=True)

            # Convert hex color to RGB
            background_color = hex_to_rgb("#e9d8d8")
            foreground_color = hex_to_rgb("#4d1616")

            # Customize the QR code
            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                color_mask=SolidFillColorMask(back_color=background_color, front_color=foreground_color)
            )

            # Add logo to the QR code
            logo_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'img', 'payscan-navlogo.png')
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                basewidth = 250
                wpercent = (basewidth / float(logo.size[0]))
                hsize = int((float(logo.size[1]) * float(wpercent)))
                logo = logo.resize((basewidth, hsize), Image.LANCZOS)
                pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
                qr_img.paste(logo, pos, mask=logo)

            # Add business name at the top left corner of the QR code image
            font_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'fonts', 'arial.ttf')  # Ensure you have the font file
            font = ImageFont.truetype(font_path, 20)
            draw = ImageDraw.Draw(qr_img)
            text_position = (10, 10)  # Top left corner with some padding
            draw.text(text_position, business.name, font=font, fill=(0, 0, 0))

            # Save the QR code
            qr_code_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'img', 'qrcodes', f'business_{business.name}_PHONE-{business.owner.user.username}_ID-{business.id}.png')
            os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
            qr_img.save(qr_code_path)

            # Save QR code to the business model
            with open(qr_code_path, "rb") as qr_file:
                business.qr_code.save(f"business_{business.name}_{business.owner.user.username}_{business.id}.png", File(qr_file))

            messages.success(request, 'Business Registration successful! Please log in.')
            return redirect('login')
    else:
        form = BusinessTransportRegistrationForm()
    
    return render(request, 'businesses/register_business_transport.html', {'form': form})



########################################### BUSINESS / MAKING PAYMENTS ######################################################

@login_required
def business_payment(request, business_id):
    business = Business.objects.get(owner__user=request.user)
    payee = get_object_or_404(Business, id=business_id)
    
    if request.method == 'POST':
        form = BusinessPaymentForm(request.POST, balance=business.balance)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if business.balance >= amount:
                commission_amount = 1
                agent = business.agent
                
                business.balance -= amount
                business.save()
                
                payee.balance += (amount - commission_amount)
                payee.save()
                
                if agent:
                    agent.user.balance += commission_amount
                    agent.user.save()
                
                transaction=Transaction.objects.create(payer=business.owner, 
                                                       payee=payee, 
                                                       amount=amount, 
                                                       transaction_type='payment',
                                                       agent=agent,
                                                       )
                return redirect('payment_success', transaction_id=transaction.id)
    else:
        form = BusinessPaymentForm(balance=business.balance)
    return render(request, 'businesses/business_payment.html', {'form': form, 'payee': payee})

@login_required
def generate_payment_qr(request):
    business_id = request.session.get('business_id')
    if not business_id:
        messages.error(request, 'No business logged in.')
        return redirect('login')
    
    try:
        business = get_object_or_404(Business, id=business_id, owner__user=request.user)
    except Business.DoesNotExist:
        messages.error(request, 'Business not found.')
        return redirect('login')

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        if amount > 0:
            formatted_amount = f"{amount:.2f}"
            qr_code_url = f"{settings.SITE_URL}/choose_wallet_dynamic/{business.id}/?amount={formatted_amount}"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_code_url)
            qr.make(fit=True)
            background_color = hex_to_rgb("#e9d8d8")
            foreground_color = hex_to_rgb("#4d1616")
            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                color_mask=SolidFillColorMask(back_color=background_color, front_color=foreground_color)
            )
            logo_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'img', 'payscan-navlogo.png')
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                basewidth = 250
                wpercent = (basewidth / float(logo.size[0]))
                hsize = int((float(logo.size[1]) * float(wpercent)))
                logo = logo.resize((basewidth, hsize), Image.LANCZOS)
                pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
                qr_img.paste(logo, pos, mask=logo)
            
            draw = ImageDraw.Draw(qr_img)
            font_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'fonts', 'arial.ttf')
            font = ImageFont.truetype(font_path, 20)
            amount_text = f"SZL {formatted_amount}"
            bbox = draw.textbbox((0, 0), amount_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_position = (qr_img.size[0] - text_width - 10, 10)
            draw.text(text_position, amount_text, font=font, fill=(0, 0, 0))
            text_position = (10, 10)
            draw.text(text_position, business.name, font=font, fill=(0, 0, 0))
            unique_id = uuid.uuid4()
            qr_code_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'qrcodes_PAYMENTS', f'SZL:{formatted_amount}_PHONE-{business.owner.user.username}_ID-{business.id}_{unique_id}.png')
            os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
            qr_img.save(qr_code_path)
            with open(qr_code_path, "rb") as qr_file:
                business.Dynamic_qr_code.save(f'SZL:{formatted_amount}_{business.owner.user.username}_{business.id}_{unique_id}.png', File(qr_file))
            qr_code_url = os.path.join(settings.STATIC_URL, 'img', 'qrcodes_PAYMENTS', f'SZL:{formatted_amount}_PHONE-{business.owner.user.username}_{business.id}_{unique_id}.png')
            return render(request, 'businesses/payment_qr_code.html', {'business': business, 'qr_code_url': qr_code_url, 'amount': formatted_amount})
    
    return render(request, 'businesses/amount_due.html', {'business': business})

@login_required
def generate_payment_qr_transport(request):
    business_id = request.session.get('business_id')
    if not business_id:
        messages.error(request, 'No business logged in.')
        return redirect('login_business')

    business = get_object_or_404(Business, id=business_id, owner__user=request.user)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        if amount > 0:
            # Format the amount to always have two decimal places
            formatted_amount = f"{amount:.2f}"

            # Generate QR code
            qr_code_url = f"{settings.SITE_URL}/choose_wallet_dynamic/{business.id}/?amount={formatted_amount}"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_code_url)
            qr.make(fit=True)

            # Convert hex color to RGB
            background_color = hex_to_rgb("#e9d8d8")
            foreground_color = hex_to_rgb("#4d1616")

            # Customize the QR code
            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                color_mask=SolidFillColorMask(back_color=background_color, front_color=foreground_color)
            )

            # Add logo to the QR code
            logo_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'img', 'payscan-navlogo.png')
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                basewidth = 250
                wpercent = (basewidth / float(logo.size[0]))
                hsize = int((float(logo.size[1]) * float(wpercent)))
                logo = logo.resize((basewidth, hsize), Image.LANCZOS)
                pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
                qr_img.paste(logo, pos, mask=logo)

            # Initialize the drawing context with the image object as background
            draw = ImageDraw.Draw(qr_img)

            # Define the font and size (ensure the path to the font file is correct)
            font_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'fonts', 'arial.ttf')
            font = ImageFont.truetype(font_path, 20)

            # Add amount at the top right corner of the QR code image
            amount_text = f"SZL {formatted_amount}"
            bbox = draw.textbbox((0, 0), amount_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_position = (qr_img.size[0] - text_width - 10, 10)  # Top right corner with some padding
            draw.text(text_position, amount_text, font=font, fill=(0, 0, 0))

            # Add business name at the top left corner of the QR code image
            text_position = (10, 10)  # Top left corner with some padding
            draw.text(text_position, business.name, font=font, fill=(0, 0, 0))

            # Save the QR code with a unique name
            unique_id = uuid.uuid4()
            qr_code_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'qrcodes_PAYMENTS', f'SZL:{formatted_amount}_PHONE-{business.owner.user.username}_ID-{business.id}_{unique_id}.png')
            os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
            qr_img.save(qr_code_path)
            
            # Save QR code to the business model (assuming you have a field for it)
            with open(qr_code_path, "rb") as qr_file:
                business.Dynamic_qr_code.save(f'SZL:{formatted_amount}_{business.owner.user.username}_{business.id}_{unique_id}.png', File(qr_file))
            
            messages.success(request, 'QR Code generated successfully!')
            qr_code_url = os.path.join(settings.STATIC_URL, 'img', 'qrcodes_PAYMENTS', f'SZL:{formatted_amount}_PHONE-{business.owner.user.username}_{business.id}_{unique_id}.png')
            return render(request, 'businesses/payment_qr_code.html', {'business': business, 'qr_code_url': qr_code_url, 'amount': formatted_amount})
   
    return render(request, 'businesses/amount_due_transport.html', {'business': business})


######################################  BUSINESS / DEPOSITS AND WITHDRAWALS ##############################################


@login_required
def business_withdraw(request):
    business = Business.objects.get(owner__user=request.user)
    if request.method == 'POST':
        form = BusinessWithdrawForm(request.POST, balance=business.balance)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if business.balance >= amount:
                business.balance -= amount
                business.save()
                Transaction.objects.create(payer=business.owner, amount=amount, transaction_type='withdraw')
                return redirect('afterlogin_business')
    else:
        form = BusinessWithdrawForm(balance=business.balance)
    return render(request, 'businesses/business_withdraw.html', {'form': form})


