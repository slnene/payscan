
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login ,logout
from users.models import PayscanUser
from businesses.models import Business
from agents.models import Agent
from django.contrib.auth.decorators import login_required
from .forms import LoginForm
from django.contrib.auth.models import User

from django.http import JsonResponse



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

@login_required
def scanner(request):
    return render(request,'payscan/scanner.html')

def launch(request):      
    return render(request, 'payscan/index.html')

def appLaunch(request):      
    return render(request, 'payscan/usercheck.html')

def home(request):
    return render(request,'payscan/home.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request=request, username=username, password=password)
            
            if user is not None:
                login(request, user)

                # Redirect logic based on user type
                if Agent.objects.filter(agentuser=user.payscanuser).exists():
                    return redirect('afterlogin_agent')
                elif Business.objects.filter(owner=user.payscanuser).exists():
                    business = get_object_or_404(Business, owner=user.payscanuser)
                    request.session['business_id'] = business.id
                    return redirect('afterlogin_business')
                else:
                    return redirect('afterlogin')  # Default redirect
            else:
                # Check if the username exists
                if User.objects.filter(username=username).exists():
                    error_message = 'Invalid password'
                else:
                    error_message = 'Invalid username'
                
                return render(request, 'users/login.html', {'form': form, 'error': error_message})
        else:
            return render(request, 'users/login.html', {'form': form, 'error': 'Please enter both username and password'})
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


def registration_error(request):
    return render(request, 'payscan/registration_error.html', {})