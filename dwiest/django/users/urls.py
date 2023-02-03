"""users URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
import dwiest.django.users.mfa
from ..auth.views import LoginView, PasswordChangeView
from .conf import settings
from .views import *

urlpatterns = [
  path('login/',
    LoginView.as_view(),
    name='login'
    ),
  path('logout/',
    LogoutView.as_view(),
    {'next_page': settings.LOGOUT_REDIRECT_URL, 'name': 'logout'},
    name='logout'
    ),
  path('mfa/',
    include('dwiest.django.users.mfa.urls')
    ),
  path('password/reset/',
    SendPasswordResetView.as_view(),
    name='password_reset'
    ),
  path('password/reset/confirm/',
    PasswordResetConfirmView.as_view(),
    name='password_reset_confirm'
    ),
  path('password/reset/confirm/success/',
    PasswordResetConfirmSuccessView.as_view(),
    name='password_reset_confirm_success'
    ),
  path('password/reset/success/',
    SendPasswordResetSuccessView.as_view(),
    name='password_reset_success'
    ),
  path('password/reset/failed/',
    PasswordResetFailedView.as_view(),
    name='password_reset_failed'
    ),
  path('password/change/',
    PasswordChangeView.as_view(),
    name='change_password'
    ),
  path('password/change/success/',
    PasswordChangeSuccessView.as_view(),
    name='change_password_success'
    ),
  path('registration/',
    RegistrationView.as_view(),
    name='registration'
    ),
  path('registration/success/',
    RegistrationSuccessView.as_view(),
    name='registration_success'
    ),
  path('registration/failed/',
    RegistrationFailedView.as_view(),
    name='registration_failed'
    ),
  path('registration/resend/',
    RegistrationResendView.as_view(),
    name='registration_resend'
    ),
  path('registration/confirm/',
    RegistrationConfirmView.as_view(),
    name='registration_confirm'
    ),
  path('registration/confirm/failed/',
    RegistrationConfirmFailedView.as_view(),
    name='registration_confirm_failed'
    ),
  path('registration/confirm/success/',
    RegistrationConfirmSuccessView.as_view(),
    name='registration_confirm_success'
    ),
]
