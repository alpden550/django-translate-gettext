from django.core.management.base import BaseCommand
from django.db.models import Model

from django_translate_gettext.services import get_all_app_models, update_py_file


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
                app_models = get_all_app_models(app_label=app_name)
            except LookupError as error:
                self.stdout.write(self.style.ERROR(error))
                continue

            self.process_app_models(app_models=app_models, **options)

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

    def process_app_models(self, *, app_models: set[Model], **options) -> None:
        for model in app_models:
            module: str = model._meta.concrete_model.__module__
            if len(module.split(".")) == 1:
                continue
            module_path = module.replace(".", "/")

            update_py_file(file_path=module_path, formatted=options["format"])

            self.stdout.write(self.style.SUCCESS("Successfully added gettext for model files."))
