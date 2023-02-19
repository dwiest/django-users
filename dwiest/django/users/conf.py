from django.conf import settings
from appconf import AppConf

class UsersAppConf(AppConf):

  def ready(self):
    from .mfa import signals
    from . import signals

  '''
    Email settings
  '''

  EMAIL_FIELD_MAX_LENGTH = 50

  ''' Account activation '''
  ACCOUNT_ACTIVATION_EMAIL_SUBJECT = 'Account Activated'
  ACCOUNT_ACTIVATION_EMAIL_HTML = 'dwiest-django-users/email/account_activation.html'
  ACCOUNT_ACTIVATION_EMAIL_TEXT = 'dwiest-django-users/email/account_activation.txt'

  ''' Password change '''
  PASSWORD_CHANGE_EMAIL_SUBJECT = 'Password Updated'
  PASSWORD_CHANGE_EMAIL_HTML = 'dwiest-django-users/email/password_updated.html'
  PASSWORD_CHANGE_EMAIL_TEXT = 'dwiest-django-users/email/password_updated.txt'

  ''' Password reset '''
  PASSWORD_RESET_EMAIL_SUBJECT = 'Password Reset'
  PASSWORD_RESET_EMAIL_HTML = 'dwiest-django-users/email/password_reset.html'
  PASSWORD_RESET_EMAIL_TEXT = 'dwiest-django-users/email/password_reset.txt'

  ''' Account registration '''
  REGISTRATION_EMAIL_SUBJECT = 'User Registration'
  REGISTRATION_EMAIL_HTML = 'dwiest-django-users/email/registration_email.html'
  REGISTRATION_EMAIL_TEXT = 'dwiest-django-users/email/registration_email.txt'

  ''' MFA disabled/enabled '''
  MFA_DISABLED_EMAIL_SUBJECT = 'Multi-Factor Authentication Disabled'
  MFA_DISABLED_EMAIL_HTML = 'dwiest-django-users/email/mfa_disabled.html'
  MFA_DISABLED_EMAIL_TEXT = 'dwiest-django-users/email/mfa_disabled.txt'

  MFA_ENABLED_EMAIL_SUBJECT = 'Multi-Factor Authentication Enabled'
  MFA_ENABLED_EMAIL_HTML = 'dwiest-django-users/email/mfa_enabled.html'
  MFA_ENABLED_EMAIL_TEXT = 'dwiest-django-users/email/mfa_enabled.txt'

  '''
    Activation id settings:

      ACTIVATION_ID_ALLOW_EXPIRED - Allow activation ids that have
        expired.  Intended for debug/test purposes.

      ACTIVATION_ID_DO_NOT_DELETE - Don't delete the activation id 
        record after use.  Intended for debug/test purposes.
  '''

  ACTIVATION_ID_ALLOW_EXPIRED = False
  ACTIVATION_ID_DO_NOT_DELETE = False

  '''
    Account registration settings:

      REGISTRATION_ALLOW_EMAIL_RESEND - Allow users to re-request their
        registration email.

      REGISTRATION_ALLOW_ALREADY_ACTIVE - Allow active users to
        re-register for an account.  Intended for debug/test purposes.
  '''

  REGISTRATION_ALLOW_EMAIL_RESEND = False
  REGISTRATION_ALLOW_ALREADY_ACTIVE = False
  REGISTRATION_EMAIL_FIELD_CLASS = 'email'
  REGISTRATION_EXPIRATION_DAYS = 1
  REGISTRATION_TEMPLATE = 'dwiest-django-users/registration/registration.html'
  REGISTRATION_SUCCESS_TEMPLATE = 'dwiest-django-users/registration/registration_success.html'
  REGISTRATION_FAILED_TEMPLATE = 'dwiest-django-users/registration/registration_failed.html'
  REGISTRATION_CONFIRM_SUCCESS_TEMPLATE = 'dwiest-django-users/registration/registration_confirm_success.html'
  REGISTRATION_CONFIRM_FAILED_TEMPLATE = 'dwiest-django-users/registration/registration_confirm_failed.html'
  REGISTRATION_USER_ALREADY_ACTIVATED_ERROR = 'That account has already been activated.'
  REGISTRATION_USER_ALREADY_EXISTS_ERROR = 'That account has already been activated.'
  REGISTRATION_USER_INVALID_ERROR = 'Your account could not be located.'
  REGISTRATION_ACTIVATION_ID_EXPIRED_ERROR = 'Your account registration link has expired.'
  REGISTRATION_ACTIVATION_ID_INVALID_ERROR = 'The activation id is invalid.'
  REGISTRATION_RESEND_NOT_ALLOWED_ERROR = 'Re-sending of registration emails is not allowed.'

  '''
    Login settings
  '''

  LOGIN_TEMPLATE = 'dwiest-django-users/registration/login.html'
  LOGIN_MFA_FIELD_LABEL = 'MFA token'
  LOGIN_INVALID_MFA_TOKEN_ERROR = 'The MFA token you entered is not correct.'
  LOGIN_REPLAYED_MFA_TOKEN_ERROR = 'The MFA token you entered has already been used. Please wait and enter the next value shown in your authenticator app.'

  '''
  MFA settings:

    MFA_ACCEPT_ANY_VALUE - Accept any provided value as valid.  Intended 
      for debug/test purposes.

    MFA_ISSUER_NAME - The issuer name to use when creating the 
      provisioning URI.

    MFA_SECRET_KEY - Allows the secret key to be specified instead of 
      using a randomly generated value.  Intended for debug/test 
      purposes.
  '''

  MFA_SECRET_KEY = None
  MFA_ISSUER_NAME = None
  MFA_ACCEPT_ANY_VALUE = False
  MFA_FIELD_CLASS = 'mfa'
  MFA_FIELD_MAX_LENGTH = 6
  MFA_FIELD_MIN_LENGTH = 6

  '''
    Password reset settings
  '''

  PASSWORD_RESET_EXPIRATION_DAYS = 1
  PASSWORD_RESET_EMAIL_FIELD_CLASS = 'email'
  PASSWORD_RESET_TEMPLATE = 'dwiest-django-users/password_reset/send_password_reset.html'
  PASSWORD_RESET_SUCCESS_TEMPLATE = 'dwiest-django-users/password_reset/send_password_reset_success.html'
  PASSWORD_RESET_FAILED_TEMPLATE = 'dwiest-django-users/password_reset/password_reset_failed.html'
  PASSWORD_RESET_CONFIM_TEMPLATE = 'dwiest-django-users/password_reset/password_reset_confirm.html'
  PASSWORD_RESET_CONFIRM_SUCCESS_TEMPLATE = 'dwiest-django-users/password_reset/password_reset_confirm_success.html'
  PASSWORD_RESET_ACTIVATION_ID_LABEL = 'Activation Id'
  PASSWORD_RESET_USER_NOT_FOUND_ERROR = 'A user with that email address could not be located.'
  PASSWORD_RESET_MFA_TOKEN_LABEL = 'MFA Token'
  PASSWORD_RESET_NEW_PASSWORD1_LABEL = 'New Password'
  PASSWORD_RESET_NEW_PASSWORD2_LABEL = 'Confirm Password'
  PASSWORD_RESET_PASSWORD_MISMATCH_ERROR = "The two password fields didn't match."
  PASSWORD_RESET_INVALID_MFA_TOKEN_ERROR = 'The MFA token you entered is not correct.'
  PASSWORD_RESET_REPLAYED_MFA_TOKEN_ERROR = 'The MFA token you entered has already been used.  Please wait and enter the next value shown in your authenticator app.'
  PASSWORD_RESET_ACTIVATION_ID_EXPIRED_ERROR = 'The activation id has expired.  Please request a new pasword reset email.'
  PASSWORD_RESET_ACTIVATION_ID_INVALID_ERROR = 'The activation id is invalid.'

  '''
    Password change settings
  '''

  PASSWORD_CHANGE_TEMPLATE = 'dwiest-django-users/password_change/password_change.html'
  PASSWORD_CHANGE_SUCCESS_TEMPLATE = 'dwiest-django-users/password_change/password_change_success.html'
  PASSWORD_CHANGE_MFA_TOKEN_FIELD_LABEL = 'MFA Token'
  PASSWORD_CHANGE_OLD_PASSWORD_FIELD_LABEL = 'Password'
  PASSWORD_CHANGE_PASSWORD1_FIELD_LABEL = 'New Password'
  PASSWORD_CHANGE_PASSWORD2_FIELD_LABEL = 'Confirm Password'
  PASSWORD_CHANGE_PASSWORD_MISMATCH_ERROR = "The two password fields didn't match."
  PASSWORD_CHANGE_INVALID_USER_ERROR = 'Your password could not be updated.'
  PASSWORD_CHANGE_INVALID_MFA_TOKEN_ERROR = 'The MFA token you entered is not correct.'
  PASSWORD_CHANGE_REPLAYED_MFA_TOKEN_ERROR = 'The MFA token you entered has already been used.  Please wait and enter the next value shown in your authenticator app.'
