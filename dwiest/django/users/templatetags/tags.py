from django.template.loader import get_template
from django import template
from ..conf import settings

register = template.Library()

'''
Display a page template footer if one is configured, otherwise don't display anything.
'''

if settings.USERS_PAGE_FOOTER:
  @register.inclusion_tag(settings.USERS_PAGE_FOOTER, takes_context=True)
  def footer(context, *args, **kwargs):
    return context
else:
  @register.simple_tag()
  def footer(*args, **kwargs):
    return ''
