from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import ActivationId

class ActivationIdInline(admin.StackedInline):
  model = ActivationId
  can_delete = False
  verbose_name_plural = 'activationid'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
  inlines = (ActivationIdInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
