"""MFA URL Configuration
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
from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
  path('', views.MfaStatusView.as_view(), name='mfa_status'),
  path('enable/', views.MfaEnableView.as_view(), name='mfa_enable'),
  path('enable/success/', views.MfaEnableSuccessView.as_view(), name='mfa_enable_success'),
  path('disable/', views.MfaDisableView.as_view(), name='mfa_disable'),
  path('disable/success/', views.MfaDisableSuccessView.as_view(), name='mfa_disable_success'),
]
