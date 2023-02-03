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
  html_body = html_template.render()
  text_body = text_template.render()
  msg = MIMEMultipart('alternative')
  msg['Subject'] = subject
  msg['From'] = sender
  msg['To'] = ', '.join(recipients)
  part1 = MIMEText(text_body, 'plain')
  part2 = MIMEText(html_body, 'html')
  msg.attach(part1)
  msg.attach(part2)
  return msg

def generate_mfa_enabled_email(recipients):
  subject = settings.USERS_MFA_ENABLED_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  html_template = get_template(settings.USERS_MFA_ENABLED_EMAIL_HTML)
  text_template = get_template(settings.USERS_MFA_ENABLED_EMAIL_TEXT)
  html_body = html_template.render()
  text_body = text_template.render()
  msg = MIMEMultipart('alternative')
  msg['Subject'] = subject
  msg['From'] = sender
  msg['To'] = ', '.join(recipients)
  part1 = MIMEText(text_body, 'plain')
  part2 = MIMEText(html_body, 'html')
  msg.attach(part1)
  msg.attach(part2)
  return msg
