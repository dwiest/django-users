from django.shortcuts import render
from django.template.loader import get_template
from ..conf import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def generate_mfa_disabled_email(recipients):
  subject = settings.USERS_MFA_DISABLED_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  html_template = get_template(settings.USERS_MFA_DISABLED_EMAIL_HTML)
  text_template = get_template(settings.USERS_MFA_DISABLED_EMAIL_TEXT)

  return _generate_email(
    sender, recipients, subject, html_template, text_template)

def generate_mfa_enabled_email(recipients):
  subject = settings.USERS_MFA_ENABLED_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  html_template = get_template(settings.USERS_MFA_ENABLED_EMAIL_HTML)
  text_template = get_template(settings.USERS_MFA_ENABLED_EMAIL_TEXT)

  return _generate_email(
    sender, recipients, subject, html_template, text_template)

def _generate_email( sender, recipients, subject,
  html_template=None, text_template=None):

  msg = MIMEMultipart('alternative') # need to handle single part
  msg['Subject'] = subject
  msg['From'] = sender
  msg['To'] = ', '.join(recipients)

  if text_template:
    text_template = get_template(settings.USERS_MFA_DISABLED_EMAIL_TEXT)
    text_body = text_template.render()
    part = MIMEText(text_body, 'plain')
    msg.attach(part)

  if html_template:
    html_template = get_template(settings.USERS_MFA_DISABLED_EMAIL_HTML)
    html_body = html_template.render()
    part = MIMEText(html_body, 'html')
    msg.attach(part)

  return msg
