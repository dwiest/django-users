from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView, TemplateView
from django.views.generic.base import TemplateResponseMixin
from enum import Enum
from .forms import MfaEnableForm, MfaDisableForm
from .models import MfaModel
from .signals import mfa_disabled, mfa_enabled

def check_user_mfa(sender, user, request, **kwargs):
  try:
    mfa_record = MfaModel.objects.get(user_id=request.user.id)
    if mfa_record:
       request.session['user_has_mfa'] = True
  except ObjectDoesNotExist:
    pass

user_logged_in.connect(check_user_mfa)

status_page = 'mfa_status'


class MfaStatusView(FormView, TemplateResponseMixin):
  template_name = settings.USERS_MFA_STATUS_TEMPLATE

  def __init__(self, *args, **kwargs):
    self.response_dict = {}

  def get(self, request, *args, **kwargs):
    if request.session.get('user_has_mfa'):
      self.response_dict['user_has_mfa'] = True
    return render(request, self.template_name, self.response_dict)


class MfaEnableView(FormView, TemplateResponseMixin):

  class ResponseDict(str, Enum):
    FORM = 'form'

  form_class = MfaEnableForm
  template_name = settings.USERS_MFA_ENABLE_TEMPLATE
  success_page = 'mfa_enable_success'

  def __init__(self, *args, **kwargs):
    self.response_dict = {}

  def get(self, request, *args, **kwargs):
    try:
      mfa_record = MfaModel.objects.get(user_id=request.user.id)
      return HttpResponseRedirect(reverse(status_page))
    except ObjectDoesNotExist:
      pass

    form = self.form_class()
    self.response_dict[self.ResponseDict.FORM] = form
    return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    try:
      mfa_record = MfaModel.objects.get(user_id=request.user.id)
      return HttpResponseRedirect(reverse(status_page))
    except ObjectDoesNotExist:
      pass

    form = self.form_class(user=request.user, data=request.POST)
    self.response_dict[self.ResponseDict.FORM] = form

    if form.is_valid():
      # create and store an MFA model object
      secret_key = form.cleaned_data['secret_key']
      user_id = request.user.id
      mfa_record = MfaModel(secret_key=secret_key, user_id=user_id)
      mfa_record.save()
      request.session['mfa_enabled'] = True
      request.session['user_has_mfa'] = True
      mfa_enabled.send(sender=request.user.__class__, request=request)
      return HttpResponseRedirect(reverse(self.success_page))

    else:
      return render(request, self.template_name, self.response_dict)


class MfaEnableSuccessView(TemplateView):
  template_name = settings.USERS_MFA_ENABLE_SUCCESS_TEMPLATE

  def get(self, request, *args, **kwargs):
    if 'mfa_enabled' in request.session:
      request.session.pop('mfa_enabled')
      return render(request, self.template_name)
    else:
      return HttpResponseRedirect(reverse(status_page))


class MfaDisableView(FormView, TemplateResponseMixin):

  class ResponseDict(str, Enum):
    FORM = 'form'

  form_class = MfaDisableForm
  template_name = settings.USERS_MFA_DISABLE_TEMPLATE
  success_page = 'mfa_disable_success'

  def __init__(self, *args, **kwargs):
    self.response_dict = {}
    return super(FormView, self).__init__(*args, **kwargs)

  def get(self, request, *args, **kwargs):
    try:
      mfa_record = MfaModel.objects.get(user_id=request.user.id)
    except ObjectDoesNotExist:
      return HttpResponseRedirect(reverse(status_page))

    form = self.form_class()
    self.response_dict[self.ResponseDict.FORM] = form
    return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    try:
      mfa_record = MfaModel.objects.get(user_id=request.user.id)
    except ObjectDoesNotExist:
      return HttpResponseRedirect(reverse(status_page))

    form = self.form_class(user=request.user, data=request.POST)
    self.response_dict[self.ResponseDict.FORM] = form

    if form.is_valid():
      mfa_record.delete()
      request.session['mfa_disabled'] = True
      request.session['user_has_mfa'] = False
      mfa_disabled.send(sender=request.user.__class__, request=request)
      return HttpResponseRedirect(reverse(self.success_page))
    else:
      return render(request, self.template_name, self.response_dict)


class MfaDisableSuccessView(TemplateView):
  template_name = settings.USERS_MFA_DISABLE_SUCCESS_TEMPLATE

  def get(self, request, *args, **kwargs):
    if 'mfa_disabled' in request.session:
      request.session.pop('mfa_disabled')
      return render(request, self.template_name)
    else:
      return HttpResponseRedirect(reverse(status_page))
