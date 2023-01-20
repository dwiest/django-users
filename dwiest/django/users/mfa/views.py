from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.template.context import RequestContext
from django.views.generic import FormView
from django.views.generic.base import TemplateResponseMixin
from .forms import MfaEnableForm, MfaDisableForm

class MfaEnableView(FormView, TemplateResponseMixin):
  form_class = MfaEnableForm
  page_name = 'Enable Multi-Factor Authentication'
  template_name = 'mfa/enable.html'
  success_url = 'mfa/enable_success.html'
  success_page = 'mfa_enable_success'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

  def get(self, request, *args, **kwargs):
    form = self.form_class()
    self.response_dict['form'] = form
    return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    form = self.form_class(data=request.POST)
    self.response_dict['form'] = form
    if form.is_valid():
      #return render(request, self.success_url, self.response_dict)
      return HttpResponseRedirect(reverse(self.success_page))
    else:
      return render(request, self.template_name, self.response_dict)


class MfaDisableView(FormView, TemplateResponseMixin):
  form_class = MfaDisableForm
  page_name = 'Disable Multi-Factor Authentication'
  template_name = 'mfa/disable.html'
  success_url = 'mfa/disable_success.html'

  def __init__(self, *args, **kwargs):
    self.response_dict = {
      'page_name': self.page_name,
    }

    return super(FormView, self).__init__(*args, **kwargs)

  def get(self, request, *args, **kwargs):
    form = self.form_class()
    self.response_dict['form'] = form
    return render(request, self.template_name, self.response_dict)

  def post(self, request, *args, **kwargs):
    form = self.form_class(data=request.POST)
    self.response_dict['form'] = form
    if form.is_valid():
      return render(request, self.template_name, self.response_dict)
    else:
      return render(request, self.template_name, self.response_dict)
