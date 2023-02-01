from django.conf import settings
from django.shortcuts import render
from django.template.loader import get_template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def generate_registration_email(recipients, activation_id):
  subject = settings.REGISTRATION_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  link = "https://wiest.world/django/registration/confirm?activation_id={}".format(activation_id)
  html_template = get_template(settings.REGISTRATION_EMAIL_HTML)
  text_template = get_template(settings.REGISTRATION_EMAIL_TEXT)
  html_body = html_template.render({'link':link})
  text_body = text_template.render({'link':link})
  msg = MIMEMultipart('alternative')
  msg['Subject'] = subject
  msg['From'] = sender
  msg['To'] = ', '.join(recipients)
  part1 = MIMEText(text_body, 'plain')
  part2 = MIMEText(html_body, 'html')
  msg.attach(part1)
  msg.attach(part2)
  return msg

def generate_account_activation_email(recipients):
  subject = settings.ACCOUNT_ACTIVATION_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  html_template = get_template(settings.ACCOUNT_ACTIVATION_EMAIL_HTML)
  text_template = get_template(settings.ACCOUNT_ACTIVATION_EMAIL_TEXT)
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

def generate_password_reset_email(recipients, activation_id):
  subject = settings.PASSWORD_RESET_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  link = "https://wiest.world/django/password/reset/confirm?activation_id={}".format(activation_id)
  html_template = get_template(settings.PASSWORD_RESET_EMAIL_HTML)
  text_template = get_template(settings.PASSWORD_RESET_EMAIL_TEXT)
  html_body = html_template.render({'link':link})
  text_body = text_template.render({'link':link})
  msg = MIMEMultipart('alternative')
  msg['Subject'] = subject
  msg['From'] = sender
  msg['To'] = ', '.join(recipients)
  part1 = MIMEText(text_body, 'plain')
  part2 = MIMEText(html_body, 'html')
  msg.attach(part1)
  msg.attach(part2)
  return msg

def generate_password_change_email(recipients):
  subject = settings.PASSWORD_CHANGE_EMAIL_SUBJECT
  sender = settings.DEFAULT_FROM_EMAIL
  html_template = get_template(settings.PASSWORD_CHANGE_EMAIL_HTML)
  text_template = get_template(settings.PASSWORD_CHANGE_EMAIL_TEXT)
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

def send_email(sender, recipients, message, smtp_server, smtp_server_port=465, smtp_server_login=None, smtp_server_password=None, proxy_server=None, proxy_port=None):
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
