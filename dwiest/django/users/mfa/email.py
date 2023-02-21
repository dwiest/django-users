from django.template.loader import get_template
from ..conf import settings
from ..email import generate_email

def generate_mfa_disabled_email(recipients):
  subject = settings.USERS_MFA_DISABLED_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  html_template = get_template(settings.USERS_MFA_DISABLED_EMAIL_HTML)
  text_template = get_template(settings.USERS_MFA_DISABLED_EMAIL_TEXT)

  return generate_email(
    sender, recipients, subject, html_template, text_template)

def generate_mfa_enabled_email(recipients):
  subject = settings.USERS_MFA_ENABLED_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  html_template = get_template(settings.USERS_MFA_ENABLED_EMAIL_HTML)
  text_template = get_template(settings.USERS_MFA_ENABLED_EMAIL_TEXT)

  return generate_email(
    sender, recipients, subject, html_template, text_template)
