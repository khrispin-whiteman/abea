from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def switch_language_path(path, lang_code):
    """
    Remove any existing language prefix and rebuild path for selected language.
    English stays without prefix because prefix_default_language=False.
    """
    if not path:
        path = "/"

    supported = [code for code, _ in settings.LANGUAGES]

    parts = [p for p in path.split("/") if p]

    if parts and parts[0] in supported:
        parts = parts[1:]

    remainder = "/" + "/".join(parts) if parts else "/"

    if path.endswith("/") and not remainder.endswith("/"):
        remainder += "/"

    if lang_code == settings.LANGUAGE_CODE:
        return remainder

    if remainder == "/":
        return f"/{lang_code}/"

    return f"/{lang_code}{remainder}"