from django.contrib.auth import views
from dwiest.django.users import views as myViews
from .forms import AuthenticationForm
from dwiest.django.users.forms import PasswordChangeForm

class LoginView(views.LoginView):
  form_class = AuthenticationForm

class PasswordChangeView(myViews.PasswordChangeView):
  form_class = PasswordChangeForm
