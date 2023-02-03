from django import forms
from django.core.exceptions import ValidationError
from dwiest.django.users.conf import settings
from dwiest.django.users.email import generate_mfa_disabled_email, generate_mfa_enabled_email, send_email
from django.utils.translation import gettext as _
import base64
from io import BytesIO
import pyotp
import qrcode

# copied from https://stackoverflow.com/questions/43425116/clear-all-form-fields-on-validation-error-in-django
class NonstickyTextInput(forms.TextInput):
    '''Custom text input widget that's "non-sticky"
    (i.e. does not remember submitted values).
    '''
    def get_context(self, name, value, attrs):
        value = None  # Clear the submitted value.
        return super().get_context(name, value, attrs)

class MfaEnableForm(forms.Form):
  token = forms.CharField(
    label='Token',
    initial='',
    max_length='6',
    min_length='6',
    required=True,
    widget=NonstickyTextInput(attrs={'size': '6'}))

  secret_key = forms.CharField(
    initial='',
    max_length='32',
    min_length='32',
    required=True,
    widget=forms.HiddenInput())

  password = forms.CharField(
    label=_("Password"),
    strip=False,
    widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
  )

  error_messages = {
    'invalid_password':
      _('The password you entered is incorrect.')
  }

  def __init__(self, user=None, *args, **kwargs):
    super(forms.Form, self).__init__(*args, **kwargs)

    self.user = user

    if getattr(settings, 'USERS_MFA_SECRET_KEY', None) != None:
      self.initial['secret_key'] = settings.USERS_MFA_SECRET_KEY
    elif kwargs.get('data'):
      self.initial['secret_key'] = kwargs['data']['secret_key']
    else:
      self.initial['secret_key'] = pyotp.random_base32()

    self.totp = pyotp.TOTP(self.initial['secret_key'])
    self.account_name = None

    if hasattr(settings, 'USERS_MFA_ISSUER_NAME'):
      self.mfa_issuer_name = settings.USERS_MFA_ISSUER_NAME
    else:
      self.mfa_issuer_name = None

    self.provisioning_uri = self.totp.provisioning_uri(
      name=self.account_name,
      issuer_name=self.mfa_issuer_name)

    self.secret_key_image = get_qrcode(self.provisioning_uri)

  def clean(self):
    if self.user.check_password(self.cleaned_data.get('password')) != True:
      raise self.get_invalid_password_error()

    if hasattr(settings, 'USERS_MFA_ACCEPT_ANY_VALUE') and settings.USERS_MFA_ACCEPT_ANY_VALUE:
      print("!WARNING! MFA accepting any value")
    elif self.cleaned_data.get('token') == self.totp.now():
      pass
    else:
      raise ValidationError('Invalid token, please try again')

    return super().clean()

  def get_invalid_password_error(self):
    return ValidationError(
      self.error_messages['invalid_password'],
      code='invalid_password',
    )


def get_qrcode(text):
  qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=5,
    border=4
  )
  qr.add_data(text)
  qr.make(fit=True)
  img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
  stream = BytesIO()
  img.save(stream, format="PNG")
  encoded_img = base64.b64encode(stream.getvalue()).decode("utf-8")
  return encoded_img


class MfaDisableForm(forms.Form):
  confirm_message = 'I want to make my account less secure'

  disable_mfa = forms.CharField(
    label='Confirm Text',
    initial='',
    required=True,
    widget=forms.TextInput(attrs={'size': len(confirm_message)}))

  password = forms.CharField(
    label=_("Password"),
    strip=False,
    widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
  )

  error_messages = {
    'invalid_password':
      _('The password you entered is incorrect.')
  }

  def __init__(self, user=None, *args, **kwargs):
    super(forms.Form, self).__init__(*args, **kwargs)
    self.user = user

  def clean(self):
    if self.user.check_password(self.cleaned_data.get('password')) != True:
      raise self.get_invalid_password_error()

    if self.cleaned_data.get('disable_mfa') != self.confirm_message:
      raise ValidationError('Please type the confirmation text.', code='confirm')

  def get_invalid_password_error(self):
    return ValidationError(
      self.error_messages['invalid_password'],
      code='invalid_password',
    )
