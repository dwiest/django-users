from django.contrib.auth import views
from ..users import views as myViews
from .forms import AuthenticationForm
from ..users.forms import PasswordChangeForm
from ..users.conf import settings

class LoginView(views.LoginView):
  form_class = AuthenticationForm
  template_name = settings.USERS_LOGIN_TEMPLATE

class PasswordChangeView(myViews.PasswordChangeView):
  form_class = PasswordChangeForm
