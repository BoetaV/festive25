# accounts/views.py

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.db.models import Q
from .forms import UserCreateForm, UserUpdateForm
from django.core.cache import cache

class AdminRequiredMixin(UserPassesTestMixin):
    """Ensures the logged-in user is a Superuser or in the 'Admin' group."""
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Admin').exists()

class UserListView(AdminRequiredMixin, ListView):
    """Displays a paginated and searchable list of users, respecting permissions."""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related('profile').order_by('first_name')
        user = self.request.user

        # Superusers see all users. Admins see only users in their own district.
        if user.is_superuser:
            pass
        elif user.groups.filter(name='Admin').exists():
            queryset = queryset.filter(profile__district=user.profile.district)

        # Apply search filtering after permission filtering
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(profile__persal_number__icontains=query) |
                Q(profile__district__icontains=query) |
                Q(profile__facility__icontains=query)
            )
        return queryset
class UserCreateView(AdminRequiredMixin, CreateView):
    """Handles the creation of new users."""
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create New User'
        context['submit_button_text'] = 'Create User'
        return context

    def get_form_kwargs(self):
        """Passes the logged-in user to the form for permission checks."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class UserUpdateView(AdminRequiredMixin, UpdateView):
    """Handles editing an existing user."""
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit User'
        context['submit_button_text'] = 'Update User'
        
        # --- THIS IS THE KEY ADDITION ---
        # Pass the user's saved municipality and facility to the template.
        # This allows the JavaScript to pre-select the correct options on page load.
        if hasattr(self.object, 'profile'):
            context['initial_municipality'] = self.object.profile.local_municipality
            context['initial_facility'] = self.object.profile.facility
        
        return context

    def get_form_kwargs(self):
        """Passes the logged-in user to the form for permission checks."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class UserDeleteView(AdminRequiredMixin, DeleteView):
    """Handles the deletion of a user."""
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
