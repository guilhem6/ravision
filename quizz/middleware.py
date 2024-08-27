from .models import UserSettings

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

        response = self.get_response(request)
        return response
