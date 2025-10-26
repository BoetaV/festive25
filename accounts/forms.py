# accounts/forms.py

from django import forms
from django.contrib.auth.models import User, Group
from .models import Profile
from births.data import DISTRICT_CHOICES, LOCATION_DATA

DEFAULT_PASSWORD = "Password1"

class UserFormMixin(forms.Form):
    """A single mixin to handle all shared form logic."""
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # --- Make location fields optional by default ---
        self.fields['district'].required = False
        self.fields['local_municipality'].required = False
        self.fields['facility'].required = False

        # --- Dynamic Dropdown & Permission Logic ---
        data = self.data
        instance = getattr(self, 'instance', None)
        
        if data:
            try:
                district = data.get('district'); municipality = data.get('local_municipality')
                if district: self.fields['local_municipality'].choices = [(m, m) for m in LOCATION_DATA['municipalities'].get(district, [])]
                if municipality: self.fields['facility'].choices = [(f, f) for f in LOCATION_DATA['facilities'].get(municipality, [])]
            except (ValueError, TypeError, KeyError): pass
        elif instance and instance.pk and hasattr(instance, 'profile'):
            profile = instance.profile
            if profile.district: self.fields['local_municipality'].choices = [(m, m) for m in LOCATION_DATA['municipalities'].get(profile.district, [])]
            if profile.local_municipality: self.fields['facility'].choices = [(f, f) for f in LOCATION_DATA['facilities'].get(profile.local_municipality, [])]
        
        if self.user and not self.user.is_superuser:
            if self.user.groups.filter(name='Admin').exists():
                admin_district = self.user.profile.district
                self.fields['district'].choices = [(admin_district, admin_district)]
                self.fields['district'].initial = admin_district
                self.fields['district'].widget.attrs['readonly'] = True
                self.fields['role'].queryset = Group.objects.filter(name='User')

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        if role:
            if role.name == 'Admin':
                if not cleaned_data.get('district'): self.add_error('district', 'District is required for the Admin role.')
            elif role.name == 'User':
                if not cleaned_data.get('district'): self.add_error('district', 'District is required for the User role.')
                if not cleaned_data.get('local_municipality'): self.add_error('local_municipality', 'Local Municipality is required for the User role.')
                if not cleaned_data.get('facility'): self.add_error('facility', 'Facility is required for the User role.')
        
        return cleaned_data


class UserCreateForm(UserFormMixin, forms.ModelForm):
    first_name = forms.CharField(label="Name", min_length=3, required=True)
    last_name = forms.CharField(label="Surname", required=True)
    email = forms.EmailField(required=False)
    title = forms.ChoiceField(choices=Profile.TITLE_CHOICES)
    designation = forms.CharField(max_length=100, required=False)
    persal_number = forms.CharField(label="Persal Number", min_length=8, max_length=8)
    mobile_number = forms.CharField(label="Mobile Number", min_length=10, max_length=10, required=False)
    role = forms.ModelChoiceField(queryset=Group.objects.all(), required=True)
    district = forms.ChoiceField(choices=DISTRICT_CHOICES)
    local_municipality = forms.ChoiceField(choices=[])
    facility = forms.ChoiceField(choices=[])

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_persal_number(self):
        persal = self.cleaned_data.get('persal_number')
        if not persal or not persal.isdigit() or len(persal) != 8:
            raise forms.ValidationError("Persal Number must be an 8-digit number.")
        if Profile.objects.filter(persal_number=persal).exists():
            raise forms.ValidationError("A user with this Persal Number already exists.")
        return persal
    
    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number')
        if mobile and (not mobile.isdigit() or len(mobile) != 10):
            raise forms.ValidationError("Mobile Number must be a 10-digit number.")
        return mobile
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['persal_number']
        user.set_password(DEFAULT_PASSWORD)
        if commit:
            user.save()
            user.groups.add(self.cleaned_data['role'])
            Profile.objects.create(
                user=user, title=self.cleaned_data['title'],
                persal_number=self.cleaned_data['persal_number'],
                designation=self.cleaned_data.get('designation'),
                mobile_number=self.cleaned_data.get('mobile_number'),
                district=self.cleaned_data.get('district'),
                local_municipality=self.cleaned_data.get('local_municipality'),
                facility=self.cleaned_data.get('facility')
            )
        return user


class UserUpdateForm(UserFormMixin, forms.ModelForm):
    first_name = forms.CharField(label="Name", min_length=3, required=True)
    last_name = forms.CharField(label="Surname", required=True)
    email = forms.EmailField(required=False)
    password = forms.CharField(label='New Password', widget=forms.PasswordInput, required=False, help_text="Leave blank to keep the current password.")
    title = forms.ChoiceField(choices=Profile.TITLE_CHOICES)
    designation = forms.CharField(max_length=100, required=False)
    persal_number = forms.CharField(label="Persal Number", min_length=8, max_length=8)
    mobile_number = forms.CharField(label="Mobile Number", min_length=10, max_length=10, required=False)
    role = forms.ModelChoiceField(queryset=Group.objects.all(), required=True)
    district = forms.ChoiceField(choices=DISTRICT_CHOICES)
    local_municipality = forms.ChoiceField(choices=[])
    facility = forms.ChoiceField(choices=[])

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.instance, 'profile'):
            profile = self.instance.profile
            self.fields['title'].initial = profile.title
            self.fields['designation'].initial = profile.designation
            self.fields['persal_number'].initial = profile.persal_number
            self.fields['mobile_number'].initial = profile.mobile_number
            self.fields['district'].initial = profile.district
            self.fields['local_municipality'].initial = profile.local_municipality
            self.fields['facility'].initial = profile.facility
        if self.instance.groups.exists():
            self.fields['role'].initial = self.instance.groups.first()

    def clean_persal_number(self):
        persal = self.cleaned_data.get('persal_number')
        if not persal or not persal.isdigit() or len(persal) != 8: raise forms.ValidationError("Persal Number must be an 8-digit number.")
        if Profile.objects.filter(persal_number=persal).exclude(user=self.instance).exists(): raise forms.ValidationError("Another user with this Persal Number already exists.")
        return persal
    
    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number')
        if mobile and (not mobile.isdigit() or len(mobile) != 10): raise forms.ValidationError("Mobile Number must be a 10-digit number.")
        return mobile

    def save(self, commit=True):
        user = super().save(commit=True)
        password = self.cleaned_data.get("password")
        if password: user.set_password(password)
        user.username = self.cleaned_data['persal_number']; user.save()
        user.groups.clear(); user.groups.add(self.cleaned_data['role'])
        Profile.objects.update_or_create(
            user=user,
            defaults={
                'title': self.cleaned_data['title'], 'persal_number': self.cleaned_data['persal_number'],
                'designation': self.cleaned_data.get('designation'), 'mobile_number': self.cleaned_data.get('mobile_number'),
                'district': self.cleaned_data.get('district'), 'local_municipality': self.cleaned_data.get('local_municipality'),
                'facility': self.cleaned_data.get('facility'),
            }
        )
        return user