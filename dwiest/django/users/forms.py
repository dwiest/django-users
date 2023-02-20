import datetime
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django import forms
from django.contrib.auth import forms as authForms
from django.utils.translation import ugettext, ugettext_lazy as _
from enum import Enum, auto
from .conf import settings
import uuid
from .mfa import MfaModel, NonstickyTextInput
from .models import ActivationId
import pyotp
import pytz

class RegistrationForm(UserCreationForm):

  class Errors(str, Enum):
    USER_ALREADY_ACTIVATED = auto()
    USER_ALREADY_EXISTS = auto()

  class Fields(str, Enum):
    USERNAME = 'username'
    PASSWORD1 = 'password1'
    PASSWORD2 = 'password2'

  user = None

  UserCreationForm.base_fields[Fields.PASSWORD2].label = \
    settings.USERS_REGISTRATION_PASSWORD2_FIELD_LABEL

  username = forms.EmailField(
    label=settings.USERS_REGISTRATION_EMAIL_FIELD_LABEL,
    initial='',
    max_length=settings.USERS_REGISTRATION_EMAIL_FIELD_MAX_LENGTH,
    )

  UserCreationForm.error_messages.update({
    Errors.USER_ALREADY_ACTIVATED:
      _(settings.USERS_REGISTRATION_USER_ALREADY_ACTIVATED_ERROR),
    Errors.USER_ALREADY_EXISTS:
      _(settings.USERS_REGISTRATION_USER_ALREADY_EXISTS_ERROR),
    })

  def clean(self):
    username = self.cleaned_data[self.__class__.Fields.USERNAME]

    try:
      # save a reference to the user, used in save()
      self.user = User.objects.get(username=username)

      # activation_id should not exist, but maybe it does?
      try:
        self.activation_id = ActivationId.objects.get(user_id=self.user.id)

      except ObjectDoesNotExist:
        pass

      if settings.USERS_REGISTRATION_ALLOW_ALREADY_ACTIVE == True:
        print("!WARNING! allowing pre-existing user")

      else:
        if self.user.is_active == True:
          raise RegistrationForm.get_user_already_activated_error()

        else:
          raise RegistrationForm.get_user_already_exists_error()

    except ObjectDoesNotExist: # new user
      pass

  @classmethod
  def get_user_already_activated_error(cls):
    return forms.ValidationError(
      cls.error_messages[cls.Errors.USER_ALREADY_ACTIVATED],
      code=cls.Errors.USER_ALREADY_ACTIVATED)

  @classmethod
  def get_user_already_exists_error(cls):
    return forms.ValidationError(
      cls.error_messages[cls.Errors.USER_ALREADY_EXISTS],
      code=cls.Errors.USER_ALREADY_EXISTS)

  def save(self):
    username = self.cleaned_data[self.__class__.Fields.USERNAME]
    email = self.cleaned_data[self.__class__.Fields.USERNAME]
    password = self.cleaned_data[self.__class__.Fields.PASSWORD1]

    # Create an account if one doesn't already exist
    if not self.user:
      self.user = User.objects.create_user(username, email, password)

    else:
      self.user.password = make_password(password)

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

  class Errors(str, Enum):
    ACTIVATION_ID_EXPIRED = auto()
    ACTIVATION_ID_INVALID = auto()
    USER_ALREADY_EXISTS = auto()
    USER_INVALID = auto()

  class Fields(str, Enum):
    ACTIVATION_ID = 'activation_id'

  activation_id = forms.CharField(
    label=_(settings.USERS_REGISTRATION_ACTIVATION_ID_FIELD_LABEL),
    required=True,
    widget=forms.HiddenInput(),
    )

  error_messages = {
    Errors.USER_INVALID:
      _(settings.USERS_REGISTRATION_USER_INVALID_ERROR),
    Errors.USER_ALREADY_EXISTS:
      _(settings.USERS_REGISTRATION_USER_ALREADY_EXISTS_ERROR),
    Errors.ACTIVATION_ID_EXPIRED:
      _(settings.USERS_REGISTRATION_ACTIVATION_ID_EXPIRED_ERROR),
    Errors.ACTIVATION_ID_INVALID:
      _(settings.USERS_REGISTRATION_ACTIVATION_ID_INVALID_ERROR),
    }

  def clean_activation_id(self):
    activation_id = self.cleaned_data[self.__class__.Fields.ACTIVATION_ID]

    try:
      self.activation_id = ActivationId.objects.get(value=activation_id)

    except ObjectDoesNotExist:
      raise RegistrationConfirmForm.get_activation_id_invalid_error()

    # check if the activation_id has expired
    if settings.USERS_ACTIVATION_ID_ALLOW_EXPIRED == True:
      print("!WARNING! Ignoring expired activation ids")

    else:
      if settings.USE_TZ:
        expires_at = datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE)) - datetime.timedelta(days=settings.REGISTRATION_EXPIRATION_DAYS)
      else:
        expires_at = datetime.datetime.now() - datetime.timedelta(days=settings.REGISTRATION_EXPIRATION_DAYS)
      if self.activation_id.created_at < expires_at:
        raise RegistrationConfirmForm.get_activation_id_expired_error()

    return activation_id

  @classmethod
  def get_activation_id_invalid_error(cls):
    return forms.ValidationError(
      cls.error_messages[cls.Errors.ACTIVATION_ID_INVALID],
      code=cls.Errors.ACTIVATION_ID_INVALID,
      )

  @classmethod
  def get_activation_id_expired_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.ACTIVATION_ID_EXPIRED],
      code=cls.Errors.ACTIVATION_ID_EXPIRED
      )

  def clean(self):
    if hasattr(self, 'activation_id'):
      try:
        self.user = User.objects.get(id=self.activation_id.user_id)

      except ObjectDoesNotExist:
        raise RegistrationConfirmForm.get_user_invalid_error()

    if settings.USERS_REGISTRATION_ALLOW_ALREADY_ACTIVE == True:
      print("!WARNING! allowing pre-existing user")

    elif self.user.is_active == True:
        raise RegistrationConfirmForm.get_user_already_exists_error()

  @classmethod
  def get_user_invalid_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.USER_INVALID],
      code=cls.Errors.USER_INVALID
      )

  @classmethod
  def get_user_already_exists_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.USER_ALREADY_EXISTS],
      code=cls.Errors.USER_ALREADY_EXISTS
      )

  def save(self):
    # mark the user as active
    self.user.is_active = True
    self.user.save()

    # delete the activation id record
    if settings.USERS_ACTIVATION_ID_DO_NOT_DELETE == True:
      print("!WARNING! Not deleting activation id")
    else:
      self.activation_id.delete()


