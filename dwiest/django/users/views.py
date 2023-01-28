from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView, TemplateView
from .email import generate_account_activation_email, send_email
from .forms import *
from .models import ActivationId

status_page = 'home'

class RegistrationView(FormView):
  template_name = "user_registration.html"
  form_class = RegistrationForm

  def post(self, request, *args, **kwargs):
    form = RegistrationForm(request.POST)

    if form.is_valid():
      form.register(request)
      return render(request, self.template_name, {'form': form, 'completed': True})
    else:
        return render(request, self.template_name, {'form': form, 'completed': False})


class ActivateRegistrationView(TemplateView):
  template_name = "activate_registration.html"

  def get(self, request, *args, **kwargs):
    activation_id = request.GET.get('activation_id')

    try:
      record = ActivationId.objects.get(value=activation_id)
      user = User.objects.get(id=record.user_id)

    except ObjectDoesNotExist:
      return render(request, self.template_name, {'successful':False})

    if user.is_active == True:
        return render(request, self.template_name, {'successful':False,'already_active':True})

    user.is_active = True
    user.save()

    if hasattr(settings, 'SEND_EMAIL') and settings.SEND_EMAIL:
      recipients = [user.email]
      email_message = generate_account_activation_email(recipients)
      send_email(settings.EMAIL_SENDER, recipients, email_message.as_string(), settings.SMTP_SERVER, smtp_server_login=settings.EMAIL_SENDER, smtp_server_password=settings.SMTP_SERVER_PASSWORD, proxy_server=settings.PROXY_SERVER, proxy_port=settings.PROXY_PORT)

    return render(request, self.template_name, {'successful':True})


class SendPasswordResetView(TemplateView):
  page_name = 'Password Reset'
  template_name = 'send_password_reset.html'
  success_page = 'password_reset_success'
  form_class = SendPasswordResetForm

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    form = self.form_class()
    self.response_dict['form'] = form
    return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    form = self.form_class(data=request.POST)
    self.response_dict['form'] = form

    if form.is_valid():
      form.sendPasswordResetEmail()
      request.session['password_reset'] = True
      return HttpResponseRedirect(reverse(self.success_page))
    else:
      return render(request, self.template_name, self.response_dict)


class SendPasswordResetSuccessView(TemplateView):
  page_name = 'Password Reset Email Sent'
  template_name = 'send_password_reset_success.html'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    if 'password_reset' in request.session:
      request.session.pop('password_reset')
      return render(request, self.template_name, self.response_dict)
    else:
      return HttpResponseRedirect(reverse('login'))


class PasswordResetConfirmView(TemplateView):
  page_name = 'Password Reset'
  template_name = 'password_reset_confirm.html'
  success_page = 'password_reset_confirm_success'
  fail_page = 'password_reset_failed'
  form_class = PasswordResetConfirmForm

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    activation_id = request.GET.get('activation_id')

    if activation_id is None:
      return HttpResponseRedirect(reverse(self.fail_page))

    else:
      form = self.form_class(None)
      self.response_dict['form'] = form
      form.fields['activation_id'].initial = activation_id
      return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    form = self.form_class(None, data=request.POST)
    self.response_dict['form'] = form

    if form.is_valid():
      # prevent the user from being logged out after a password change
      update_session_auth_hash(request, request.user)
      request.session['password_reset_confirm'] = True
      form.save()
      return HttpResponseRedirect(reverse(self.success_page))
    else:
      # Don't allow form re-submission for activation id issues
      if 'activation_id' in form.errors:
        request.session['password_reset_failed'] = True
        for error in form.errors['activation_id']:
          messages.error(request, error)
        return HttpResponseRedirect(reverse(self.fail_page))
      else:
        return render(request, self.template_name, self.response_dict)


class PasswordResetConfirmSuccessView(TemplateView):
  page_name = 'Password Changed'
  template_name = 'password_reset_confirm_success.html'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    if 'password_reset_confirm' in request.session:
      request.session.pop('password_reset_confirm')
      return render(request, self.template_name, self.response_dict)
    else:
      return HttpResponseRedirect(reverse(status_page))


class PasswordResetFailedView(TemplateView):
  page_name = 'Password Reset Failed'
  template_name = 'password_reset_failed.html'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    if 'password_reset_failed' in request.session:
      request.session.pop('password_reset_failed')
      return render(request, self.template_name, self.response_dict)
    else:
      return HttpResponseRedirect(reverse(status_page))


class PasswordChangeView(LoginRequiredMixin, TemplateView):
  form_class = PasswordChangeForm
  page_name = 'Change Password'
  template_name = "password_change.html"

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    self.response_dict['form'] = self.form_class(request.user)
    return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    form = PasswordChangeForm(request.user, data=request.POST)
    self.response_dict['form'] = form

    if form.is_valid():
      form.save()
      # prevent the user from being logged out after a password change
      update_session_auth_hash(request, request.user)
      request.session['password_changed'] = True
      return HttpResponseRedirect(reverse('change_password_success'))
    else:
      return render(request, self.template_name, self.response_dict)


class PasswordChangeSuccessView(TemplateView):
  page_name = 'Password Changed'
  template_name = 'password_change_success.html'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    if 'password_changed' in request.session:
      request.session.pop('password_changed')
      return render(request, self.template_name, self.response_dict)
    else:
      return HttpResponseRedirect(reverse(status_page))
