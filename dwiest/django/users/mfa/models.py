from django.contrib.auth.models import User
from django.db import models
from ..conf import settings

class MfaModel(models.Model):
  user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    )

  secret_key = models.CharField(
    max_length=settings.USERS_MFA_SECRET_KEY_LENGTH,
    )

  last_value = models.CharField(
    max_length=settings.USERS_MFA_TOKEN_LENGTH,
    null=True,
    blank=True
    )
