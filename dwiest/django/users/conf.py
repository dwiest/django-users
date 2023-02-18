from django.conf import settings
from appconf import AppConf

class UsersAppConf(AppConf):

  def ready(self):
    from .mfa import signals
    from . import signals

  ''' Account activation email settings '''

  ACCOUNT_ACTIVATION_EMAIL_SUBJECT = 'Account Activated'
  ACCOUNT_ACTIVATION_EMAIL_HTML = 'dwiest-django-users/email/account_activation.html'
  ACCOUNT_ACTIVATION_EMAIL_TEXT = 'dwiest-django-users/email/account_activation.txt'

  ''' Password change email settings '''

  PASSWORD_CHANGE_EMAIL_SUBJECT = 'Password Updated'
  PASSWORD_CHANGE_EMAIL_HTML = 'dwiest-django-users/email/password_updated.html'
  PASSWORD_CHANGE_EMAIL_TEXT = 'dwiest-django-users/email/password_updated.txt'

  ''' Password reset email settings '''

  PASSWORD_RESET_EMAIL_SUBJECT = 'Password Reset'
  PASSWORD_RESET_EMAIL_HTML = 'dwiest-django-users/email/password_reset.html'
  PASSWORD_RESET_EMAIL_TEXT = 'dwiest-django-users/email/password_reset.txt'

  ''' Account registration email settings '''

  REGISTRATION_EMAIL_SUBJECT = 'User Registration'
  REGISTRATION_EMAIL_HTML = 'dwiest-django-users/email/registration_email.html'
  REGISTRATION_EMAIL_TEXT = 'dwiest-django-users/email/registration_email.txt'

  ''' MFA disabled/enabled email settings '''

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
