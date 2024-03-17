import subprocess
from contextlib import suppress
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand
from loguru import logger

from django_translate_gettext.services import update_py_file
from django_translate_gettext.services.files import fetch_app_files


class Command(BaseCommand):
    help = "Add calling gettext for the model files"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "apps", nargs="+", type=str, help="Apps to add gettext for the model files.\nFor example: app1 app2 app3"
        )
        parser.add_argument(
            "-f",
            "--format",
            action="store_true",
            help="Call Ruff formatting tool to format the code after generating new model files.",
        )

    def handle(self, **options) -> None:
        for app_name in options["apps"]:
            try:
                apps.get_app_config(app_name)
            except LookupError as error:
                self.stdout.write(self.style.ERROR(error))
                continue

            self.process_app_files(app_name=app_name, **options)

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

    @staticmethod
    def process_py_file(*, file_path: Path, formatted=True) -> None:
        with suppress(FileNotFoundError):
            update_py_file(file_path=file_path)
            filename = file_path.absolute()
            if formatted:
                logger.info(f"Formatting the code for files in app {filename!s}")
                subprocess.run(["ruff", "format", f"{filename!s}"], check=True)  # noqa: S603, S607

    def process_app_files(self, *, app_name: str, **options) -> None:
        for file_path in fetch_app_files(app_name=app_name):
            self.process_py_file(file_path=file_path, formatted=options["format"])

        self.stdout.write(self.style.SUCCESS("Successfully added gettext for app files."))
