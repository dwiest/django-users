from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import ActivationId
from .mfa.models import MfaModel

class ActivationIdInline(admin.StackedInline):
  model = ActivationId
  can_delete = False
  verbose_name_plural = 'activationid'

class MfaInline(admin.StackedInline):
  model = MfaModel
  can_delete = False
  verbose_name_plural = 'multi-factor authentication'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
  inlines = (ActivationIdInline,MfaInline)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
