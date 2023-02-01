from django.conf import settings
from appconf import AppConf

class UsersAppConf(AppConf):

  ''' Account activation email settings '''

  ACCOUNT_ACTIVATION_EMAIL_SUBJECT = 'Account Activated'
  ACCOUNT_ACTIVATION_EMAIL_HTML = 'email/account_activation.html'
  ACCOUNT_ACTIVATION_EMAIL_TEXT = 'email/account_activation.txt'

  ''' Password change email settings '''

  PASSWORD_CHANGE_EMAIL_SUBJECT = 'Password Updated'
  PASSWORD_CHANGE_EMAIL_HTML = 'email/password_updated.html'
  PASSWORD_CHANGE_EMAIL_TEXT = 'email/password_updated.txt'

  ''' Password reset email settings '''

  PASSWORD_RESET_EMAIL_SUBJECT = 'Password Reset'
  PASSWORD_RESET_EMAIL_HTML = 'email/password_reset.html'
  PASSWORD_RESET_EMAIL_TEXT = 'email/password_reset.txt'

  ''' Account registration email settings '''

  REGISTRATION_EMAIL_SUBJECT = 'User Registration'
  REGISTRATION_EMAIL_HTML = 'email/registration_email.html'
  REGISTRATION_EMAIL_TEXT = 'email/registration_email.txt'

  '''
    Activation id settings:

      ACTIVATION_ID_IGNORE_EXPIRED - Allow activation ids that have 
        expired.  Intended for debug/test purposes.

      ACTIVATION_ID_DO_NOT_DELETE - Don't delete the activation id 
        record after use.  Intended for debug/test purposes.
  '''

  ACTIVATION_ID_IGNORE_EXPIRED = False
  ACTIVATION_ID_DO_NOT_DELETE = False

  '''
    Account registration settings:

      REGISTRATION_ALLOW_EMAIL_RESEND - Allow users to re-request their
        registration email.

      REGISTRATION_IGNORE_ALREADY_ACTIVE - Allow active users to 
        re-register for an account.  Intended for debug/test purposes.
  '''

  REGISTRATION_ALLOW_EMAIL_RESEND = False
  REGISTRATION_IGNORE_ALREADY_ACTIVE = False

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