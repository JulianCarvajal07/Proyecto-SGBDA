# tu_app/middleware.py
from django.shortcuts import redirect
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = getattr(settings, 'LOGIN_EXEMPT_URLS', [])

    def __call__(self, request):
        if not request.user.is_authenticated:
            if not any(request.path.startswith(url) for url in self.exempt_urls):
                return redirect(settings.LOGIN_URL)
        return self.get_response(request)