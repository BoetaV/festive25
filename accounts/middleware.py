# accounts/middleware.py
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.contrib import messages

# Use the same constant for consistency
DEFAULT_PASSWORD = "Password1"

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Middleware runs on every request. We only care about authenticated users.
        if request.user.is_authenticated:
            # Avoid redirect loops by checking the current path
            if request.path != reverse('password_change') and request.path != reverse('logout'):
                
                # Check if the user is still using the default password
                if request.user.check_password(DEFAULT_PASSWORD):
                    # Add a message to inform the user
                    messages.warning(request, 'For security, you must change your temporary password before proceeding.')
                    # Redirect them to the password change page
                    return redirect('password_change')
        
        return response