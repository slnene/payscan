from decimal import Decimal
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect

from users.models import PayscanUser
from businesses.models import Business
from agents.models import Agent
from payscan.models import Transaction

from django.contrib.auth.decorators import login_required
from .forms import AgentRegisterForm,AgentLoginForm,AgentBusinessRegistrationForm,AgentRegisterForm2

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
import random
import string
from twilio.rest import Client

from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from payscan.utils import send_pin,generate_pin
from django.contrib.auth import update_session_auth_hash
import os




##################################### AGENTS / REGISTRAION AND DASHBOARD ###############################

def register_agent(request):
    if request.method == 'POST':
        form = AgentRegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            Id_number = form.cleaned_data.get('Id_number')          
            priority= 1
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
            payscan_user=PayscanUser.objects.create(user=user, default_pin=pin)  # Save default PIN
            agent = Agent.objects.create(agentuser=payscan_user,Id_number=Id_number, priority=1)
            
            request.session['pin'] = pin
            request.session['form_data'] = form.cleaned_data
            print(f'PIN: {pin}')
            messages.success(request, 'Registration successful! Login with default PIN and reset your PIN on first login.')
            return redirect('login')
        else:
            print("Form errors:", form.errors)
    else:
        form = AgentRegisterForm()
    return render(request, 'agents/register_agent.html', {'form': form})

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


def register_agent_2(request):
    if request.method == 'POST':
        form = AgentRegisterForm2(request.POST)
        if form.is_valid():
            Id_number = form.cleaned_data.get('Id_number')          
            payscan_user = PayscanUser.objects.get(user=request.user)
            Agent.objects.create(agentuser=payscan_user,Id_number=Id_number)
            return redirect('agent_dashboard')
    else:
        form = AgentRegisterForm2()
        return render(request, 'agents/register_agent_2.html', {'form': form, 'user': request.user})


@login_required
def agent_dashboard(request):
    try:
        payscan_user = get_object_or_404(PayscanUser, user=request.user)
        if not hasattr(payscan_user, 'agent'):
            return redirect('registration_error')

        agent = get_object_or_404(Agent, agentuser=payscan_user)
        transactions = Transaction.objects.filter(agent=agent).order_by('-timestamp')
        businesses = Business.objects.filter(agent=agent)
        total_earned_commission = sum(transaction.commission for transaction in transactions)
        business_id = request.GET.get('business_id')
        filtered_transactions = Transaction.objects.filter(agent=agent, business_id=business_id)
        transaction_count = filtered_transactions.count()

        return render(request, 'agents/agent_dashboard.html', {
            'agent': agent,
            'transactions': transactions,
            'total_earned_commission': total_earned_commission,
            'businesses': businesses,
            'transaction_count': transaction_count
        })
    except PayscanUser.DoesNotExist:
        return redirect('login_agent')

def get_businesses(request):
    if request.method == 'GET':
        businesses = Business.objects.all().select_related('owner')
        businesses_data = [
            {
                'name': business.name,
                'owner': {
                    'user': {
                        'username': business.owner.user.username,
                        'first_name': business.owner.user.first_name,
                        'last_name': business.owner.user.last_name,
                    }
                }
            }
            for business in businesses
        ]
        return JsonResponse({'businesses': businesses_data})
 
 
 
 
 
 
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

@login_required
def agent_register_business(request):
    if request.method == 'POST':
        form = AgentBusinessRegistrationForm(request.POST)
        if form.is_valid():
            business_name = form.cleaned_data['business_name']
            username = form.cleaned_data['username']
            owner_email = form.cleaned_data['owner_email']
            owner_first_name = form.cleaned_data['owner_first_name']
            owner_last_name = form.cleaned_data['owner_last_name']
            
            phone_number = username
            if not phone_number.startswith('+'):
                phone_number = f'+268{phone_number}'
            
            pin = generate_pin()
            send_pin(phone_number, pin)
            password = pin  # Default pin as password

            owner_user = User.objects.create_user(
                email=owner_email,
                username=username,
                first_name=owner_first_name,
                last_name=owner_last_name,
                password=password  
            )
            owner_payscan_user = PayscanUser.objects.create(user=owner_user,default_pin=pin)

            # Get the agent
            agent = Agent.objects.get(agentuser__user=request.user)

            # Create the business
            business = Business.objects.create(owner=owner_payscan_user, name=business_name, agent=agent,priority=1)
            
            request.session['pin'] = pin
            request.session['business_id'] = business.id
            print(f'PIN: {pin}')
            
            # QR code generation logic
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

            messages.success(request, 'Business registered successfully')
            return redirect('afterlogin_agent')
        else:
            print("Form is not valid:", form.errors)  # Debug statement
    else:
        form = AgentBusinessRegistrationForm()
    return render(request, 'agents/agent_register_business.html', {'form': form})

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


########################################### AGENTS / MAKING PAYMENTS ######################################################


######################################  AGENTS / DEPOSITS AND WITHDRAWALS ##############################################

