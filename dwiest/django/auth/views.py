from django.contrib.auth import views
from ..users import views as myViews
from .forms import AuthenticationForm
from ..users.conf import settings
from ..users.forms import PasswordChangeForm

class LoginView(views.LoginView):
  form_class = AuthenticationForm
  template_name = settings.USERS_LOGIN_TEMPLATE

class PasswordChangeView(myViews.PasswordChangeView):
  form_class = PasswordChangeForm
