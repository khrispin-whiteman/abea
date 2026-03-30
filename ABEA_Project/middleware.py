from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import is_valid_path
from django.utils import translation


class LanguageRedirectMiddleware:
    """
    Redirect first-time visitors to a language-prefixed URL based on browser language,
    unless they already have a language cookie or are visiting excluded paths.
    """

    EXCLUDED_PATH_PREFIXES = (
        "/admin/",
        "/i18n/",
        "/static/",
        "/media/",
        "/pesapal/",
    )

    def __init__(self, get_response):
        self.get_response = get_response
        self.supported_languages = [code for code, _ in settings.LANGUAGES]
        self.default_language = settings.LANGUAGE_CODE

    def __call__(self, request):
        path = request.path_info or "/"

        if self._should_skip(request, path):
            return self.get_response(request)

        # If language already selected in cookie, do nothing
        language_from_cookie = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if language_from_cookie in self.supported_languages:
            return self.get_response(request)

        # If URL already has language prefix, do nothing
        if self._path_has_language_prefix(path):
            return self.get_response(request)

        # Detect browser-preferred language
        preferred_language = self._get_preferred_language(request)

        # Do not redirect for default language
        if preferred_language == self.default_language:
            return self.get_response(request)

        localized_path = f"/{preferred_language}{path}"

        query_string = request.META.get("QUERY_STRING")
        if query_string:
            localized_path = f"{localized_path}?{query_string}"

        if is_valid_path(localized_path):
            return HttpResponseRedirect(localized_path)

        return self.get_response(request)

    def _should_skip(self, request, path):
        if request.method != "GET":
            return True

        for prefix in self.EXCLUDED_PATH_PREFIXES:
            if path.startswith(prefix):
                return True

        return False

    def _path_has_language_prefix(self, path):
        parts = [part for part in path.split("/") if part]
        return bool(parts and parts[0] in self.supported_languages)

    def _get_preferred_language(self, request):
        browser_lang = translation.get_language_from_request(request, check_path=False)
        if not browser_lang:
            return self.default_language

        short_code = browser_lang.split("-")[0].lower()
        if short_code in self.supported_languages:
            return short_code

        return self.default_language