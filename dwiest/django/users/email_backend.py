"""SMTP over SOCKS5, without changing process-wide socket behavior."""
import smtplib
import socket
import ssl
from functools import partial

import socks
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


def verified_context(certfile=None, keyfile=None):
    context = ssl.create_default_context()
    if certfile:
        context.load_cert_chain(certfile, keyfile)
    return context


class SOCKSSMTP(smtplib.SMTP):
    def __init__(self, *args, **kwargs):
        self.proxy_options = kwargs.pop('proxy_options')
        super().__init__(*args, **kwargs)

    def _get_socket(self, host, port, timeout):
        if timeout is socket._GLOBAL_DEFAULT_TIMEOUT:
            timeout = socket.getdefaulttimeout()
        return socks.create_connection((host, port), timeout=timeout,
                                       source_address=self.source_address,
                                       **self.proxy_options)

    def starttls(self, keyfile=None, certfile=None, context=None):
        # Django 3.2 passes legacy keyfile/certfile arguments. Always verify TLS.
        context = context or verified_context(certfile, keyfile)
        return super().starttls(context=context)


class SOCKSSMTPSSL(SOCKSSMTP):
    def __init__(self, *args, **kwargs):
        context = kwargs.pop('context', None)
        certfile = kwargs.pop('certfile', None)
        keyfile = kwargs.pop('keyfile', None)
        self.tls_context = context or verified_context(certfile, keyfile)
        super().__init__(*args, **kwargs)

    def _get_socket(self, host, port, timeout):
        connection = super()._get_socket(host, port, timeout)
        try:
            return self.tls_context.wrap_socket(connection, server_hostname=host)
        except Exception:
            connection.close()
            raise


class EmailBackend(SMTPBackend):
    """Select with EMAIL_BACKEND='dwiest.django.users.email_backend.EmailBackend'."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy_server = getattr(settings, 'PROXY_SERVER', None)
        if not self.proxy_server:
            raise ImproperlyConfigured('The SOCKS email backend requires PROXY_SERVER.')
        try:
            self.proxy_port = int(getattr(settings, 'PROXY_PORT', 1080))
            if not 1 <= self.proxy_port <= 65535:
                raise ValueError
        except (ValueError, TypeError):
            raise ImproperlyConfigured('PROXY_PORT must be a port from 1 to 65535.')
        if not (self.use_ssl or self.use_tls):
            raise ImproperlyConfigured('Enable EMAIL_USE_SSL or EMAIL_USE_TLS for SOCKS email.')
        if self.timeout is None:
            self.timeout = 15

    @property
    def connection_class(self):
        return partial(SOCKSSMTPSSL if self.use_ssl else SOCKSSMTP,
                       proxy_options={
                           'proxy_type': socks.SOCKS5,
                           'proxy_addr': self.proxy_server,
                           'proxy_port': self.proxy_port,
                           'proxy_rdns': True,
                           'proxy_username': getattr(settings, 'PROXY_USERNAME', None),
                           'proxy_password': getattr(settings, 'PROXY_PASSWORD', None),
                       })

    def open(self):
        try:
            result = super().open()
            if result is None and self.connection is not None:
                self.connection.close()
                self.connection = None
            return result
        except Exception:
            # A failed TLS handshake/login must not leave a connection reusable.
            if self.connection is not None:
                self.connection.close()
                self.connection = None
            raise
