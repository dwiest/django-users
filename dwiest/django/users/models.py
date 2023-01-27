from django.contrib.auth.models import User
from django.db import models

class ActivationId(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  value = models.CharField(max_length=36)
  created_at = models.DateTimeField(auto_now_add=True)
