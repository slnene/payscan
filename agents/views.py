from decimal import Decimal
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect

from users.models import PayscanUser
from businesses.models import Business
from agents.models import Agent
from payscan.models import Transaction

from django.contrib.auth.decorators import login_required
from .forms import AgentRegisterForm,AgentLoginForm,AgentBusinessRegistrationForm

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


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

#####Agent Suite###

def register_agent(request):
    if request.method == 'POST':
        form = AgentRegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            password = form.cleaned_data['password1']
                            
            user = User.objects.create_user(email=email, username=username, first_name=first_name, last_name=last_name, password=password)          
            payscan_user = PayscanUser.objects.create(user=user)
            
            Agent.objects.create(agentuser=payscan_user)

            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login_agent')
        else:
            print("Form is not valid:", form.errors)  # Debug statement
    else:
        form = AgentRegisterForm()
    return render(request, 'agents/register_agent.html', {'form': form})


def register_agent_2(request):
    if request.method == 'POST':
        form = AgentRegisterForm(request.POST)
        if form.is_valid():
            
            payscan_user=PayscanUser.objects.create(user=request.user)
            Agent.objects.create(agentuser=payscan_user)

            return redirect('login_agent')     
    else:
            # Handle the case where the passwords do not match
        form = AgentRegisterForm()            
    return render(request, 'agents/register_agent.html', {'form': form})




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




def generate_default_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def send_sms(phone_number, message):
    account_sid = 'your_account_sid'
    auth_token = 'your_auth_token'
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=message,
        from_='+1234567890',
        to=phone_number
    )

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
            default_password = generate_default_password()

            # Create a new user for the business owner with the default password
            owner_user = User.objects.create_user(
                email=owner_email,
                username=username,
                first_name=owner_first_name,
                last_name=owner_last_name,
                password=default_password
            )
            owner_payscan_user = PayscanUser.objects.create(user=owner_user)

            # Get the agent
            agent = Agent.objects.get(agentuser__user=request.user)

            # Create the business
            business = Business.objects.create(owner=owner_payscan_user, name=business_name, agent=agent)

            # Send the default password via SMS
            sms_message = f"Your Payscan account has been created. Your default password is: {default_password}"
            send_sms(username, sms_message)  # Assuming the username is the phone number

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
def initial_password_setup(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password and new_password == confirm_password and len(new_password) == 5:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Prevents logging the user out
            messages.success(request, 'Password updated successfully')
            return redirect('afterlogin_business')  # Redirect to the business dashboard
        else:
            messages.error(request, 'Passwords must match and be 5 digits long')

    return render(request, 'agents/initial_password_setup.html')
