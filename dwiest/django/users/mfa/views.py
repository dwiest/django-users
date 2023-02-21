from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView, TemplateView
from django.views.generic.base import TemplateResponseMixin
from .forms import MfaEnableForm, MfaDisableForm
from .models import MfaModel
from .signals import mfa_disabled, mfa_enabled

def check_user_mfa(sender, user, request, **kwargs):
  print("checking if MFA is enabled for the user")
  try:
    mfa_record = MfaModel.objects.get(user_id=request.user.id)
    if mfa_record:
       print("MFA enabled")
       request.session['user_has_mfa'] = True
  except ObjectDoesNotExist:
    print("MFA not enabled")

user_logged_in.connect(check_user_mfa)

status_page = 'mfa_status'

class MfaStatusView(FormView, TemplateResponseMixin):
  page_name = 'Multi-Factor Authentication'
  template_name = 'dwiest-django-users/mfa/index.html'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    if request.session.get('user_has_mfa'):
      print("MFA enabled")
      self.response_dict['user_has_mfa'] = True
    return render(request, self.template_name, self.response_dict)

class MfaEnableView(FormView, TemplateResponseMixin):
  form_class = MfaEnableForm
  page_name = 'Enable Multi-Factor Authentication'
  template_name = 'dwiest-django-users/mfa/enable.html'
  success_page = 'mfa_enable_success'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    try:
      mfa_record = MfaModel.objects.get(user_id=request.user.id)
      if mfa_record:
        print("MFA already enabled")
      return HttpResponseRedirect(reverse(status_page))
    except ObjectDoesNotExist:
      print("MFA not enabled")

    form = self.form_class()
    self.response_dict['form'] = form
    return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    try:
      mfa_record = MfaModel.objects.get(user_id=request.user.id)
      if mfa_record:
        print("MFA already enabled")
      return HttpResponseRedirect(reverse(status_page))
    except ObjectDoesNotExist:
      print("MFA not enabled")

    form = self.form_class(user=request.user, data=request.POST)
    self.response_dict['form'] = form
    if form.is_valid():
      request.session['mfa_enabled'] = True
      request.session['user_has_mfa'] = True
      # create and store an MFA model object
      secret_key = form.cleaned_data['secret_key']
      user_id = request.user.id
      mfa_record = MfaModel(secret_key=secret_key, user_id=user_id)
      mfa_record.save()
      mfa_enabled.send(sender=request.user.__class__, request=request)
      return HttpResponseRedirect(reverse(self.success_page))
    else:
      return render(request, self.template_name, self.response_dict)

class MfaEnableSuccessView(TemplateView):
  page_name = 'Multi-Factor Authentication Enabled'
  template_name = 'dwiest-django-users/mfa/enable_success.html'

  def get(self, request, *args, **kwargs):
    if 'mfa_enabled' in request.session:
      request.session.pop('mfa_enabled')
      return render(request, self.template_name)
    else:
      return HttpResponseRedirect(reverse(status_page))

class MfaDisableView(FormView, TemplateResponseMixin):
  form_class = MfaDisableForm
  page_name = 'Disable Multi-Factor Authentication'
  template_name = 'dwiest-django-users/mfa/disable.html'
  success_page = 'mfa_disable_success'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

    return super(FormView, self).__init__(*args, **kwargs)

  def get(self, request, *args, **kwargs):
    try:
      mfa_record = MfaModel.objects.get(user_id=request.user.id)
    except ObjectDoesNotExist:
      print("MFA not enabled")
      return HttpResponseRedirect(reverse(status_page))

    form = self.form_class()
    self.response_dict['form'] = form
    return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    try:
      mfa_record = MfaModel.objects.get(user_id=request.user.id)
    except ObjectDoesNotExist:
      print("MFA is not enabled")
      return HttpResponseRedirect(reverse(status_page))

    form = self.form_class(user=request.user, data=request.POST)
    self.response_dict['form'] = form
    if form.is_valid():
      print("Deleting MFA record")
      mfa_record.delete()
      request.session['mfa_disabled'] = True
      request.session['user_has_mfa'] = False
      mfa_disabled.send(sender=request.user.__class__, request=request)
      return HttpResponseRedirect(reverse(self.success_page))
    else:
      return render(request, self.template_name, self.response_dict)

class MfaDisableSuccessView(TemplateView):
  page_name = 'Multi-Factor Authentication Disabled'
  template_name = 'dwiest-django-users/mfa/disable_success.html'

  def get(self, request, *args, **kwargs):
    if 'mfa_disabled' in request.session:
      request.session.pop('mfa_disabled')
      return render(request, self.template_name)
    else:
      return HttpResponseRedirect(reverse(status_page))
