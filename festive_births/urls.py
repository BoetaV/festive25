from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm # <-- IMPORT THIS

# Create a custom form class on the fly to change the label
class CustomAuthForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Persal Number"

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Modify the LoginView to use our custom form
    path('login/', LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=CustomAuthForm # <-- ADD THIS LINE
    ), name='login'),

    path('users/', include('accounts.urls')),
    path('', include('births.urls')),
]