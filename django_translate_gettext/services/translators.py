import re
from pathlib import Path

from deep_translator import GoogleTranslator
from deep_translator.exceptions import LanguageNotSupportedException
from django.conf import settings

from django_translate_gettext.exceptions import TranslatorError


class PoFileTranslator:
    def __init__(self, lang_code: str):
        self.lang_code = lang_code
        self.locale_paths = [Path(filepath) for filepath in settings.LOCALE_PATHS]
        try:
            self.translator = GoogleTranslator(source="auto", target=lang_code)
        except LanguageNotSupportedException as error:
            raise TranslatorError(f"Language code {lang_code} is not supported by the translator") from error

    def translate_block(self, block: str, msgid: list[str]) -> str:
        msgstr = re.findall(r'msgstr "(.*?)"', block)
        if msgstr and msgstr[0]:
            return block
        translated = self.translator.translate(msgid[0])
        return re.sub(r'msgstr "(.*?)*"', f'msgstr "{translated}"', block)

    def process_first_block(self, block: str) -> str:
        parts = block.split("\n")
        raw_msgid, raw_msgstr = parts[-2], parts[-1]
        msgid = re.findall(r'msgid "(.*?)"', raw_msgid)
        parts[-1] = self.translate_block(block=raw_msgstr, msgid=msgid)
        return "\n".join(parts)

    def translate_locale_path(self, *, locale_path: Path) -> None:
        result = []
        po_file = locale_path.joinpath(self.lang_code, "LC_MESSAGES", "django.po")
        if not po_file.exists():
            raise TranslatorError(f"The file for code {self.lang_code} does not exist.")

        file_content = po_file.read_text().split("\n\n")
        for block in file_content:
            if not block:
                continue

            msgid = re.findall(r'msgid "(.*?)"', block)
            if len(msgid) != 1:
                result.append(self.process_first_block(block=block))
                continue

            result.append(self.translate_block(block=block, msgid=msgid))

        po_file.write_text("\n\n".join(result))

    def translate_codes(self) -> None:
        for locale_path in self.locale_paths:
            self.translate_locale_path(locale_path=locale_path)
