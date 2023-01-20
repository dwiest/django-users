from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
import base64
from io import BytesIO
import pyotp
import qrcode

class MfaEnableForm(forms.Form):
  token = forms.CharField(
    label='Token',
    initial='',
    max_length='6',
    min_length='6',
    required=True,
    widget=forms.TextInput(attrs={'size': '6'}))

  secret_key = forms.CharField(
    initial='',
    max_length='32',
    min_length='32',
    required=True,
    widget=forms.HiddenInput())

  def __init__(self, *args, **kwargs):
    super(forms.Form, self).__init__(*args, **kwargs)
    if hasattr(settings, 'MFA_SECRET_KEY'):
      self.initial['secret_key'] = settings.MFA_SECRET_KEY
    elif kwargs.get('data'):
      self.initial['secret_key'] = kwargs['data']['secret_key']
    else:
      self.initial['secret_key'] = pyotp.random_base32()
    self.totp = pyotp.TOTP(self.initial['secret_key'])
    self.account_name = None
    if hasattr(settings, 'MFA_ISSUER_NAME'):
      self.mfa_issuer_name = settings.MFA_ISSUER_NAME
    else:
      self.mfa_issuer_name = None
    self.provisioning_uri = self.totp.provisioning_uri(
      name=self.account_name,
      issuer_name=self.mfa_issuer_name)
    self.secret_key_image = get_qrcode(self.provisioning_uri)

  def clean(self):
    super().clean()
    if hasattr(settings, 'MFA_ACCEPT_ANY_VALUE') and settings.MFA_ACCEPT_ANY_VALUE:
      print("!WARNING! MFA accepting any value")
      return True
    elif self.cleaned_data.get('token') == self.totp.now():
      return True
    else:
      raise ValidationError('Invalid token, please try again')

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
  pass
