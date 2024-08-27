from .models import UserSettings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin

class CustomLocaleMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            user_settings = UserSettings.objects.get(user=request.user)
            language = user_settings.language
            translation.activate(language)
        else:
            translation.deactivate()

class UserSettingsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_settings, created = UserSettings.objects.get_or_create(user=request.user)
            # Gérer le mode sombre
            request.dark_mode = user_settings.dark_mode

            # Gérer la langue
            request.session['django_language'] = user_settings.language

        print(request.session['django_language'])
        response = self.get_response(request)
        return response
