from django.contrib.auth import views
from ..users import views as myViews
from .forms import AuthenticationForm
from ..users.forms import PasswordChangeForm

class LoginView(views.LoginView):
  form_class = AuthenticationForm

class PasswordChangeView(myViews.PasswordChangeView):
  form_class = PasswordChangeForm
