import subprocess
from contextlib import suppress
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand

from django_translate_gettext.exceptions import TranslatorError
from django_translate_gettext.services import update_py_file
from django_translate_gettext.services.files import fetch_app_files
from django_translate_gettext.services.translators import PoFileTranslator


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
        parser.add_argument(
            "-mm",
            "--makemessages",
            nargs="+",
            type=str,
            help="Call makemessages command to create the .po files after adding the gettext "
            "and translating for the passed languages."
            "\nFor example: en de fr",
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

        self.process_translating(**options)

    def translate_lang_code(self, *, lang_code: str) -> None:
        try:
            translator = PoFileTranslator(lang_code=lang_code)
            translator.translate_codes()
            self.stdout.write(self.style.SUCCESS(f"Successfully translated for lang code {lang_code}."))
        except TranslatorError as error:
            self.stdout.write(self.style.ERROR(error))

    def process_translating(self, **options) -> None:
        if options["makemessages"]:
            self.stdout.write(self.style.WARNING("Calling makemessages command to create the .po files."))
            langs = [f"--locale={lang}" for lang in options["makemessages"]]
            with suppress(subprocess.CalledProcessError):
                subprocess.run(["python", "manage.py", "makemessages", *langs], check=True)  # noqa: S603, S607

            for code in options["makemessages"]:
                self.translate_lang_code(lang_code=code)

        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "Please, un the command 'python manage.py makemessages -l {lang code}' to create the .po files."
                )
            )

    def process_py_file(self, *, file_path: Path, formatted=True) -> None:
        with suppress(FileNotFoundError):
            update_py_file(file_path=file_path)
            filename = file_path.absolute()
            if formatted:
                subprocess.run(["ruff", "format", f"{filename!s}"], check=True)  # noqa: S603, S607
                self.stdout.write(self.style.SUCCESS(f"Formatted the code for files in app {filename!s}"))

    def process_app_files(self, *, app_name: str, **options) -> None:
        for file_path in fetch_app_files(app_name=app_name):
            self.process_py_file(file_path=file_path, formatted=options["format"])

        self.stdout.write(self.style.SUCCESS("Successfully added gettext for app files."))
