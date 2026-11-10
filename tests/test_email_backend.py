import io
import smtplib
import socket
import ssl
import unittest
from unittest.mock import Mock, patch

from django.conf import settings
if not settings.configured:
    settings.configure(SECRET_KEY='email-backend-tests',
                       EMAIL_BACKEND='dwiest.django.users.email_backend.EmailBackend',
                       EMAIL_HOST='smtp.gmail.com', EMAIL_PORT=465,
                       EMAIL_USE_SSL=True, EMAIL_USE_TLS=False, EMAIL_TIMEOUT=15,
                       EMAIL_HOST_USER='', EMAIL_HOST_PASSWORD='',
                       DEFAULT_FROM_EMAIL='sender@example.com',
                       PROXY_SERVER='dante', PROXY_PORT=1080)

from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from django.test import override_settings
from dwiest.django.users.email_backend import EmailBackend, SOCKSSMTP, SOCKSSMTPSSL


class EmailBackendTests(unittest.TestCase):
    def fake_socket(self, replies=b'220 ready\r\n'):
        sock = Mock()
        sock.makefile.return_value = io.BytesIO(replies)
        return sock

    @patch('dwiest.django.users.email_backend.socks.create_connection')
    @patch('dwiest.django.users.email_backend.ssl.create_default_context')
    def test_ssl_send_mail_routes_via_proxy_without_global_socket_changes(self, context, connect):
        original_socket = socket.socket
        sock = self.fake_socket(b'220 ready\r\n250 ready\r\n250 ok\r\n250 ok\r\n354 data\r\n250 queued\r\n221 bye\r\n')
        connect.return_value = sock
        context.return_value.wrap_socket.return_value = sock
        self.assertEqual(send_mail('Test', 'Hello Wurm', 'sender@example.com', ['buyer@example.com']), 1)
        options = connect.call_args[1]
        self.assertEqual(connect.call_args[0][0], ('smtp.gmail.com', 465))
        self.assertEqual(options['proxy_addr'], 'dante')
        self.assertEqual(options['proxy_port'], 1080)
        self.assertTrue(options['proxy_rdns'])
        self.assertEqual(options['timeout'], 15)
        context.return_value.wrap_socket.assert_called_once_with(sock, server_hostname='smtp.gmail.com')
        self.assertIs(socket.socket, original_socket)
        self.assertTrue(any(b'Hello Wurm' in call[0][0] for call in sock.sendall.call_args_list))

    def test_verified_default_context(self):
        client = SOCKSSMTPSSL(proxy_options={})
        self.assertTrue(client.tls_context.check_hostname)
        self.assertEqual(client.tls_context.verify_mode, ssl.CERT_REQUIRED)

    @override_settings(EMAIL_USE_SSL=False, EMAIL_USE_TLS=True, EMAIL_PORT=587)
    @patch('smtplib.SMTP.starttls')
    def test_starttls_uses_verified_context(self, starttls):
        backend = EmailBackend()
        client = backend.connection_class()
        self.assertIsInstance(client, SOCKSSMTP)
        self.assertNotIsInstance(client, SOCKSSMTPSSL)
        client.starttls()
        context = starttls.call_args[1]['context']
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    @patch('dwiest.django.users.email_backend.socks.create_connection')
    def test_failed_tls_handshake_closes_socket(self, connect):
        sock = self.fake_socket()
        connect.return_value = sock
        context = Mock()
        context.wrap_socket.side_effect = ssl.SSLError('bad certificate')
        with self.assertRaises(ssl.SSLError):
            SOCKSSMTPSSL('smtp.gmail.com', 465, proxy_options={}, context=context)
        sock.close.assert_called_once()

    @override_settings(PROXY_SERVER='')
    def test_missing_proxy_fails_closed(self):
        with self.assertRaises(ImproperlyConfigured):
            EmailBackend()

    @override_settings(PROXY_PORT=70000)
    def test_invalid_proxy_port(self):
        with self.assertRaises(ImproperlyConfigured):
            EmailBackend()

    @override_settings(EMAIL_USE_SSL=False, EMAIL_USE_TLS=False)
    def test_unencrypted_config_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            EmailBackend()

    @override_settings(EMAIL_TIMEOUT=None)
    def test_timeout_defaults_to_fifteen_seconds(self):
        self.assertEqual(EmailBackend().timeout, 15)

    @patch('dwiest.django.users.email_backend.socks.create_connection', side_effect=OSError('proxy down'))
    def test_connection_error_propagates(self, connect):
        with self.assertRaises(OSError):
            send_mail('Test', 'Body', 'sender@example.com', ['buyer@example.com'])

    @patch('dwiest.django.users.email_backend.socks.create_connection', side_effect=OSError('proxy down'))
    def test_fail_silently_returns_zero(self, connect):
        self.assertEqual(send_mail('Test', 'Body', 'sender@example.com', ['buyer@example.com'], fail_silently=True), 0)


if __name__ == '__main__':
    unittest.main()
