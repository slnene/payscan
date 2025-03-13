
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login ,logout
from users.models import PayscanUser
from businesses.models import Business
from agents.models import Agent
from django.contrib.auth.decorators import login_required
from .forms import LoginForm
from django.contrib.auth.models import User

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django_ratelimit.decorators import ratelimit



def check_login_status(request):
    return JsonResponse({'is_logged_in': request.user.is_authenticated})

@login_required

def check_user_type(request):
    if hasattr(request.user, 'payscanuser'):
        if hasattr(request.user.payscanuser, 'business'):
            return JsonResponse({'is_business_user': True})
        elif hasattr(request.user.payscanuser, 'agent'):
            return JsonResponse({'is_agent_user': True})
    return JsonResponse({'is_business_user': False, 'is_agent_user': False})


from django.views.decorators.cache import cache_page
@login_required
#@cache_page(6000 * 15)  # Cache the view for 15 minutes
def scanner(request):
    return render(request,'payscan/scanner.html')

def launch(request):      
    return render(request, 'payscan/index.html')

def appLaunch(request):      
    return render(request, 'payscan/usercheck.html')

def home(request):
    return render(request,'payscan/home.html')


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def check_user_session(request):
    return JsonResponse({'logged_in': True})





@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request=request, username=username, password=password)

            if user is not None:
                payscan_user = PayscanUser.objects.get(user=user)
                
                # Check if the password used matches the default password
                if check_password(payscan_user.default_pin, user.password):
                    login(request, user)
                    messages.success(request, 'Login successful! Please reset your PIN.')
                    return redirect('reset_pin')

                login(request, user)
                
                # Set session variables for different user types
                if Agent.objects.filter(agentuser=payscan_user).exists():
                    agent = Agent.objects.get(agentuser=payscan_user)
                    request.session['agent_id'] = agent.id
                    if agent.priority == 1:
                        return redirect('afterlogin_agent')
                
                if Business.objects.filter(owner=payscan_user).exists():
                    business = Business.objects.get(owner=payscan_user)
                    request.session['business_id'] = business.id
                    if business.priority == 1:
                        return redirect('afterlogin_business')

                return redirect('afterlogin')  # Default redirect if no priority 1 found
            else:
                if User.objects.filter(username=username).exists():
                    error_message = 'Invalid PIN'
                else:
                    error_message = 'Invalid Phone Number'
                return render(request, 'users/login.html', {'form': form, 'error': error_message})
        else:
            error_message = 'Invalid Phone Number or PIN'
            return render(request, 'users/login.html', {'form': form, 'error': error_message})
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})





def logout_view(request):
    logout(request)
    return redirect('login')

def registration_error(request):
    return render(request, 'payscan/registration_error.html', {})



from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def log_qr_scan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            scanned_data = data.get('scanned_data')
            if scanned_data:
                with open('qr_scan_log.txt', 'a') as log_file:
                    log_file.write(f"Scanned QR Code: {scanned_data}\n")
                return JsonResponse({"status": "success"}, status=200)
            else:
                return JsonResponse({"status": "error", "message": "No data provided"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
