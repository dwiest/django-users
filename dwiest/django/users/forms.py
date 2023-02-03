import datetime
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django import forms
from django.contrib.auth import forms as authForms
from django.utils.translation import ugettext, ugettext_lazy as _
from .conf import settings
import uuid
from .models import ActivationId
from dwiest.django.users.mfa import MfaModel, NonstickyTextInput
import pyotp
import pytz


class RegistrationForm(UserCreationForm):
  UserCreationForm.base_fields['password2'].label = 'Confirm password'

  username = forms.EmailField(label='Email',initial='',max_length=50)

  UserCreationForm.error_messages.update({
    'user_already_activated':
      _("That account has already been activated."),
    'user_already_exists':
      _("That email address has already been registered."),
    })

  def clean(self):
    username = self.cleaned_data['username']

    try:
      # save a reference to the user, used in save()
      self.user = User.objects.get(username=username)

      # activation_id should not exist, but maybe it does?
      try:
        self.activation_id = ActivationId.objects.get(user_id=self.user.id)
      except ObjectDoesNotExist:
        pass

      if getattr(settings, 'USERS_REGISTRATION_ALLOW_ALREADY_ACTIVE', False) == True:
        print("!WARNING! allowing pre-existing user")
      else:
        if self.user.is_active == True:
          raise forms.ValidationError(
            self.error_messages['user_already_activated'],
            code='user_already_activated',)
        else:
          raise forms.ValidationError(
            self.error_messages['user_already_exists'],
            code='user_already_exists',)

    except ObjectDoesNotExist: # new user
      pass

  def save(self):
    username = self.cleaned_data.get('username')
    email = self.cleaned_data.get('username')
    password = self.cleaned_data.get('password1')

    # Create an account if one doesn't already exist
    if getattr(self, 'user', None) == None:
      self.user = User.objects.create_user(username, email, password)
    else:
      self.user.password = make_password(password)
      pass

    self.user.is_active=False
    self.user.save()

    # Check if an activation record exists (it shouldn't); prevents multiple per-user
    try:
      activation_id = ActivationId.objects.get(user_id=self.user.id)
      # Update the timestamp if it does exist
      if settings.USE_TZ:
        activation_id.created_at = datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
      else:
        activation_id.created_at = datetime.datetime.now()
    except ObjectDoesNotExist:
      # Create an activation id record if one doesn't exist (it shouldn't)
      activation_id = ActivationId(value=uuid.uuid4(), user_id=self.user.id)

    activation_id.save()
    self.activation_id = activation_id


class RegistrationConfirmForm(forms.Form):
  activation_id = forms.CharField(
    label=_('Activation Id'),
    required=True,
    widget=forms.HiddenInput(),
    )

  error_messages = {
    'user_invalid':
      _("Your account could not be located."),
    'user_already_exists':
      _("Your account has already been activated."),
    'activation_id_expired': 
      _("Your account registration link has expired."),
    'activation_id_invalid': 
      _("The activation id is invalid."),
    }

  def clean_activation_id(self):
    activation_id = self.cleaned_data['activation_id']

    try:
      self.activation_id = ActivationId.objects.get(value=activation_id)
    except ObjectDoesNotExist:
      raise forms.ValidationError(
        self.error_messages['activation_id_invalid'],
        code='activation_id_invalid',)

    # check if the activation_id has expired
    if getattr(settings, 'USERS_ACTIVATION_ID_ALLOW_EXPIRED', False) == True:
      print("!WARNING! Ignoring expired activation ids")
    else:
      if settings.USE_TZ:
        expires_at = datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE)) - datetime.timedelta(days=1)
      else:
        expires_at = datetime.datetime.now() - datetime.timedelta(days=1)
      if self.activation_id.created_at < expires_at:
        raise ValidationError(
          self.error_messages['activation_id_expired'],
          code='activation_id_expired',)

    return activation_id

  def clean(self):
    if hasattr(self, 'activation_id'):
      try:
        self.user = User.objects.get(id=self.activation_id.user_id)
      except ObjectDoesNotExist:
        raise ValidationError(
          self.error_messages['user_invalid'],
          code='user_invalid',)

    if getattr(settings, 'USERS_REGISTRATION_ALLOW_ALREADY_ACTIVE', False) == True:
      print("!WARNING! allowing pre-existing user")
    elif self.user.is_active == True:
        raise ValidationError(
          self.error_messages['user_already_exists'],
          code='user_already_exists',)

  def save(self):
    # mark the user as active
    self.user.is_active = True
    self.user.save()

    # delete the activation id record
    if getattr(settings, 'USERS_ACTIVATION_ID_DO_NOT_DELETE', False) == True:
      print("!WARNING! Not deleting activation id")
    else:
      self.activation_id.delete()


