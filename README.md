# Django-translate-getetxt

This is a django app that allows you to wrap django applications files fields with a translation field (not for Pycharm and docker-compose python interpretator).

It uses gettext package to achieve this and wrapping fields.

v.0.2.2 - Added support for clean models methods and ValidationError messages

v0.2.0 - Added support for admin files

v0.1.0 - Initial release with models files support


## Installation

```bash
poetry add django-translate-gettext

# or
poetry add git+https://github.com/alpden550/django-translate-gettext.git
```

## Usage

Add `django_translate` to your `INSTALLED_APPS` setting like this:

```python
INSTALLED_APPS = [
    ...,
    'django_translate_gettext',
    ...
]
```

Call django commands to create the translation fields for your apps, use `--format` flag to call ruff format tool after files changed.

Example:

```bash
python manage.py translate app1 app2 app3 app4 --format
```

[![asciicast](https://asciinema.org/a/K7TWvXujFr65D4hq0yiYRaXEV.svg)](https://asciinema.org/a/K7TWvXujFr65D4hq0yiYRaXEV)

Models files before:

`demo/models/base.py`
```python
from django.db import models


class Base(models.Model):
    created_at = models.DateTimeField("Date Created", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Date Updated", auto_now=True)
    items = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        abstract = True
```

`demo/models/user.py`
```python
import csv
from pathlib import Path
from django.db import models

from demo.models import Base


class CustomQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs).order_by("id")


class UserTypes(models.TextChoices):
    ADMIN = "admin", "Admin"
    USER = "user", "User"
    STAFF = "staff", "Staff"


class CustomUser(Base):
    class _InnerTypes(models.TextChoices):
        NEW = "new", "New"
        OLD = "old", "Old"

    username = models.CharField("User Name", max_length=100, help_text="This is the help text")
    email = models.EmailField()
    password = models.CharField(max_length=100)
    created_at = models.DateTimeField("Date Created", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Date Updated", auto_now=True)
    first_name = models.CharField(verbose_name="First_Name", max_length=25)
    last_name = models.CharField("Last_Name", max_length=25)
    is_active = models.BooleanField(default=True)
    choices = models.CharField(max_length=5, choices=UserTypes.choices, default=UserTypes.USER)
    groups = models.ManyToManyField("auth.Group", verbose_name="Custom Groups", blank=True)
    owner = models.ForeignKey("auth.User", related_name="users", on_delete=models.CASCADE, blank=True, null=True)

    objects = CustomQuerySet.as_manager()

    class Meta:
        verbose_name = "Own Custom User"
        verbose_name_plural = "Own Custom Users"
        ordering = ("-created_at",)
        get_latest_by = ("-created_at", "is_active")
```

Models files after:

`demo/models/base.py`
```python
from django.db import models
from django.utils.translation import gettext_lazy as _


class Base(models.Model):
    created_at = models.DateTimeField(_("Date Created"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("Date Updated"), auto_now=True)
    items = models.JSONField(verbose_name=_("Items"), default=dict, blank=True, null=True)

    class Meta:
        abstract = True
```

`demo/models/user.py`
```python
import csv
from pathlib import Path
from django.db import models
from demo.models import Base
from django.utils.translation import gettext_lazy as _


class CustomQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs).order_by("id")


class UserTypes(models.TextChoices):
    ADMIN = ("admin", _("Admin"))
    USER = ("user", _("User"))
    STAFF = ("staff", _("Staff"))


class CustomUser(Base):
    class _InnerTypes(models.TextChoices):
        NEW = ("new", _("New"))
        OLD = ("old", _("Old"))

    username = models.CharField(_("User Name"), max_length=100, help_text=_("This is the help text"))
    email = models.EmailField(_("Email"))
    password = models.CharField(verbose_name=_("Password"), max_length=100)
    created_at = models.DateTimeField(_("Date Created"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("Date Updated"), auto_now=True)
    first_name = models.CharField(verbose_name=_("First_Name"), max_length=25)
    last_name = models.CharField(_("Last_Name"), max_length=25)
    is_active = models.BooleanField(verbose_name=_("Is_Active"), default=True)
    choices = models.CharField(
        verbose_name=_("Choices"), max_length=5, choices=UserTypes.choices, default=UserTypes.USER
    )
    groups = models.ManyToManyField("auth.Group", verbose_name=_("Custom Groups"), blank=True)
    owner = models.ForeignKey(
        "auth.User", verbose_name=_("Owner"), related_name="users", on_delete=models.CASCADE, blank=True, null=True
    )
    objects = CustomQuerySet.as_manager()

    class Meta:
        verbose_name = _("Own Custom User")
        verbose_name_plural = _("Own Custom Users")
        ordering = ("-created_at",)
        get_latest_by = ("-created_at", "is_active")
```

Don't forget to check the changes before call `makemigrations` and `migrate` commands.

Don't forget to fill the settings.py like example file with the recommended Django settings before calling the `makemessaging` command.

```python
# settings.py
LANGUAGE_CODE = "en"
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = [Path(BASE_DIR, "locale")]
LANGUAGES = [
    ("en", "English"),
    ("ru", "Russian"),
]
```
