"""djang-users URL Configuration

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
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include
from .views import RegistrationView, ActivateRegistrationView, SendPasswordResetView, PasswordChangeView

urlpatterns = [
    path('django/register/', RegistrationView.as_view(), name='register'),
    path('django/activate', ActivateRegistrationView.as_view(), name='activate'),
    path('django/login/', LoginView.as_view(), name='login'),
    path('django/logout/', LogoutView.as_view(), {'next_page': settings.LOGOUT_REDIRECT_URL, 'name': 'logout'}, name='logout'),
    path('django/resetPassword/', SendPasswordResetView.as_view(), name='reset_password'),
    path('django/changePassword/', PasswordChangeView.as_view(), name='change_password'),
]