class RegistrationResendForm(forms.Form):

  class Errors(str, Enum):
    ACTIVATION_ID_EXPIRED = auto()
    ACTIVATION_ID_INVALID = auto()
    USER_ALREADY_ACTIVATED = auto()
    USER_INVALID = auto()
    RESEND_NOT_ALLOWED = auto()

  class Fields(str, Enum):
    ACTIVATION_ID = 'activation_id'

  activation_id = forms.CharField(
    label=_(settings.USERS_REGISTRATION_ACTIVATION_ID_FIELD_LABEL),
    required=True,
    widget=forms.HiddenInput(),
    )

  error_messages = {
    Errors.USER_INVALID:
      _(settings.USERS_REGISTRATION_USER_INVALID_ERROR),
    Errors.USER_ALREADY_ACTIVATED:
      _(settings.USERS_REGISTRATION_USER_ALREADY_ACTIVATED_ERROR),
    Errors.ACTIVATION_ID_EXPIRED:
      _(settings.USERS_REGISTRATION_ACTIVATION_ID_EXPIRED_ERROR),
    Errors.ACTIVATION_ID_INVALID:
      _(settings.USERS_REGISTRATION_ACTIVATION_ID_INVALID_ERROR),
    Errors.RESEND_NOT_ALLOWED:
      _(settings.USERS_REGISTRATION_RESEND_NOT_ALLOWED_ERROR),
    }

  def clean_activation_id(self):
    activation_id = self.cleaned_data[self.__class__.Fields.ACTIVATION_ID]

    try:
      self.activation_id = ActivationId.objects.get(value=activation_id)

    except ObjectDoesNotExist:
      raise RegistrationResendForm.get_activation_id_invalid_error()

    return activation_id

  @classmethod
  def get_activation_id_invalid_error(cls):
    return forms.ValidationError(
      cls.error_messages[cls.Errors.ACTIVATION_ID_INVALID],
      code=cls.Errors.ACTIVATION_ID_INVALID
      )

  @classmethod
  def get_resend_not_allowed_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.RESEND_NOT_ALLOWED],
      code=cls.Errors.RESEND_NOT_ALLOWED)

  @classmethod
  def get_user_invalid_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.USER_INVALID],
      code=cls.Errors.USER_INVALID,)

  @classmethod
  def get_user_already_active_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.USER_ALREADY_ACTIVATED],
      code=cls.Errors.USER_ALREADY_ACTIVATED)

  def clean(self):
    if settings.USERS_REGISTRATION_ALLOW_EMAIL_RESEND != True:
      raise RegistrationResendForm.get_resend_not_allowed_error()

    # Check that the user is not already active
    try:
      self.user = User.objects.get(id=self.activation_id.user_id)

    except ObjectDoesNotExist:
      raise RegistrationResendForm.get_user_invalid_error()

    if settings.USERS_REGISTRATION_ALLOW_ALREADY_ACTIVE == True:
      print("!WARNING! allowing pre-existing user")

    elif self.user.is_active == True:
      raise RegistrationResendForm.get_user_already_active_error()

  def save(self):
    # Update the created_at timestamp
    if settings.USE_TZ == True:
      timezone = pytz.timezone(settings.TIME_ZONE)
      self.activation_id.created_at = datetime.datetime.now(tz=timezone)

    else:
       self.activation_id.created_at = datetime.datetime.now()

    self.activation_id.save()


