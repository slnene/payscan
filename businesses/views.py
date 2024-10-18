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


#####Business Suite###

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def register_business(request):
    if request.method == 'POST':
        form = BusinessRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            business_name = form.cleaned_data.get('business_name')
            payscan_user = PayscanUser.objects.create(user=user)
            business = Business.objects.create(owner=payscan_user, name=business_name)
            
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
            qr_code_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'img','qrcodes' f'business_{business.name}_PHONE-{business.owner.user.username}_ID-{business.id}.png')
            os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
            qr_img.save(qr_code_path)
            
            # Save QR code to the business model (assuming you have a field for it)
            with open(qr_code_path, "rb") as qr_file:
                business.qr_code.save(f"business_{business.name}_{business.owner.user.username}_{business.id}.png", File(qr_file))
            
            messages.success(request, 'Business Registration successful! Please log in.')
            return redirect('login_business')
    else:
        form = BusinessRegistrationForm()
    return render(request, 'businesses/register_business.html', {'form': form})

@login_required
def register_business_2(request):
    if request.method == 'POST':
        form = BusinessRegistrationForm_2(request.POST)
        if form.is_valid():
            business_name = form.cleaned_data.get('business_name')
            payscan_user = PayscanUser.objects.get(user=request.user)
            business = Business.objects.create(owner=payscan_user, name=business_name)

                        
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
            qr_code_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'img','qrcodes' f'business_{business.name}_PHONE-{business.owner.user.username}_ID-{business.id}.png')
            os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
            qr_img.save(qr_code_path)
            
            # Save QR code to the business model (assuming you have a field for it)
            with open(qr_code_path, "rb") as qr_file:
                business.qr_code.save(f"business_{business.name}_{business.owner.user.username}_{business.id}.png", File(qr_file))
            
            
            messages.success(request, 'Business registration successful! you were redirected to business dashboard.')
            return redirect('afterlogin_business')
    else:
        form = BusinessRegistrationForm_2()
    return render(request, 'businesses/register_business_2.html', {'form': form})

def login_business(request: HttpRequest):
    if request.method == 'POST':
        form = BusinessLoginForm(data=request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request=request, username=username, password=password)
            if user is not None:
                business = get_object_or_404(Business, owner__user=user)
                request.session['business_id'] = business.id
                login(request, user)
                return redirect('afterlogin_business')
            else:
                return render(request, 'businesses/login_business.html', {'form': form, 'error': 'Invalid Phone number or password'})
        else:
            return render(request, 'businesses/login_business.html', {'form': form, 'error': 'Please enter both username and password'})
    else:
        form = BusinessLoginForm()
    return render(request, 'businesses/login_business.html', {'form': form})


def logout_view_business(request):
    logout(request)
    return redirect('login_business')


@login_required
def business_dashboard(request):
    try:
        payscan_user = PayscanUser.objects.get(user=request.user)
        # Check if the user is a business owner
        if not Business.objects.filter(owner=payscan_user).exists():
            return redirect('registration_error')

        business = Business.objects.get(owner=payscan_user)
        transactions = Transaction.objects.filter(business=business).order_by('-timestamp')
        qr_code_url = business.qr_code.url if business.qr_code else None

        return render(request, 'businesses/business_dashboard.html', {
            'business': business,
            'transactions': transactions,
            'qr_code_url': qr_code_url,
        })
    except PayscanUser.DoesNotExist:
        return redirect('login_business')

    
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



@login_required
def generate_payment_qr(request):
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
            
            qr_code_url = os.path.join(settings.STATIC_URL, 'img', 'qrcodes_PAYMENTS', f'SZL:{formatted_amount}_PHONE-{business.owner.user.username}_{business.id}_{unique_id}.png')
            return render(request, 'businesses/payment_qr_code.html', {'business': business, 'qr_code_url': qr_code_url, 'amount': formatted_amount})
   
    return render(request, 'businesses/amount_due.html', {'business': business})


def register_business_transport(request):
    if request.method == 'POST':
        form = BusinessTransportRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            business_name = form.cleaned_data.get('business_name')
            number_plate = form.cleaned_data.get('number_plate')
            payscan_user = PayscanUser.objects.create(user=user)
            business = Business.objects.create(owner=payscan_user, name=business_name,number_plate=number_plate)
            corridor_start = form.cleaned_data['corridor_start']
            corridor_end = form.cleaned_data['corridor_end']
            business.corridor = f'{corridor_start} to {corridor_end}'  # Combine the two values
            business.save()  # Save the instance with the updated corridor

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
            qr_code_path = os.path.join(settings.BASE_DIR, 'payscan', 'static', 'img','qrcodes' f'business_{business.name}_PHONE-{business.owner.user.username}_ID-{business.id}.png')
            os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
            qr_img.save(qr_code_path)
            
            # Save QR code to the business model (assuming you have a field for it)
            with open(qr_code_path, "rb") as qr_file:
                business.qr_code.save(f"business_{business.name}_{business.owner.user.username}_{business.id}.png", File(qr_file))
            
            messages.success(request, 'Business Registration successful! Please log in.')
            return redirect('login_business')
    else:
        form = BusinessRegistrationForm()
    return render(request, 'businesses/register_business_transport.html', {'form': form})


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
