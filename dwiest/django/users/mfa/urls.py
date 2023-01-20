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
from .views import MfaEnableView, MfaDisableView

urlpatterns = [
  path('', TemplateView.as_view(template_name='mfa/index.html'), name='mfa'),
  path('enable/', MfaEnableView.as_view(), name='mfa_enable'),
  path('enable/success/', TemplateView.as_view(template_name='mfa/enable_success.html'), name='mfa_enable_success'),
  path('disable/', MfaDisableView.as_view(), name='mfa_disable'),
]