class SendPasswordResetForm(forms.Form):

  class Errors(str, Enum):
    USER_INVALID = auto()

  class Fields(str, Enum):
    EMAIL = 'email'

  error_messages = {
    Errors.USER_INVALID:
      _(settings.USERS_PASSWORD_RESET_USER_INVALID_ERROR),
    }

  email = forms.EmailField(
    label=settings.USERS_PASSWORD_RESET_EMAIL_FIELD_LABEL,
    initial='',
    max_length=settings.USERS_EMAIL_FIELD_MAX_LENGTH,
    widget=NonstickyTextInput(
      attrs = {
      'class': settings.USERS_PASSWORD_RESET_EMAIL_FIELD_CLASS,
      }
    )
  )

  def clean(self):
    email = self.cleaned_data[self.__class__.Fields.EMAIL]

    try:
      user = User.objects.get(username=email, is_active=True)
      self.user = user

    except ObjectDoesNotExist:
      raise self.get_invalid_user_error()

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

  @classmethod
  def get_invalid_user_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.USER_INVALID],
      code=cls.Errors.USER_INVALID,
      )


class PasswordResetConfirmForm(authForms.PasswordChangeForm):

  class Errors(str, Enum):
    ACTIVATION_ID_EXPIRED = auto()
    ACTIVATION_ID_INVALID = auto()
    MFA_TOKEN_INVALID = auto()
    MFA_TOKEN_REPLAYED = auto()
    PASSWORD_MISMATCH = auto()

  class Fields(str, Enum):
    NEW_PASSWORD1 = 'new_password1'
    NEW_PASSWORD2 = 'new_password2'
    ACTIVATION_ID = 'activation_id'
    MFA_TOKEN = 'mfa_token'

  activation_id = forms.CharField(
    label=_(settings.USERS_PASSWORD_RESET_ACTIVATION_ID_FIELD_LABEL),
    required=True,
    widget=forms.HiddenInput(),
    )

  mfa_token = forms.CharField(
    label=_(settings.USERS_PASSWORD_RESET_MFA_TOKEN_LABEL),
    max_length=settings.USERS_MFA_FIELD_MAX_LENGTH,
    min_length=settings.USERS_MFA_FIELD_MIN_LENGTH,
    required=False,
    widget=NonstickyTextInput(attrs={'size': 6}))

  old_password = None # clear existing field

  authForms.PasswordChangeForm.base_fields[Fields.NEW_PASSWORD1].label = \
    settings.USERS_PASSWORD_RESET_NEW_PASSWORD1_LABEL

  authForms.PasswordChangeForm.base_fields[Fields.NEW_PASSWORD2].label = \
    settings.USERS_PASSWORD_RESET_NEW_PASSWORD2_LABEL

  authForms.PasswordChangeForm.error_messages.update({
    Errors.PASSWORD_MISMATCH:
      _(settings.USERS_PASSWORD_RESET_PASSWORD_MISMATCH_ERROR),
    Errors.MFA_TOKEN_INVALID:
      _(settings.USERS_PASSWORD_RESET_MFA_TOKEN_INVALID_ERROR),
    Errors.MFA_TOKEN_REPLAYED:
      _(settings.USERS_PASSWORD_RESET_MFA_TOKEN_REPLAYED_ERROR),
    Errors.ACTIVATION_ID_EXPIRED:
      _(settings.USERS_PASSWORD_RESET_ACTIVATION_ID_EXPIRED_ERROR),
    Errors.ACTIVATION_ID_INVALID:
      _(settings.USERS_PASSWORD_RESET_ACTIVATION_ID_INVALID_ERROR),
    })

  @classmethod
  def get_activation_id_invalid_error(cls):
    return forms.ValidationError(
      cls.error_messages[cls.Errors.ACTIVATION_ID_INVALID],
      code=cls.Errors.ACTIVATION_ID_INVALID
      )

  @classmethod
  def get_activation_id_expired_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.ACTIVATION_ID_EXPIRED],
      code=cls.Errors.ACTIVATION_ID_EXPIRED
      )

  def clean_activation_id(self):
    id = self.cleaned_data[self.__class__.Fields.ACTIVATION_ID]

    try:
      self.activation_id = ActivationId.objects.get(value=id)
      self.user = User.objects.get(id=self.activation_id.user_id, is_active=True)

    except ObjectDoesNotExist:
      raise PasswordResetConfirmForm.get_activation_id_invalid_error()

    # check if the activation_id has expired
    if settings.USERS_ACTIVATION_ID_ALLOW_EXPIRED == True:
      print("!WARNING! Ignoring expired activation ids")

    else:
      if settings.USE_TZ:
        expires_at = datetime.datetime.now(tz=pytz.timezone(settings.TIME_ZONE)) - datetime.timedelta(days=settings.USERS_PASSWORD_RESET_EXPIRATION_DAYS)

      else:
        expires_at = datetime.datetime.now() - datetime.timedelta(days=settings.USERS_PASSWORD_RESET_EXPIRATION_DAYS)

      if self.activation_id.created_at < expires_at:
        raise PasswordResetConfirmForm.get_activation_id_expired_error()

    return id

  def clean_mfa_token(self):
    mfa_token = self.cleaned_data[self.__class__.Fields.MFA_TOKEN]

    if settings.USERS_MFA_ACCEPT_ANY_VALUE == True:
      print("!WARNING! MFA accepting any value")
      mfa_token = None

    if mfa_token != None:

      try:
        user_mfa = MfaModel.objects.get(user_id=self.user.id)
        totp = pyotp.TOTP(user_mfa.secret_key)

        if mfa_token != totp.now():
          raise PasswordResetConfirmForm.get_invalid_mfa_token_error()

        elif mfa_token == user_mfa.last_value:
          raise PasswordResetConfirmForm.get_replayed_mfa_token_error()

        else:
          user_mfa.last_value = mfa_token
          user_mfa.save()

      except ObjectDoesNotExist:
        raise PasswordResetConfirmForm.get_invalid_mfa_token_error()

    return mfa_token

  @classmethod
  def get_invalid_mfa_token_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.MFA_TOKEN_INVALID],
      code=cls.Errors.MFA_TOKEN_INVALID,
      )

  @classmethod
  def get_replayed_mfa_token_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.MFA_TOKEN_REPLAYED],
      code=cls.Errors.MFA_TOKEN_REPLAYED,
      )

  def save(self):
    if settings.USERS_ACTIVATION_ID_DO_NOT_DELETE == True:
      print("!WARNING! Not deleting activation id")
    else:
      self.activation_id.delete()

    return super().save()


