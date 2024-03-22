import concurrent.futures
import subprocess
from contextlib import suppress
from pathlib import Path
from typing import NamedTuple

from django.apps import apps
from django.core.management.base import BaseCommand

from django_translate_gettext.exceptions import TranslatorError
from django_translate_gettext.services import update_py_file
from django_translate_gettext.services.files import fetch_app_files
from django_translate_gettext.services.translators import PoFileTranslator

MAX_WORKERS = 5


class FileToGettext(NamedTuple):
    file_path: Path
    formatted: bool


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
        files_to_gettext = []
        for app_name in options["apps"]:
            try:
                apps.get_app_config(app_name)
            except LookupError as error:
                self.stdout.write(self.style.ERROR(error))
                continue

            files_to_gettext.extend(self.fetch_app_files_to_gettext(app_name=app_name, formatted=options["format"]))

        self.stdout.write(
            self.style.WARNING(
                "Please, check the files, and don't forget to call migrate command to apply the changes "
                "to the database after adding the gettext."
            )
        )

        self.add_gettext_for_files(files=files_to_gettext)
        self.stdout.write(self.style.SUCCESS("Successfully added gettext for the apps files."))

        self.process_translating(**options)

    def translate_lang_code(self, lang_code: str) -> None:
        translator = PoFileTranslator(lang_code=lang_code)
        translator.translate_codes()
        self.stdout.write(self.style.SUCCESS(f"Successfully translated for lang code {lang_code}."))

    def process_translating(self, **options) -> None:
        if not options["makemessages"]:
            self.stdout.write(
                self.style.SUCCESS(
                    "Please, un the command 'python manage.py makemessages -l {lang code}' to create the .po files."
                )
            )
            return

        self.stdout.write(self.style.WARNING("Calling makemessages command to create the .po files."))
        langs = [f"--locale={lang}" for lang in options["makemessages"]]
        with suppress(subprocess.CalledProcessError):
            subprocess.run(["python", "manage.py", "makemessages", *langs], check=True)  # noqa: S603, S607

        lang_codes = options["makemessages"]
        max_workers = MAX_WORKERS if len(lang_codes) > MAX_WORKERS else len(lang_codes)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.translate_lang_code, code) for code in lang_codes]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except TranslatorError as error:  # noqa: PERF203
                    self.stdout.write(self.style.ERROR(f"Translator error: {error}"))

    @staticmethod
    def fetch_app_files_to_gettext(*, app_name: str, formatted: bool = False) -> list[FileToGettext]:
        return [
            FileToGettext(file_path=file_path, formatted=formatted) for file_path in fetch_app_files(app_name=app_name)
        ]

    @staticmethod
    def gettext_py_file(file_path: Path, formatted: bool = False) -> None:  # noqa: FBT001, FBT002
        with suppress(FileNotFoundError):
            update_py_file(file_path=file_path)
            filename = file_path.absolute()
            if formatted:
                subprocess.run(["ruff", "format", f"{filename!s}"], check=True)  # noqa: S603, S607

    def add_gettext_for_files(self, files: list[FileToGettext]) -> None:
        max_workers = MAX_WORKERS if len(files) > MAX_WORKERS else len(files)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.gettext_py_file, f.file_path, f.formatted) for f in files]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except FileNotFoundError as error:  # noqa: PERF203
                    self.stdout.write(self.style.ERROR(f"File not found error: {error}"))
