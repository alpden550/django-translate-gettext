import ast
from collections.abc import Iterator
from pathlib import Path

from django_translate_gettext.constants import TO_SKIP
from django_translate_gettext.services.transformers import ClassDefTransformer


def fetch_app_files(app_name: str) -> Iterator[Path]:
    """
    Fetch all python files in the app directory excluding the files in the TO_SKIP list.
    Args:
        app_name (str): The app name to fetch the files from.

    Returns:

    """

    all_files = {file for file in Path(app_name).rglob("*.py") if file.is_file()}
    return filter(lambda x: not any(skip in str(x) for skip in TO_SKIP), all_files)


def update_py_file(*, file_path: Path) -> None:
    """
    Update the python file with the gettext call wrapping.
    Args:
        file_path (Path): The file path Pathlib object to update.

    Returns:
        None
    """
    tree = ast.parse(file_path.read_text())

    transformer = ClassDefTransformer()
    new_tree = transformer.visit(tree)
    new_tree = transformer.insert_getetxt_import(new_tree)

    code = ast.unparse(new_tree)
    file_path.write_text(code)
