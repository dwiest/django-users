from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView, TemplateView
import json
from .conf import settings
from .forms import *
from .signals import *

login_page = 'login'
status_page = 'home'

class RegistrationView(FormView):
  page_name = 'User Registration'
  template_name = settings.USERS_REGISTRATION_TEMPLATE
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
    form = RegistrationForm(data=request.POST)
    query_string = ''
    process_errors = True

    if form.is_valid():
      form.save()
      request.session['registration_success'] = True
      user_registration.send(sender=request.user.__class__, request=request, email=form.user.email, activation_id=form.activation_id)
      return HttpResponseRedirect(reverse(self.success_page), self.response_dict)
    else:
      form_errors = json.loads(form.errors.as_json()) # as_data() doesn't include the code

      # if an account has already been activated don't show the other errors
      if form.Fields.USERNAME in form_errors:
        for error in form_errors[form.Fields.USERNAME]:
          if error['code'] == form.Errors.USER_ALREADY_ACTIVE:
            messages.error(request, error['message'])
            process_errors = False

      if process_errors:
        for field, errors in form_errors.items():
          for error in errors:
            messages.error(request, error['message'])
            if error['code'] == form.Errors.USER_ALREADY_EXISTS and form.activation_id:
              query_string = '?activation_id=' + form.activation_id.value

      request.session['registration_failed'] = True
      return HttpResponseRedirect(reverse(self.fail_page) + query_string, self.response_dict)


class RegistrationSuccessView(TemplateView):
  page_name = 'Registration Successful'
  template_name = settings.USERS_REGISTRATION_SUCCESS_TEMPLATE

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
  template_name = settings.USERS_REGISTRATION_FAILED_TEMPLATE

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
    query_string = ''
    process_errors = True

    # Ensure that an activation_id parameter was present in the query string
    activation_id = request.GET.get('activation_id')
    if activation_id:
      form.fields[form.Fields.ACTIVATION_ID].initial = activation_id
    else:
      messages.error(request, 'The activation link was not valid.')
      request.session['registration_confirm_failed'] = True
      return HttpResponseRedirect(reverse(self.fail_page), self.response_dict)

    if form.is_valid():
      form.save()
      request.session['registration_confirm_success'] = True
      user_registration_confirmed.send(sender=request.user.__class__, request=request, email=form.user.email)
      return HttpResponseRedirect(reverse(self.success_page), self.response_dict)
    else:
      form_errors = json.loads(form.errors.as_json()) # as_data() ddoesn't include the code

      # if an account has already been activated don't show the other errors
      if '__all__' in form_errors:
        for error in form_errors['__all__']:
          if error['code'] == form.Errors.USER_ALREADY_EXISTS:
            messages.error(request, error['message'])
            process_errors = False

      if process_errors:
        for field, errors in form_errors.items():
          for error in errors:
            messages.error(request, error['message'])
            if error['code'] == form.Errors.ACTIVATION_ID_EXPIRED:
              query_string = '?activation_id=' + activation_id

      request.session['registration_confirm_failed'] = True
      return HttpResponseRedirect(reverse(self.fail_page) + query_string, self.response_dict)


class RegistrationConfirmSuccessView(TemplateView):
  page_name = 'Account Activated'
  template_name = settings.USERS_REGISTRATION_CONFIRM_SUCCESS_TEMPLATE

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
  template_name = settings.USERS_REGISTRATION_CONFIRM_FAILED_TEMPLATE

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