class RegistrationResendForm(forms.Form):

  activation_id = forms.CharField(
    label=_('Activation Id'),
    required=True,
    widget=forms.HiddenInput(),
    )

  error_messages = {
    'username_invalid':
      _("Your account could not be located."),
    'username_already_active':
      _("Your account has already been activated."),
    'activation_id_expired':
      _("Your account registration link has expired."),
    'activation_id_invalid':
      _("The activation id is invalid."),
    'resend_not_allowed':
      _("Re-sending of registration emails is not allowed."),
    }

  def clean_activation_id(self):
    activation_id = self.cleaned_data['activation_id']

    try:
      self.activation_id = ActivationId.objects.get(value=activation_id)
    except ObjectDoesNotExist:
      raise forms.ValidationError(
        self.error_messages['activation_id_invalid'],
        code='activation_id_invalid',)

    return activation_id

  def clean(self):
    if getattr(settings, 'USERS_REGISTRATION_ALLOW_EMAIL_RESEND', False) != True:
      raise ValidationError(
        self.error_messages['resend_not_allowed'],
        code='resend_not_allowed')

    # Check that the user is not already active
    try:
      self.user = User.objects.get(id=self.activation_id.user_id)
    except ObjectDoesNotExist:
      raise ValidationError(
        self.error_messages['username_invalid'],
        code='username_invalid',)

    if getattr(settings, 'USERS_REGISTRATION_ALLOW_ALREADY_ACTIVE', False) == True:
      print("!WARNING! allowing pre-existing user")
    elif self.user.is_active == True:
      raise ValidationError(
        self.error_messages['username_already_active'],
        code='username_already_active',)

  def save(self):
    # Update the created_at timestamp
    if getattr(settings, 'USE_TZ', True) == True:
      timezone = pytz.timezone(getattr(settings, 'TIME_ZONE', 'UTC'))
      self.activation_id.created_at = datetime.datetime.now(tz=timezone)
    else:
       self.activation_id.created_at = datetime.datetime.now()

    self.activation_id.save()


class SendPasswordResetForm(forms.Form):
  email = forms.EmailField(label='Email',initial='',max_length=50)

  def sendPasswordResetEmail(self):
    email = self.cleaned_data.get('email')
    try:
      user = User.objects.get(username=email, is_active=True)
      self.user = user
    except ObjectDoesNotExist:
      # Silently ignore an unknown email address or inactive user
      return

    # Re-use an activation id record it exists; don't allows multiple per-user
    try:
      activation_id = ActivationId.objects.get(user_id=user.id)
      # Update the timestamp
      if settings.USE_TZ:
        activation_id.created_at = datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
      else:
        activation_id.created_at = datetime.datetime.now()
    except ObjectDoesNotExist:
      # No record found, create a new one
      activation_id = ActivationId(user_id=user.id, value=uuid.uuid4())
    activation_id.save()
    self.activation_id = activation_id


class PasswordResetConfirmForm(authForms.PasswordChangeForm):

  activation_id = forms.CharField(
    label=_('Activation Id'),
    required=True,
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
    'activation_id_expired': _(
      "The activation id has expired.  Please request a new pasword reset email."
    ),
    'activation_id_invalid': _(
      "The activation id is invalid."
    ),
  })

  def clean_activation_id(self):
    id = self.cleaned_data.get("activation_id")
    try:
      self.activation_id = ActivationId.objects.get(value=id)
      self.user = User.objects.get(id=self.activation_id.user_id, is_active=True)
    except ObjectDoesNotExist:
      raise forms.ValidationError(
        self.error_messages['activation_id_invalid'],
        code='activation_id_invalid',)
    # check if the activation_id has expired
    if getattr(settings, 'USERS_ACTIVATION_ID_ALLOW_EXPIRED', False) == True:
      print("!WARNING! Ignoring expired activation ids")
    else:
      if settings.USE_TZ:
        expires_at = datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE)) - datetime.timedelta(days=1)
      else:
        expires_at = datetime.datetime.now() - datetime.timedelta(days=1)
      if self.activation_id.created_at < expires_at:
        raise ValidationError(
          self.error_messages['activation_id_expired'],
          code='activation_id_expired',)
    return id

  def clean_mfa_token(self):
    mfa_token = self.cleaned_data.get('mfa_token')

    if getattr(settings, 'USERS_MFA_ACCEPT_ANY_VALUE', False) == True:
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

  def save(self):
    if getattr(settings, 'USERS_ACTIVATION_ID_DO_NOT_DELETE', False) == True:
      print("!WARNING! Not deleting activation id")
    else:
      self.activation_id.delete()

    return super().save()


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

    if getattr(settings, 'USERS_MFA_ACCEPT_ANY_VALUE', False) == True:
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

  def _sendPasswordChangeEmail(self):
    email = self.user.email
    try:
      User.objects.get(username=email, is_active=True)
    except ObjectDoesNotExist:
      # Silently ignore an unknown email address or inactive user
      return
