import base64
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from enum import Enum, auto
from io import BytesIO
import pyotp
import qrcode
from ..conf import settings

# copied from https://stackoverflow.com/questions/43425116/clear-all-form-fields-on-validation-error-in-django
class NonstickyTextInput(forms.TextInput):
    '''Custom text input widget that's "non-sticky"
    (i.e. does not remember submitted values).
    '''
    def get_context(self, name, value, attrs):
        value = None  # Clear the submitted value.
        return super().get_context(name, value, attrs)

class MfaEnableForm(forms.Form):

  class Errors(str, Enum):
    PASSWORD_INVALID = auto()
    TOKEN_INVALID = auto()

  class Fields(str, Enum):
    PASSWORD = 'password'
    SECRET_KEY = 'secret_key'
    TOKEN = 'token'

  token = forms.CharField(
    label=settings.USERS_MFA_TOKEN_FIELD_LABEL,
    initial='',
    max_length=settings.USERS_MFA_FIELD_MAX_LENGTH,
    min_length=settings.USERS_MFA_FIELD_MIN_LENGTH,
    required=True,
    widget=NonstickyTextInput(
      attrs={
        'class': settings.USERS_MFA_FIELD_CLASS,
        'size': settings.USERS_MFA_TOKEN_LENGTH,
        }
      )
    )

  secret_key = forms.CharField(
    initial='',
    max_length=settings.USERS_MFA_SECRET_KEY_MAX_LENGTH,
    min_length=settings.USERS_MFA_SECRET_KEY_MIN_LENGTH,
    required=True,
    widget=forms.HiddenInput())

  password = forms.CharField(
    label=_(settings.USERS_MFA_PASSWORD_FIELD_LABEL),
    strip=False,
    widget=forms.PasswordInput(
      attrs={
        'class': settings.USERS_MFA_PASSWORD_CLASS,
        "autocomplete": "current-password",
        }
      ),
    )

  error_messages = {
    Errors.PASSWORD_INVALID:
      _(settings.USERS_MFA_PASSWORD_INVALID_ERROR),
    Errors.TOKEN_INVALID:
      _(settings.USERS_MFA_TOKEN_INVALID_ERROR),
  }

  def __init__(self, user=None, *args, **kwargs):
    super(forms.Form, self).__init__(*args, **kwargs)

    self.user = user

    if settings.USERS_MFA_SECRET_KEY:
      self.initial[self.Fields.SECRET_KEY] = settings.USERS_MFA_SECRET_KEY

    elif kwargs.get('data'):
      self.initial[self.Fields.SECRET_KEY] = kwargs['data'][self.Fields.SECRET_KEY]

    else:
      self.initial[self.Fields.SECRET_KEY] = pyotp.random_base32()

    self.totp = pyotp.TOTP(self.initial[self.Fields.SECRET_KEY])
    self.account_name = None

    self.mfa_issuer_name = settings.USERS_MFA_ISSUER_NAME

    self.provisioning_uri = self.totp.provisioning_uri(
      name=self.account_name,
      issuer_name=self.mfa_issuer_name
      )

    self.secret_key_image = self.get_qrcode(self.provisioning_uri)

  def clean(self):
    if self.user.check_password(self.cleaned_data[self.Fields.PASSWORD]) != True:
      raise self.get_invalid_password_error()

    if settings.USERS_MFA_ACCEPT_ANY_VALUE == True:
      print("!WARNING! MFA accepting any value")

    elif self.cleaned_data[self.Fields.TOKEN] == self.totp.now():
      pass

    else:
      raise self.get_invalid_token_error()

    return super().clean()

  @classmethod
  def get_token_invalid_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.TOKEN_INVALID_ERROR],
      code=cls.Errors.TOKEN_INVALID_ERROR,
      )

  @classmethod
  def get_invalid_password_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.PASSWORD_INVALID_ERROR],
      code=cls.Errors.PASSWORD_INVALID_ERROR,
      )

  @staticmethod
  def get_qrcode(text):
    qr = qrcode.QRCode(
      version=settings.USERS_MFA_QRCODE_VERSION,
      error_correction=settings.USERS_MFA_QRCODE_ERROR_CORRECTION,
      box_size=settings.USERS_MFA_QRCODE_BOX_SIZE,
      border=settings.USERS_MFA_QRCODE_BORDER,
    )

    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(
      fill_color=settings.USERS_MFA_QRCODE_FILL_COLOR,
      back_color=settings.USERS_MFA_QRCODE_BACKGROUND_COLOR,
      ).convert('RGB')

    stream = BytesIO()
    img.save(stream, format=settings.USERS_MFA_QRCODE_IMAGE_FORMAT)
    encoded_img = base64.b64encode(stream.getvalue()).decode("utf-8")
    return encoded_img


class MfaDisableForm(forms.Form):

  class Errors(str, Enum):
    PASSWORD_INVALID = auto()
    CONFIRM_MESSAGE_INVALID = auto()

  class Fields(str, Enum):
    PASSWORD = 'password'
    DISABLE_MFA = 'disable_mfa'

  confirm_message = settings.USERS_MFA_CONFIRM_MESSAGE

  disable_mfa = forms.CharField(
    label=_(settings.USERS_MFA_DISABLE_FIELD_LABEL),
    initial='',
    required=True,
    widget=forms.TextInput(
      attrs={
        'size': len(settings.USERS_MFA_CONFIRM_MESSAGE),
        }
      )
    )

  password = forms.CharField(
    label=_(settings.USERS_MFA_PASSWORD_FIELD_LABEL),
    strip=False,
    widget=forms.PasswordInput(
      attrs={
        "autocomplete": "current-password",
        }
      ),
    )

  error_messages = {
    Errors.PASSWORD_INVALID:
      _(settings.USERS_MFA_PASSWORD_INVALID_ERROR),
    Errors.CONFIRM_MESSAGE_INVALID:
      _(settings.USERS_MFA_CONFIRM_MESSAGE_INVALID),
  }

  def __init__(self, user=None, *args, **kwargs):
    super(forms.Form, self).__init__(*args, **kwargs)
    self.user = user

  def clean(self):
    if self.user.check_password(self.cleaned_data[self.Fields.PASSWORD]) != True:
      raise self.get_invalid_password_error()

    if self.cleaned_data[self.Fields.DISABLE_MFA] != self.confirm_message:
      raise self.get_confirm_message_invalid_error()

  @classmethod
  def get_password_invalid_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.PASSWORD_INVALID],
      code=cls.Errors.PASSWORD_INVALID,
      )

  @classmethod
  def get_confirm_message_invalid_error(cls):
    return ValidationError(
      cls.error_messages[cls.Errors.CONFIRM_MESSAGE_INVALID],
      code=cls.Errors.CONFIRM_MESSAGE_INVALID,
      )
