from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView, TemplateView
from .email import generate_account_activation_email, send_email
from .forms import RegistrationForm, SendPasswordResetForm, PasswordChangeForm
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
    activation_id = request.GET['id']

    try:
      record = ActivationId.objects.get(value=activation_id)
      user = User.objects.get(id=record.user_id)

    except ObjectDoesNotExist:
      return render(request, self.template_name, {'successful':False})

    if user.is_active == True:
        return render(request, self.template_name, {'successful':False,'already_active':True})

    user.is_active = True
    user.save()

    if settings.SEND_EMAIL:
      recipients = [user.email]
      email_message = generate_account_activation_email(recipients)
      send_email(settings.EMAIL_SENDER, recipients, email_message.as_string(), settings.SMTP_SERVER, smtp_server_login=settings.EMAIL_SENDER, smtp_server_password=settings.SMTP_SERVER_PASSWORD, proxy_server=settings.PROXY_SERVER, proxy_port=settings.PROXY_PORT)

    return render(request, self.template_name, {'successful':True})


class SendPasswordResetView(TemplateView):
  template_name = "send_password_reset.html"

  def post(self, request, *args, **kwargs):
    form = SendPasswordResetForm(request.POST)

    if form.is_valid():
      form.sendPasswordResetEmail()
      return render(request, self.template_name, {'form': form, 'completed': True})
    else:
      return render(request, self.template_name, {'form': form, 'completed': False})


class PasswordChangeView(LoginRequiredMixin, TemplateView):
  form_class = PasswordChangeForm
  page_name = 'Change Password'
  template_name = "password_change.html"
#  success_page = 'mfa_enable_success'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    form = self.form_class(request.user)
    self.response_dict['form'] = form
    return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    form = PasswordChangeForm(request.user, data=request.POST)

    if form.is_valid():
      form.save()
      # prevent the user from being logged out after a password change
      update_session_auth_hash(request, request.user)
      request.session['password_changed'] = True
      return HttpResponseRedirect(reverse('change_password_success'))
    else:
      return render(request, self.template_name, {'form': form, 'completed': False})

class PasswordChangeSuccessView(TemplateView):
  page_name = 'Password Changed'
  template_name = 'password_change_success.html'

  def get(self, request, *args, **kwargs):
    if 'password_changed' in request.session:
      request.session.pop('password_changed')
      return render(request, self.template_name)
    else:
      return HttpResponseRedirect(reverse(status_page))
