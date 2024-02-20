from django.db.models import Model


def get_all_app_models(app_label: str) -> set[Model]:
    """Get all models for the app label including the abstract models.

    Args:
        app_label (str): The app label to get the models for.

    Returns:
        set[Model]: The set of models for the app label.
    """
    result = set()
    generation = {Model}
    while generation:
        generation = {sc for c in generation for sc in c.__subclasses__()}
        result.update([c for c in generation if c._meta.app_label == app_label])  # noqa: SLF001
    return result
