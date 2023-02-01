from django.contrib.auth import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import CharField
from django.utils.translation import gettext, gettext_lazy as _
from dwiest.django.users.mfa import MfaModel, NonstickyTextInput
from dwiest.django.users.conf import settings
import pyotp

class AuthenticationForm(forms.AuthenticationForm):
  mfa_token = CharField(
    label=_("MFA token"),
    max_length=6,
    min_length=6,
    required=False,
    widget=NonstickyTextInput(attrs={'size': 6}))

  forms.AuthenticationForm.error_messages.update({
    'invalid_mfa_token': _(
      "The MFA token you entered is not correct."
    ),
    'replayed_mfa_token': _(
      "The MFA token you entered has already been used.Please wait and enter the next value shown in your authenticator app."
    ),
  })

  def clean(self):
    super().clean()
    mfa_token = self.cleaned_data.get('mfa_token')

    if hasattr(settings, 'USERS_MFA_ACCEPT_ANY_VALUE') and settings.USERS_MFA_ACCEPT_ANY_VALUE:
      print("!WARNING! MFA accepting any value")
      mfa_token = None

    if mfa_token != None:
      try:
        user_mfa = MfaModel.objects.get(user_id=self.user_cache.id)
        totp = pyotp.TOTP(user_mfa.secret_key)

        if mfa_token != totp.now():
          print("invalid_mfa_token")
          raise self.get_invalid_mfa_token_error()
        elif mfa_token == user_mfa.last_value:
          print("replayed_mfa_token")
          raise self.get_replayed_mfa_token_error()
        else:
          print("valid_mfa_token")
          user_mfa.last_value = mfa_token
          user_mfa.save()

      except ObjectDoesNotExist:
          print("No MFA object for user")
          raise self.get_invalid_mfa_token_error()

    return self.cleaned_data

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
