# django-users
Django app to register, login/logout and manage user accounts


## SMTP through a SOCKS5 proxy

Install the revision containing `dwiest.django.users.email_backend.EmailBackend`.
`PySocks>=1.7.1` is now a package dependency. If installing the wheel with
`--no-deps`, install PySocks separately in the same virtual environment:

```sh
python -m pip install 'PySocks>=1.7.1'
```

Configure the host project's settings (Gmail example):

```python
import os

EMAIL_BACKEND = 'dwiest.django.users.email_backend.EmailBackend'
PROXY_SERVER = 'dante'
PROXY_PORT = 1080
# Optional SOCKS authentication, only if your proxy requires it:
# PROXY_USERNAME = os.environ['SMTP_PROXY_USERNAME']
# PROXY_PASSWORD = os.environ['SMTP_PROXY_PASSWORD']

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
EMAIL_TIMEOUT = 15
EMAIL_HOST_USER = 'your-google-email-address'
EMAIL_HOST_PASSWORD = os.environ['GMAIL_APP_PASSWORD']
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
```

Supply credentials to the Django service outside source control. Use a Google
app password supported by the account, or your provider's SMTP credentials.
The sender should be the authenticated mailbox or a permitted sender alias.
Restart Django after installing the package and changing settings. No database
migration is needed. Keep the SMTP hostname: the SOCKS5 proxy resolves it, while
TLS verifies that same hostname. Permit the destination SMTP port in Dante and
its network egress. The app must be able to resolve/reach the proxy itself.
`https_proxy` and Squid settings are independent of this SMTP transport.

For STARTTLS instead, set `EMAIL_PORT = 587`, `EMAIL_USE_TLS = True`, and
`EMAIL_USE_SSL = False`. The backend requires TLS and an explicit proxy; it does
not fall back to a direct connection if proxy configuration is missing. Timeout
defaults to 15 seconds when Django's `EMAIL_TIMEOUT` is None. Certificate and
hostname checks are enabled for both TLS modes. No process-wide sockets are
patched by this backend.

Test from a Django shell in the application's service-equivalent environment:

```python
from django.conf import settings
from django.core.mail import send_mail

send_mail('Store email test', 'SMTP through Dante works.',
          settings.DEFAULT_FROM_EMAIL, ['your-test-address@example.com'],
          fail_silently=False)
```

A result of 1 means the SMTP server accepted the email, not guaranteed inbox
delivery. Store notifications using Django's `send_mail` automatically use this
backend; existing failed order events can be retried from store management.
The older `users.email.send_email` helper is unchanged and still has its own
proxy handling; this backend applies to Django's standard email API.

Run the isolated backend tests with Django and PySocks installed:

```sh
python -m unittest discover -s tests -v
```

Tests cover routing, proxy-side DNS, TLS identity/verification, message sending,
timeouts, validation and failure handling with mocked network connections.
Live Dante access and SMTP authentication must be checked in the host environment.
