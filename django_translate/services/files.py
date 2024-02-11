import ast
from pathlib import Path

from django.conf import settings
from loguru import logger

from django_translate.services.transformers import ClassDefTransformer


def update_py_file(*, file_path: str) -> None:
    model_file = Path(settings.BASE_DIR, file_path).with_suffix(".py").absolute()
    tree = ast.parse(model_file.read_text())

    transformer = ClassDefTransformer()
    new_tree = transformer.visit(tree)
    new_tree = transformer.insert_getetxt_import(new_tree)

    code = ast.unparse(new_tree)
    model_file.write_text(code)

    logger.info(f"File {model_file} has been updated")
