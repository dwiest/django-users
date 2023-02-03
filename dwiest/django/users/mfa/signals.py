from django.dispatch import Signal
from ..email import *

mfa_enabled = Signal()
mfa_disabled = Signal()

@receiver(mfa_disabled)
def mfa_disabled_callback(sender, **kwargs):
  recipients = [kwargs['request'].user.email]
  msg = generate_mfa_disabled_email(recipients)
  send_email(recipients, msg.as_string())

@receiver(mfa_enabled)
def mfa_enabled_callback(sender, **kwargs):
  recipients = [kwargs['request'].user.email]
  msg = generate_mfa_enabled_email(recipients)
  send_email(recipients, msg.as_string())