class PasswordChangeForm(authForms.PasswordChangeForm):

  class Errors(str, Enum):
    MFA_TOKEN_INVALID = auto()
    MFA_TOKEN_REPLAYED = auto()
    PASSWORD_MISMATCH = auto()
    USER_INVALID = auto()

  class Fields(str, Enum):
    OLD_PASSWORD = 'old_password'
    NEW_PASSWORD1 = 'new_password1'
    NEW_PASSWORD2 = 'new_password2'
    MFA_TOKEN = 'mfa_token'

  mfa_token = forms.CharField(
    label=_(settings.USERS_PASSWORD_CHANGE_MFA_TOKEN_FIELD_LABEL),
    max_length=settings.USERS_MFA_FIELD_MAX_LENGTH,
    min_length=settings.USERS_MFA_FIELD_MIN_LENGTH,
    required=False,
    widget=NonstickyTextInput(attrs={'size': 6}))

  authForms.PasswordChangeForm.base_fields[Fields.OLD_PASSWORD].label = \
    settings.USERS_PASSWORD_CHANGE_OLD_PASSWORD_FIELD_LABEL

  authForms.PasswordChangeForm.base_fields[Fields.NEW_PASSWORD1].label = \
    settings.USERS_PASSWORD_CHANGE_PASSWORD1_FIELD_LABEL

  authForms.PasswordChangeForm.base_fields[Fields.NEW_PASSWORD2].label = \
    settings.USERS_PASSWORD_CHANGE_PASSWORD2_FIELD_LABEL

  authForms.PasswordChangeForm.error_messages.update({
    Errors.PASSWORD_MISMATCH:
      _(settings.USERS_PASSWORD_CHANGE_PASSWORD_MISMATCH_ERROR),
    Errors.USER_INVALID:
      _(settings.USERS_PASSWORD_CHANGE_USER_INVALID_ERROR),
    Errors.MFA_TOKEN_INVALID:
      _(settings.USERS_PASSWORD_CHANGE_MFA_TOKEN_INVALID_ERROR),
    Errors.MFA_TOKEN_REPLAYED:
      _(settings.USERS_PASSWORD_CHANGE_MFA_TOKEN_REPLAYED_ERROR),
    })

  def clean_mfa_token(self):
    mfa_token = self.cleaned_data[self.__class__.Fields.MFA_TOKEN]

    if settings.USERS_MFA_ACCEPT_ANY_VALUE == True:
      print("!WARNING! MFA accepting any value")
      mfa_token = None

    if mfa_token != None:
      try:
        user_mfa = MfaModel.objects.get(user_id=self.user.id)
        totp = pyotp.TOTP(user_mfa.secret_key)

        if mfa_token != totp.now():
          raise PasswordChangeForm.get_invalid_mfa_token_error()

        elif mfa_token == user_mfa.last_value:
          raise PasswordChangeForm.get_replayed_mfa_token_error()

        else:
          user_mfa.last_value = mfa_token
          user_mfa.save()

      except ObjectDoesNotExist:
          raise PasswordChangeForm.get_invalid_mfa_token_error()

    return mfa_token

  @classmethod
  def get_invalid_mfa_token_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.MFA_TOKEN_INVALID],
      code=cls.Errors.MFA_TOKEN_INVALID,
    )

  @classmethod
  def get_replayed_mfa_token_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.MFA_TOKEN_REPLAYED],
      code=cls.Errors.MFA_TOKEN_REPLAYED,
    )
