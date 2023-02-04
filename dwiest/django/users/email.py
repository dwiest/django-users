from django.dispatch import receiver
from django.shortcuts import render
from django.template.loader import get_template
from django.urls import reverse
from .conf import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def generate_registration_email(recipients, domain, activation_id):
  subject = settings.USERS_REGISTRATION_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  html_template = get_template(settings.USERS_REGISTRATION_EMAIL_HTML)
  text_template = get_template(settings.USERS_REGISTRATION_EMAIL_TEXT)

  query_string = '?activation_id={}'.format(activation_id)
  link = str(domain) + reverse('registration_confirm') + query_string
  context = {'link': link}

  return generate_email(
    sender, recipients, subject, html_template, text_template, context)

def generate_account_activation_email(recipients):
  subject = settings.USERS_ACCOUNT_ACTIVATION_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  html_template = get_template(settings.USERS_ACCOUNT_ACTIVATION_EMAIL_HTML)
  text_template = get_template(settings.USERS_ACCOUNT_ACTIVATION_EMAIL_TEXT)

  return generate_email(
    sender, recipients, subject, html_template, text_template)

def generate_password_reset_email(recipients, domain, activation_id):
  subject = settings.USERS_PASSWORD_RESET_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  html_template = get_template(settings.USERS_PASSWORD_RESET_EMAIL_HTML)
  text_template = get_template(settings.USERS_PASSWORD_RESET_EMAIL_TEXT)

  query_string = '?activation_id={}'.format(activation_id)
  link = str(domain) + reverse('password_reset_confirm') + query_string
  context = {'link': link}

  return generate_email(
    sender, recipients, subject, html_template, text_template, context)

def generate_password_changed_email(recipients):
  subject = settings.USERS_PASSWORD_CHANGE_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  html_template = get_template(settings.USERS_PASSWORD_CHANGE_EMAIL_HTML)
  text_template = get_template(settings.USERS_PASSWORD_CHANGE_EMAIL_TEXT)

  return generate_email(
    sender, recipients, subject, html_template, text_template)

def send_email(recipients, message,
  sender=settings.DEFAULT_FROM_EMAIL,
  smtp_server=settings.EMAIL_HOST,
  smtp_server_port=465,
  smtp_server_login=settings.EMAIL_HOST_USER,
  smtp_server_password=settings.EMAIL_HOST_PASSWORD,
  proxy_server=settings.PROXY_SERVER,
  proxy_port=settings.PROXY_PORT):
  if proxy_server:
    import socks
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy_server, proxy_port)
    socks.wrapmodule(smtplib)

  if settings.EMAIL_USE_SSL == True:
    server = smtplib.SMTP_SSL(smtp_server, smtp_server_port)
  else:
    server = smtplib.SMTP(smtp_server, smtp_server_port)
  server.login(smtp_server_login, smtp_server_password)
  server.sendmail(sender, recipients, message)
  server.quit()

def generate_email( sender, recipients, subject,
  html_template=None, text_template=None, context={}):

  msg = MIMEMultipart('alternative') # need to handle single part
  msg['Subject'] = subject
  msg['From'] = sender
  msg['To'] = ', '.join(recipients)

  if text_template:
    text_body = text_template.render(context)
    part = MIMEText(text_body, 'plain')
    msg.attach(part)

  if html_template:
    html_body = html_template.render(context)
    part = MIMEText(html_body, 'html')
    msg.attach(part)

  return msg
