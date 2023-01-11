from celery.app.base import Celery
import email

app = Celery(broker='amqp://')

@app.task
def generate_registration_email(recipients, activation_id):
  email.generate_registration_email(recipients, activation_id)

@app.task
def generate_account_activation_email(recipients):
  email.generate_account_activation_email(recipients)

@app.task
def generate_password_reset_email(recipients, activation_id):
  email.generate_password_reset_email(recipients, activation_id)

@app.task
def generate_password_change_email(recipients):
  email.generate_password_change_email(recipients)

@app.task
def send_email(sender, recipients, message, smtp_server, smtp_server_port=465, smtp_server_login=None, smtp_server_password=None, proxy_server=None, proxy_port=None):
  email.send_email(sender, recipients, message, smtp_server, smtp_server_port=smtp_server_port, smtp_server_login=smtp_server_login, smtp_server_password=smtp_server_password, proxy_server=proxy_server, proxy_port=proxy_port)
