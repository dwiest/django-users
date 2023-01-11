from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django forms import Form
from django.utils.translation import ugettext, ugettext_lazy as _
import uuid
from .models import ActivationId
from .email import generate_password_change_email, generate_password_reset_email, generate_registration_email, send_email



class RegistrationForm(UserCreationForm):
  username = forms.EmailField(label='Email',initial='',max_length=50)

  def register(self, request):
    # form to sign up is valid
    username = self.cleaned_data.get('username')
    email = self.cleaned_data.get('username')
    password = self.cleaned_data.get('password1')
    user = User.objects.create_user(username, email, password)
    user.is_active=False
    user.save()
    activation_id = uuid.uuid4()
    user_activation_id = ActivationId(value=activation_id,user_id=user.id)
    user_activation_id.save()

    if settings.SEND_EMAIL:
      recipients = [self.cleaned_data['username']]
      email_message = generate_registration_email(recipients, activation_id)
      send_email(settings.EMAIL_SENDER, recipients, email_message.as_string(), settings.SMTP_SERVER, smtp_server_login=settings.EMAIL_SENDER, smtp_server_password=settings.SMTP_SERVER_PASSWORD, proxy_server=settings.PROXY_SERVER, proxy_port=settings.PROXY_PORT)


class SendPasswordResetForm(Form):
  email = forms.EmailField(label='email',initial='',max_length=50)

  def sendPasswordResetEmail(self):
    email = self.cleaned_data.get('email')
    try:
      user = User.objects.get(username=email, is_active=True)
    except ObjectDoesNotExist:
      # Silently ignore an unknown email address or inactive user
      return

    # Re-use the activation id for the password reset link
    activation_id = uuid.uuid4()
    user_activation_id = ActivationId.objects.get(user_id=user.id)
    user_activation_id.value = activation_id
    user_activation_id.save()

    if settings.SEND_EMAIL:
      recipients = [email]
      email_message = generate_password_reset_email(recipients, activation_id)
      send_email(settings.EMAIL_SENDER, recipients, email_message.as_string(), settings.SMTP_SERVER, smtp_server_login=settings.EMAIL_SENDER, smtp_server_password=settings.SMTP_SERVER_PASSWORD, proxy_server=settings.PROXY_SERVER, proxy_port=settings.PROXY_PORT)


class PasswordChangeForm(SetPasswordForm):

  error_messages = {
    'password_mismatch': _("The two password fields didn't match."),
    'update_failed': _("Your password could not be updated."),
    'invalid_user': _("Your password could not be updated."),
  }

  activation_id = forms.CharField(label='activation_id',initial='',required=False, max_length=36)

  def __init__(self, user, *args, **kwargs):
    self.user = user
    super(SetPasswordForm, self).__init__(*args, **kwargs)

  def clean_activation_id(self):
    activation_id = self.cleaned_data.get("activation_id")
    if activation_id and activation_id != '':
      try:
        user_activation_id = ActivationId.objects.get(value=activation_id)
        self.user = User.objects.get(id=user_activation_id.user_id, is_active=True)
      except ObjectDoesNotExist:
        raise forms.ValidationError(
          self.error_messages['update_failed'],
          code='update_failed',)
      return activation_id

  def save(self, commit=True):
    if settings.SEND_EMAIL:
      self._sendPasswordChangeEmail()
    super().save(commit)

  def _sendPasswordChangeEmail(self):
    email = self.user.email
    try:
      user = User.objects.get(username=email, is_active=True)
    except ObjectDoesNotExist:
      # Silently ignore an unknown email address or inactive user
      return

    recipients = [email]
    email_message = generate_password_change_email(recipients)
    send_email(settings.EMAIL_SENDER, recipients, email_message.as_string(), settings.SMTP_SERVER, smtp_server_login=settings.EMAIL_SENDER, smtp_server_password=settings.SMTP_SERVER_PASSWORD, proxy_server=settings.PROXY_SERVER, proxy_port=settings.PROXY_PORT)
