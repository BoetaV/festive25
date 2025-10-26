# accounts/middleware.py

from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone

# The default password for new users
DEFAULT_PASSWORD = "Password1"

class ForcePasswordChangeMiddleware:
    """
    Redirects users to the password change page if they are still using
    the default temporary password.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Only check for authenticated, non-superuser users
        if request.user.is_authenticated and not request.user.is_superuser:
            # Avoid a redirect loop by excluding the password change and logout pages
            if request.path not in [reverse('password_change'), reverse('logout')]:
                
                # Check if the user's current password is the default one
                if request.user.check_password(DEFAULT_PASSWORD):
                    messages.warning(request, 'For security, you must change your temporary password before proceeding.')
                    return redirect('password_change')
        
        return response
