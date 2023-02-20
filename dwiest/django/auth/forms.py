from django.contrib.auth import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import CharField
from django.utils.translation import gettext, gettext_lazy as _
from enum import Enum
from ..users.mfa import MfaModel, NonstickyTextInput
from ..users.conf import settings
import pyotp

class AuthenticationForm(forms.AuthenticationForm):

  # we need to inherit from str in case form.errors.as_json() is called
  class Errors(str, Enum):
    MFA_TOKEN_INVALID = 0
    MFA_TOKEN_REPLAYED = 1

  CLASS = 'class'
  SIZE = 'size'

  MFA_TOKEN_FIELD = 'mfa_token'

  mfa_token = CharField(
    label=_(settings.USERS_LOGIN_MFA_FIELD_LABEL),
    max_length=settings.USERS_MFA_FIELD_MAX_LENGTH,
    min_length=settings.USERS_MFA_FIELD_MIN_LENGTH,
    required=False,
    widget=NonstickyTextInput(
      attrs={
        CLASS: settings.USERS_MFA_FIELD_CLASS,
        SIZE: 6,
        }
      )
    )

  forms.AuthenticationForm.error_messages.update({
    Errors.MFA_TOKEN_INVALID: _(
      settings.USERS_LOGIN_MFA_TOKEN_INVALID_ERROR,
    ),
    Errors.MFA_TOKEN_REPLAYED: _(
      settings.USERS_LOGIN_MFA_TOKEN_REPLAYED_ERROR,
    ),
  })

  def clean(self):
    super().clean()
    mfa_token = self.cleaned_data.get(self.MFA_TOKEN_FIELD)

    if settings.USERS_MFA_ACCEPT_ANY_VALUE == True:
      print("!WARNING! MFA accepting any value")
      mfa_token = None

    if mfa_token != None:
      try:
        user_mfa = MfaModel.objects.get(user_id=self.user_cache.id)
        totp = pyotp.TOTP(user_mfa.secret_key)

        if mfa_token != totp.now():
          print("invalid_mfa_token")
          raise AuthenticationForm.get_invalid_mfa_token_error()
        elif mfa_token == user_mfa.last_value:
          print("replayed_mfa_token")
          raise AuthenticationForm.get_replayed_mfa_token_error()
        else:
          print("valid_mfa_token")
          user_mfa.last_value = mfa_token
          user_mfa.save()

      except ObjectDoesNotExist:
          print("No MFA object for user")
          raise AuthenticationForm.get_invalid_mfa_token_error()

    return self.cleaned_data

  @classmethod
  def get_invalid_mfa_token_error(cls):
    return ValidationError(
      cls.error_messages[Errors.MFA_TOKEN_INVALID],
      code=Errors.MFA_TOKEN_INVALID,
    )

  @classmethod
  def get_replayed_mfa_token_error(cls):
    return ValidationError(
      cls.error_messages[Errors.MFA_TOKEN_REPLAYED],
      code=Errors.MFA_TOKEN_REPLAYED,
    )
