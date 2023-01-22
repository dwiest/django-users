from django.contrib.auth.models import User
from django.db import models

class MfaModel(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  secret_key = models.CharField(max_length=32)
  last_value = models.CharField(max_length=6, null=True, blank=True)
