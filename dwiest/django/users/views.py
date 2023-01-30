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

login_page = 'login'
status_page = 'home'

class RegistrationView(FormView):
  page_name = 'User Registration'
  template_name = 'registration.html'
  success_page = 'registration_success'
  fail_page = 'registration_failed'
  form_class = RegistrationForm

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    form = self.form_class()
    self.response_dict['form'] = form
    return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    form = RegistrationForm(request.POST)

    if form.is_valid():
      form.save()
      request.session['registration_success'] = True
      return HttpResponseRedirect(reverse(self.success_page), self.response_dict)
    else:
      request.session['registration_failed'] = True
      return HttpResponseRedirect(reverse(self.fail_page), self.response_dict)


class RegistrationSuccessView(TemplateView):
  page_name = 'Registration Successful'
  template_name = 'registration_success.html'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    if 'registration_success' in request.session:
      request.session.pop('registration_success')
      return render(request, self.template_name, self.response_dict)
    else:
      return HttpResponseRedirect(reverse(login_page))


class RegistrationFailedView(TemplateView):
  page_name = 'Registration Failed'
  template_name = 'registration_failed.html'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    if 'registration_failed' in request.session:
      request.session.pop('registration_failed')
      return render(request, self.template_name, self.response_dict)
    else:
      return HttpResponseRedirect(reverse(login_page))


class RegistrationConfirmView(TemplateView):
  page_name = 'Confirm Account Registration'
  template_name = None
  success_page = 'registration_confirm_success'
  fail_page = 'registration_confirm_failed'
  form_class = RegistrationConfirmForm

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    form = self.form_class(data=request.GET)

    activation_id = request.GET.get('activation_id')
    if activation_id:
      form.fields['activation_id'].initial = activation_id
    else:
      messages.error(request, 'The activation link was not valid.')
      request.session['registration_confirm_failed'] = True
      return HttpResponseRedirect(reverse(self.fail_page), self.response_dict)

    if form.is_valid():
      form.save()
      request.session['registration_confirm_success'] = True
      return HttpResponseRedirect(reverse(self.success_page), self.response_dict)
    else:
      for field, errors in form.errors.as_data().items():
        for error in errors:
          for msg in error:
            messages.error(request, msg)
      request.session['registration_confirm_failed'] = True
      return HttpResponseRedirect(reverse(self.fail_page), self.response_dict)


class RegistrationConfirmSuccessView(TemplateView):
  page_name = 'Account Activated'
  template_name = 'registration_confirm_success.html'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    if 'registration_confirm_success' in request.session:
      request.session.pop('registration_confirm_success')
      return render(request, self.template_name, self.response_dict)
    else:
      return HttpResponseRedirect(reverse(login_page))


class RegistrationConfirmFailedView(TemplateView):
  page_name = 'Account Activation Failed'
  template_name = 'registration_confirm_failed.html'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    if 'registration_confirm_failed' in request.session:
      request.session.pop('registration_confirm_failed')
      return render(request, self.template_name, self.response_dict)
    else:
      return HttpResponseRedirect(reverse(login_page), self.response_dict)


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
      return HttpResponseRedirect(reverse(login_page))


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
