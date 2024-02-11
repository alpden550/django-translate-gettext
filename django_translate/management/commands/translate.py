import subprocess
from collections.abc import Generator

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Model

from django_translate.services import update_py_file


class Command(BaseCommand):
    help = "Add calling gettext for the model files"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "apps", nargs="+", type=str, help="Apps to add gettext for the model files.\nFor example: app1 app2 app3"
        )
        parser.add_argument(
            "--format",
            action="store_true",
            help="Call Ruff formatting tool to format the code after generating new model files.",
        )

    def handle(self, **options) -> None:
        for app_name in options["apps"]:
            try:
                app_models = apps.get_app_config(app_name).get_models()
            except LookupError as error:
                self.stdout.write(self.style.ERROR(error))
                continue

            self.process_app_models(app_models=app_models)

            if options["format"]:
                self.stdout.write(self.style.SUCCESS("Formatting the code..."))
                subprocess.run(["ruff", "format", "."], check=True)  # noqa: S603, S607
                self.stdout.write(self.style.SUCCESS("The code has been formatted successfully."))

    def process_app_models(self, *, app_models: Generator[Model]) -> None:
        for model in app_models:
            module: str = model._meta.concrete_model.__module__
            module_path = module.replace(".", "/")

            update_py_file(file_path=module_path)

            self.stdout.write(self.style.SUCCESS("Successfully added gettext for model files."))
            self.stdout.write(
                self.style.WARNING(
                    "Please, check the files, and don't forget to call migrate command to apply the changes "
                    "to the database after adding the gettext."
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Please, un the command 'python manage.py makemessages -l {lang code}' to create the .po files."
                )
            )