class RegistrationResendView(TemplateView):
  page_name = 'Resend Registration Email'
  template_name = None
  success_page = 'registration_success'
  fail_page = 'registration_failed'
  form_class = RegistrationResendForm

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):

    if request.GET.get('activation_id') == None:
      request.session[self.fail_page] = True
      return HttpResponseRedirect(reverse(self.fail_page), self.response_dict)

    elif settings.USERS_REGISTRATION_ALLOW_EMAIL_RESEND != True:
      messages.error(request, 'Re-sending of registration emails is not allowed.')
      request.session[self.fail_page] = True
      return HttpResponseRedirect(reverse(self.fail_page), self.response_dict)

    form = self.form_class(data=request.GET)
    if form.is_valid():
      form.save()
      request.session[self.success_page] = True
      resend_registration_email.send(sender=request.user.__class__, request=request, email=form.user.email, activation_id=form.activation_id)
      return HttpResponseRedirect(reverse(self.success_page), self.response_dict)
    else:
      for field, errors in form.errors.as_data().items():
        for error in errors:
          for msg in error:
            messages.error(request, msg)
      request.session[self.fail_page] = True
      return HttpResponseRedirect(reverse(self.fail_page), self.response_dict)


class SendPasswordResetView(TemplateView):
  page_name = 'Password Reset'
  template_name = settings.USERS_PASSWORD_RESET_TEMPLATE
  success_page = 'password_reset_success'
  fail_page = 'password_reset_failed'
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
      request.session['password_reset'] = True
      password_reset_request.send(sender=request.user.__class__, request=request, email=form.user.email, activation_id=form.activation_id)
      return HttpResponseRedirect(reverse(self.success_page))
    else:
      form_errors = json.loads(form.errors.as_json()) # as_data() ddoesn't include the code
      for field, errors in form_errors.items():
        for error in errors:
          messages.error(request, error['message'])
      request.session['password_reset_failed'] = True
      return HttpResponseRedirect(reverse(self.fail_page))


class SendPasswordResetSuccessView(TemplateView):
  page_name = 'Password Reset Email Sent'
  template_name = settings.USERS_PASSWORD_RESET_SUCCESS_TEMPLATE

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
  template_name = settings.USERS_PASSWORD_RESET_CONFIRM_TEMPLATE
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
      form.fields[form.Fields.ACTIVATION_ID].initial = activation_id
      return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    form = self.form_class(None, data=request.POST)
    self.response_dict['form'] = form

    if form.is_valid():
      # prevent the user from being logged out after a password change
      update_session_auth_hash(request, request.user)
      request.session['password_reset_confirm'] = True
      form.save()
      password_changed.send(sender=request.user.__class__, request=request, email=form.user.email)
      return HttpResponseRedirect(reverse(self.success_page))
    else:
      # Don't allow form re-submission for activation id issues
      if form.Fields.ACTIVATION_ID in form.errors:
        request.session['password_reset_failed'] = True
        for error in form.errors[form.Fields.ACTIVATION_ID]:
          messages.error(request, error)
        return HttpResponseRedirect(reverse(self.fail_page))
      else:
        return render(request, self.template_name, self.response_dict)


class PasswordResetConfirmSuccessView(TemplateView):
  page_name = 'Password Changed'
  template_name = settings.USERS_PASSWORD_RESET_CONFIRM_SUCCESS_TEMPLATE

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
  template_name = settings.USERS_PASSWORD_RESET_FAILED_TEMPLATE

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
  template_name = settings.USERS_PASSWORD_CHANGE_TEMPLATE
  success_page = 'change_password_success'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    self.response_dict['form'] = self.form_class(request.user)
    return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    form = self.form_class(request.user, data=request.POST)
    self.response_dict['form'] = form

    if form.is_valid():
      form.save()
      # prevent the user from being logged out after a password change
      update_session_auth_hash(request, request.user)
      request.session['password_changed'] = True
      password_changed.send(sender=request.user.__class__, request=request, email=request.user.email)
      return HttpResponseRedirect(reverse(self.success_page))
    else:
      return render(request, self.template_name, self.response_dict)


class PasswordChangeSuccessView(TemplateView):
  page_name = 'Password Changed'
  template_name = settings.USERS_PASSWORD_CHANGE_SUCCESS_TEMPLATE

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
