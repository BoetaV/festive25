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

class ActiveUserListView(AdminRequiredMixin, ListView):
    # We no longer set the model or queryset here, as we will build it manually
    template_name = 'accounts/active_user_list.html'
    context_object_name = 'active_users_data' # Use a more descriptive name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Get all potential user IDs
        all_user_ids = User.objects.filter(is_superuser=False).values_list('id', flat=True)
        
        # 2. Construct all the cache keys
        cache_keys = [f'last-seen-{user_id}' for user_id in all_user_ids]
        
        # 3. Get all the values from the cache in a single bulk request
        found_caches = cache.get_many(cache_keys)
        
        # 4. Get the user IDs of the active users
        active_user_ids = [int(key.split('-')[-1]) for key in found_caches.keys()]
        
        # 5. Fetch the user objects in a single query
        active_users = User.objects.filter(id__in=active_user_ids).select_related('profile')
        
        # 6. Create the final list with user and their last activity time
        active_users_data = []
        for user in active_users:
            cache_key = f'last-seen-{user.id}'
            cached_data = found_caches.get(cache_key)
            if cached_data:
                active_users_data.append({
                    'user': user,
                    'last_activity': cached_data['last_activity']
                })
        
        # 7. Sort the list to show the most recently active user first
        active_users_data.sort(key=lambda x: x['last_activity'], reverse=True)

        context['active_users_data'] = active_users_data
        return context

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
