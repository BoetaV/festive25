from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import Profile

class PersalAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # The 'username' from the login form is treated as a persal number
            profile = Profile.objects.get(persal_number=username)
            user = profile.user
            if user.check_password(password):
                return user
        except Profile.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None