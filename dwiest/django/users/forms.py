from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django import forms
from django.contrib.auth import forms as authForms
from django.utils.translation import ugettext, ugettext_lazy as _
import uuid
from .models import ActivationId
from .email import generate_password_change_email, generate_password_reset_email, generate_registration_email, send_email
from dwiest.django.users.mfa import MfaModel, NonstickyTextInput
import pyotp

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


class SendPasswordResetForm(forms.Form):
  email = forms.EmailField(label='Email',initial='',max_length=50)

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



class PasswordResetConfirmForm(authForms.PasswordChangeForm):

  activation_id = forms.CharField(
    label=_('Activation Id'),
    required=False,
    widget=forms.HiddenInput(),
    )

  mfa_token = forms.CharField(
    label=_("MFA Token"),
    max_length=6,
    min_length=6,
    required=False,
    widget=NonstickyTextInput(attrs={'size': 6}))

  old_password = None

  authForms.PasswordChangeForm.base_fields['new_password1'].label = 'New Password'
  authForms.PasswordChangeForm.base_fields['new_password2'].label = 'Confirm Password'

  authForms.PasswordChangeForm.error_messages.update({
    'password_mismatch':
      _("The two password fields didn't match."),
    'invalid_mfa_token': _(
      "The MFA token you entered is not correct."
    ),
    'replayed_mfa_token': _(
      "The MFA token you entered has already been used.  Please wait and enter the next value shown in your authenticator app."
    ),
    'activation_id_invalid': _(
      "The activation id is invalid."
    ),
    'activation_id_missing': _(
      "An activation id was not provided."
    ),
  })

  def clean_activation_id(self):
    activation_id = self.cleaned_data.get("activation_id")
    if activation_id and activation_id != '':
      try:
        user_activation_id = ActivationId.objects.get(value=activation_id)
        self.user = User.objects.get(id=user_activation_id.user_id, is_active=True)
      except ObjectDoesNotExist:
        raise forms.ValidationError(
          self.error_messages['activation_id_invalid'],
          code='activation_id_invalid',)
      return activation_id
    else:
      raise forms.ValidationError(
        self.error_messages['activation_id_missing'],
        code='activation_id_missing',)

  def clean_mfa_token(self):
    mfa_token = self.cleaned_data.get('mfa_token')

    if hasattr(settings, 'MFA_ACCEPT_ANY_VALUE') and settings.MFA_ACCEPT_ANY_VALUE:
      print("!WARNING! MFA accepting any value")
      mfa_token = None

    if mfa_token != None:
      try:
        user_mfa = MfaModel.objects.get(user_id=self.user.id)
        totp = pyotp.TOTP(user_mfa.secret_key)

        if mfa_token != totp.now():
          raise self.get_invalid_mfa_token_error()
        elif mfa_token == user_mfa.last_value:
          raise self.get_replayed_mfa_token_error()
        else:
          user_mfa.last_value = mfa_token
          user_mfa.save()

      except ObjectDoesNotExist:
          raise self.get_invalid_mfa_token_error()
    return mfa_token

  def get_invalid_mfa_token_error(self):
    return ValidationError(
      self.error_messages['invalid_mfa_token'],
      code='invalid_mfa_token',
    )

  def get_replayed_mfa_token_error(self):
    return ValidationError(
      self.error_messages['replayed_mfa_token'],
      code='replayed_mfa_token',
    )

def activation_id_is_valid(activation_id):
  if activation_id is not None:
    try:
      if ActivationId.objects.get(value=activation_id):
        return True
    except ObjectDoesNotExist:
      return False
  return False


class PasswordChangeForm(authForms.PasswordChangeForm):
  mfa_token = forms.CharField(
    label=_("MFA Token"),
    max_length=6,
    min_length=6,
    required=False,
    widget=NonstickyTextInput(attrs={'size': 6}))

  authForms.PasswordChangeForm.base_fields['old_password'].label = 'Password'
  authForms.PasswordChangeForm.base_fields['new_password1'].label = 'New Password'
  authForms.PasswordChangeForm.base_fields['new_password2'].label = 'Confirm Password'

  authForms.PasswordChangeForm.error_messages.update({
    'password_mismatch':
      _("The two password fields didn't match."),
    'invalid_user':
      _("Your password could not be updated."),
    'invalid_mfa_token': _(
      "The MFA token you entered is not correct."
    ),
    'replayed_mfa_token': _(
      "The MFA token you entered has already been used.  Please wait and enter the next value shown in your authenticator app."
    ),
  })


  def clean_mfa_token(self):
    mfa_token = self.cleaned_data.get('mfa_token')

    if hasattr(settings, 'MFA_ACCEPT_ANY_VALUE') and settings.MFA_ACCEPT_ANY_VALUE:
      print("!WARNING! MFA accepting any value")
      mfa_token = None

    if mfa_token != None:
      try:
        user_mfa = MfaModel.objects.get(user_id=self.user.id)
        totp = pyotp.TOTP(user_mfa.secret_key)

        if mfa_token != totp.now():
          raise self.get_invalid_mfa_token_error()
        elif mfa_token == user_mfa.last_value:
          raise self.get_replayed_mfa_token_error()
        else:
          user_mfa.last_value = mfa_token
          user_mfa.save()

      except ObjectDoesNotExist:
          raise self.get_invalid_mfa_token_error()
    return mfa_token

  def get_invalid_mfa_token_error(self):
    return ValidationError(
      self.error_messages['invalid_mfa_token'],
      code='invalid_mfa_token',
    )

  def get_replayed_mfa_token_error(self):
    return ValidationError(
      self.error_messages['replayed_mfa_token'],
      code='replayed_mfa_token',
    )

  def save(self, commit=True):
    if settings.SEND_EMAIL:
      self._sendPasswordChangeEmail()
    super().save(commit)

  def _sendPasswordChangeEmail(self):
    email = self.user.email
    try:
      User.objects.get(username=email, is_active=True)
    except ObjectDoesNotExist:
      # Silently ignore an unknown email address or inactive user
      return

    recipients = [email]
    email_message = generate_password_change_email(recipients)
    send_email(settings.EMAIL_SENDER, recipients, email_message.as_string(), settings.SMTP_SERVER, smtp_server_login=settings.EMAIL_SENDER, smtp_server_password=settings.SMTP_SERVER_PASSWORD, proxy_server=settings.PROXY_SERVER, proxy_port=settings.PROXY_PORT)
