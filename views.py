from decimal import Decimal
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import PayscanUser, Transaction, Business
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm  ,DepositForm,WithdrawForm,PaymentForm,BusinessRegisterForm
from django.http import HttpResponse


def scanner(request):
    return render(request,'payscan/scanner.html')

def launch(request):      
    return render(request, 'payscan/index.html')

def home(request):
    return render(request,'payscan/home.html')

def register(request):
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
    return render(request, 'payscan/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'business'):
                return redirect('/business_dashboard', business_id=user.business.id)
            else:
                return redirect('/afterlogin')
        else:
            return render(request, 'payscan/login.html', {'error': 'Invalid username or password'})
    else:
        return render(request, 'payscan/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    
    try:
        payscan_user = PayscanUser.objects.get(user=request.user)
        
        transactions = Transaction.objects.filter(payer=payscan_user).order_by('-timestamp')
    
        return render(request, 'payscan/dashboard.html', {'balance': payscan_user.balance ,'transactions': transactions})

    except PayscanUser.DoesNotExist:
        return render(request, 'payscan/login.html')
        pass
    
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
    payscan_user = PayscanUser.objects.get(user=request.user)
    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if payscan_user.balance >= amount:
                payscan_user.balance -= amount
                payscan_user.save()
                Transaction.objects.create(payer=payscan_user, amount=amount, transaction_type='withdraw')
                return redirect('/afterlogin')
    else:
        form = WithdrawForm()
    return render(request, 'payscan/withdraw.html', {'form': form})

@login_required
def payment(request, business_id):
    business = get_object_or_404(Business, id=business_id)
    payscan_user = PayscanUser.objects.get(user=request.user)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            business = form.cleaned_data['business']
            amount = form.cleaned_data['amount']
            if payscan_user.balance >= amount:
                payscan_user.balance -= amount
                payscan_user.save()
                business.balance += amount
                business.save()
                transaction = Transaction.objects.create(payer=payscan_user, payee=business, amount=amount, transaction_type='payment')
                return redirect('payment_success', transaction_id=transaction.id)
    else:
        form = PaymentForm()
    return render(request, 'payscan/payment.html', {'form': form , 'business': business})

@login_required
def payment_success(request, transaction_id):
    transaction = Transaction.objects.get(id=transaction_id)
    return render(request, 'payscan/payment_success.html', {'transaction': transaction})


@login_required
def register_business(request):
    if request.method == 'POST':
        form = BusinessRegisterForm(request.POST)
        if form.is_valid():
            business = form.save(commit=False)
            business.owner = PayscanUser.objects.get(user=request.user)
            business.save()
            return redirect('/login', business_id=business.id)
    else:
        form = BusinessRegisterForm()
    return render(request, 'payscan/register_business.html', {'form': form})

@login_required
def edit_business(request, business_id):
    business = get_object_or_404(Business, id=business_id, owner=PayscanUser.objects.get(user=request.user))
    if request.method == 'POST':
        form = BusinessRegisterForm(request.POST, instance=business)
        if form.is_valid():
            form.save()
            return redirect('business_dashboard', business_id=business.id)
    else:
        form = BusinessRegisterForm(instance=business)
    return render(request, 'payscan/edit_business.html', {'form': form})

@login_required
def business_dashboard(request, business_id):
    business = get_object_or_404(Business, id=business_id, owner=PayscanUser.objects.get(user=request.user))
    return render(request, 'payscan/business_dashboard.html', {'business': business})
