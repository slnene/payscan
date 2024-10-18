"""
RL configuration for payscan project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from users import views as user_views
from agents import views as agent_views
from businesses import views as business_views
from payscan import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('check_login_status/', views.check_login_status, name='check_login_status'),
    path('check_user_type/', views.check_user_type, name='check_user_type'),
    path('',views.launch),
    path('home/', views.home, name='home'),
    path('register/', user_views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registration_error/', views.registration_error, name='registration_error'),

    path('afterlogin/', user_views.dashboard, name='afterlogin'),
    path('deposit/', user_views.deposit, name='deposit'),
    path('withdraw/', user_views.withdraw, name='withdraw'),
    path('choose_wallet/<int:business_id>/',user_views.choose_wallet, name='choose_wallet'),
    path('choose_wallet_dynamic/<int:business_id>/',user_views.choose_wallet_dynamic, name='choose_wallet_dynamic'),
    path('choose_deposit/',user_views.choose_deposit, name='choose_deposit'),
    path('choose_withdraw/',user_views.choose_withdraw, name='choose_withdraw'),
    path('confirm_payment/<int:business_id>/', user_views.confirm_payment, name='confirm_payment'),

    path('payment/<int:business_id>/', user_views.payment, name='payment'),
    path('payment_momo/<int:business_id>/', user_views.payment_momo, name='payment_momo'),
    path('payment_error', user_views.payment_error, name='payment_error'),

    path('payment_success/<int:transaction_id>/', user_views.payment_success, name='payment_success'),

    path('scanner/', views.scanner, name='scanner'),
    path('success/<int:transaction_id>/', user_views.payment_success, name='payment_success'),
    path('applaunch/',views.appLaunch),


    path('register_agent/', agent_views.register_agent, name='register_agent'),
    path('register_agent_2/', agent_views.register_agent_2, name='register_agent_2'),
    path('afterlogin_agent/', agent_views.agent_dashboard, name='agent_dashboard'),
    path('agent_register_business/', agent_views.agent_register_business, name='agent_register_business'),
    path('agent_dashboard/', agent_views.agent_dashboard, name='agent_dashboard'),
    path('agent_register_business/', agent_views.agent_register_business, name='register_business'),
    
    
    path('register_business/', business_views.register_business, name='register_business'),
    path('register_business_2/', business_views.register_business_2, name='register_business_2'),
    path('register_business_transport/', business_views.register_business_transport, name='register_business_transport'),
    path('afterlogin_business/', business_views.business_dashboard, name='afterlogin_business'),
    path('payment_business/<int:business_id>/', business_views.business_payment, name='payment_business'),
    path('withdraw_business/', business_views.business_withdraw, name='withdraw_business'),
    path('generate_payment_qr/', business_views.generate_payment_qr, name='generate_payment_qr'),
    path('generate_payment_qr_transport/', business_views.generate_payment_qr_transport, name='generate_payment_qr_transport'),

    
    ]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
