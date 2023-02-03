from django.dispatch import Signal
from .email import *

user_registration = Signal()
user_registration_confirmed = Signal()
resend_registration_email = Signal()
password_reset_request = Signal()
password_changed = Signal()

@receiver(user_registration)
def user_registration_callback(sender, **kwargs):
  print("user_registration_callback")
  if getattr(settings, 'EMAIL_SEND', False) == True:
    request = kwargs['request']
    domain = 'https://' + request.META['HTTP_HOST']
    recipients = [kwargs['email']]
    activation_id = kwargs['activation_id']
    msg = generate_registration_email(recipients, domain, activation_id.value)
    send_email(recipients, msg.as_string())

@receiver(user_registration_confirmed)
def user_registration_confirmed_callback(sender, **kwargs):
  print("user_registration_confirmed_callback")
  if getattr(settings, 'EMAIL_SEND', False) == True:
    recipients = [kwargs['email']]
    msg = generate_account_activation_email(recipients)
    send_email(recipients, msg.as_string())

@receiver(resend_registration_email)
def resend_registration_email_callback(sender, **kwargs):
  print("resend_registration_email_callback")
  if getattr(settings, 'EMAIL_SEND', False) == True:
    request = kwargs['request']
    domain = 'https://' + request.META['HTTP_HOST']
    recipients = [kwargs['email']]
    activation_id = kwargs['activation_id']
    msg = generate_registration_email(recipients, domain, activation_id.value)
    send_email(recipients, msg.as_string())

@receiver(password_reset_request)
def password_reset_callback(sender, **kwargs):
  print("password_reset_callback")
  if getattr(settings, 'EMAIL_SEND', False) == True:
    request = kwargs['request']
    domain = 'https://' + request.META['HTTP_HOST']
    recipients = [kwargs['email']]
    activation_id = kwargs['activation_id']
    msg = generate_password_reset_email(recipients, domain, activation_id.value)
    send_email(recipients, msg.as_string())

@receiver(password_changed)
def password_changed_callback(sender, **kwargs):
  print("password_changed_callback")
  if getattr(settings, 'EMAIL_SEND', False) == True:
    recipients = [kwargs['email']]
    msg = generate_password_changed_email(recipients)
    send_email(recipients, msg.as_string())
