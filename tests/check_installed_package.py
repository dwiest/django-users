"""Run with python -I against an installed distribution, without tag stubs."""
from pathlib import Path
import sys

from django.conf import settings

settings.configure(
    SECRET_KEY="package-smoke-test",
    INSTALLED_APPS=[
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "dwiest.django.users",
    ],
    TEMPLATES=[{
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    }],
    USE_I18N=False,
)

import django
django.setup()

from django.template import Context, engines
import dwiest.django.users

package = Path(dwiest.django.users.__file__).resolve()
checkout = Path(__file__).resolve().parents[1]
assert checkout not in package.parents, f"Imported checkout instead of wheel: {package}"
engine = engines["django"].engine
assert "dwiest_django_users.tags" in engine.template_libraries
for name in [
    "registration/login.html",
    "password_change/password_change.html",
    "mfa/index.html",
    "mfa/enable.html",
]:
    engine.get_template("dwiest-django-users/" + name)
html = engine.from_string(
    "{% load dwiest_django_users.tags %}{% footer %}"
).render(Context({"user": {"is_anonymous": True}}))
assert "Your IP address is:" in html
print(f"Passed real tag discovery, account template compilation and footer rendering on Django {django.get_version()}: {package}")
