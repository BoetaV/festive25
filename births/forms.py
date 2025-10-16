from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from datetime import date, time
from .models import Delivery, Baby
from .data import LOCATION_DATA, DISTRICT_CHOICES

# --- STATIC CHOICES LISTS ---
FACILITY_TYPE_CHOICES = [
    ("", "--Select Facility Type--"), ("District Hospital", "District Hospital"),
    ("Private Hospital", "Private Hospital"), ("CHC", "CHC"), ("Clinic", "Clinic"),
]
REPORT_DATE_CHOICES = [
    ("", "--Select Report Date--"), ("25 December 2025", "25 December 2025"),
    ("01 January 2026", "01 January 2026"),
]
TIME_SLOT_CHOICES = [
    ("", "--Select Time Slot--"), ("00:01 - 06:00", "00:01 - 06:00"),
    ("06:01 - 12:00", "06:01 - 12:00"), ("12:01 - 18:00", "12:01 - 18:00"),
    ("18:01 - 24:00", "18:01 - 24:00"),
]
BIRTH_MODE_CHOICES = [
    ("", "--Select Birth Mode--"), ("Normal Vertex", "Normal Vertex"),
    ("Caesarean section Elective", "Caesarean section Elective"),
    ("Caesarean section Emergency", "Caesarean section Emergency"),
    ("Vacuum", "Vacuum"), ("Forceps", "Forceps"), ("Vaginal Breech", "Vaginal Breech"),
]


# --- THE MAIN FORM FOR THE DELIVERY EVENT ---
class DeliveryForm(forms.ModelForm):
    number_of_babies = forms.ChoiceField(
        choices=[('', '--Select Number of Babies--')] + [(i, str(i)) for i in range(1, 6)],
        label="Number of Babies in this Delivery", required=False
    )
    district = forms.ChoiceField(choices=DISTRICT_CHOICES, required=True)
    local_municipality = forms.ChoiceField(choices=[], required=True)
    facility = forms.ChoiceField(choices=[], required=True)
    facility_type = forms.ChoiceField(choices=FACILITY_TYPE_CHOICES, required=True)
    report_date = forms.ChoiceField(choices=REPORT_DATE_CHOICES, required=True)
    time_slot = forms.ChoiceField(choices=TIME_SLOT_CHOICES, required=True)
    birth_mode = forms.ChoiceField(choices=BIRTH_MODE_CHOICES, required=False)

    class Meta:
        model = Delivery
        fields = [
            'district', 'local_municipality', 'facility', 'facility_type',
            'report_date', 'time_slot', 'no_births_to_report', 'born_before_arrival',
            'delivery_time', 'mother_name', 'mother_surname', 'mother_dob',
            'birth_mode', 'gravidity', 'parity'
        ]
        widgets = {
            'mother_dob': forms.DateInput(
                attrs={
                    'class': 'datepicker', # <-- ADD THIS CLASS
                    'placeholder': 'Select Mother D.O.B...'
                }
            ),
            'delivery_time': forms.TimeInput(
                attrs={
                    'class': 'timepicker', # <-- ADD THIS CLASS
                    'placeholder': 'Select Time of Delivery...'
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        data = self.data
        instance = self.instance

        self.fields['time_slot'].widget.attrs['readonly'] = True
        self.fields['time_slot'].help_text = 'This will be set automatically based on the Time of Delivery.'

        # --- Dynamic Dropdown Population ---
        if data:
            try:
                district = data.get('district')
                municipality = data.get('local_municipality')
                if district:
                    self.fields['local_municipality'].choices = [(m, m) for m in LOCATION_DATA['municipalities'].get(district, [])]
                if municipality:
                    self.fields['facility'].choices = [(f, f) for f in LOCATION_DATA['facilities'].get(municipality, [])]
            except (ValueError, TypeError, KeyError):
                pass
        elif instance and instance.pk:
            if instance.district:
                self.fields['local_municipality'].choices = [(m, m) for m in LOCATION_DATA['municipalities'].get(instance.district, [])]
            if instance.local_municipality:
                self.fields['facility'].choices = [(f, f) for f in LOCATION_DATA['facilities'].get(instance.local_municipality, [])]

        # --- Permission Logic ---
        if user:
            if user.is_superuser:
                return  # Superuser gets a fully unlocked form

            profile = user.profile
            if user.groups.filter(name='Admin').exists():
                self.fields['district'].initial = profile.district
                self.fields['district'].choices = [(profile.district, profile.district)]
                self.fields['district'].widget.attrs['readonly'] = True

            elif user.groups.filter(name='User').exists():
                self.fields['district'].initial = profile.district
                self.fields['district'].choices = [(profile.district, profile.district)]
                self.fields['district'].widget.attrs['readonly'] = True
                
                self.fields['local_municipality'].choices = [(profile.local_municipality, profile.local_municipality)]
                self.fields['local_municipality'].initial = profile.local_municipality
                self.fields['local_municipality'].widget.attrs['readonly'] = True
                
                self.fields['facility'].choices = [(profile.facility, profile.facility)]
                self.fields['facility'].initial = profile.facility
                self.fields['facility'].widget.attrs['readonly'] = True
        
        # --- Field Requirement Logic ---
        for field_name, field in self.fields.items():
            if field_name not in ['district', 'local_municipality', 'facility', 'facility_type', 'report_date', 'time_slot', 'no_births_to_report']:
                field.required = False

    def clean_mother_dob(self):
        dob = self.cleaned_data.get('mother_dob')
        if dob is None:
            return dob
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        MIN_AGE = 10
        MAX_AGE = 65
        if not (MIN_AGE <= age <= MAX_AGE):
            raise forms.ValidationError(
                f"Mother's age must be between {MIN_AGE} and {MAX_AGE}. "
                f"The calculated age for the given D.O.B. is {age}."
            )
        return dob

    # ==========================================================
    # NEW MULTI-FIELD VALIDATION METHOD
    # ==========================================================
    def clean(self):
        # First, run the parent class's clean method to get the cleaned_data
        cleaned_data = super().clean()

        # Get the values for delivery_time and time_slot from the form
        delivery_time = cleaned_data.get('delivery_time')
        
        # Don't do anything if this is a NIL report or if no time was entered.
        if cleaned_data.get('no_births_to_report') or not delivery_time:
            return cleaned_data

        # Determine the correct time slot based on the delivery_time
        correct_slot = None
        if time(0, 1) <= delivery_time <= time(6, 0):
            correct_slot = "00:01 - 06:00"
        elif time(6, 1) <= delivery_time <= time(12, 0):
            correct_slot = "06:01 - 12:00"
        elif time(12, 1) <= delivery_time <= time(18, 0):
            correct_slot = "12:01 - 18:00"
        elif time(18, 1) <= delivery_time <= time(23, 59):
            correct_slot = "18:01 - 24:00"
        elif delivery_time == time(0, 0): # Edge case for midnight
            correct_slot = "18:01 - 24:00"

        # If a correct slot was determined, update the cleaned_data
        if correct_slot:
            # This line automatically sets the value for the time_slot field
            cleaned_data['time_slot'] = correct_slot
        else:
            # Optional: if the time doesn't fit any slot, raise an error
            self.add_error('delivery_time', 'The entered time of delivery is invalid.')

        # Always return the full cleaned_data dictionary.
        return cleaned_data

# ==========================================================
# CUSTOM FORMSET TO HANDLE EMPTY FORMS (DEFINE THIS FIRST)
# ==========================================================
class BaseBabyFormSet(BaseInlineFormSet):
    def clean(self):
        """
        This method is called after all individual form validations.
        We check here if any data was submitted at all. If not, but there are
        validation errors on empty forms, we can clear them.
        """
        super().clean()

        if any(self.errors):
            # If there are errors, we check if they are on forms that have no data.
            for form in self.forms:
                if not form.has_changed():
                    # This form is empty and unchanged.
                    # We can clear its errors if we want to allow empty extra forms.
                    # A simple way to handle this is to let it pass and rely on
                    # whether the main DeliveryForm is not a NIL report.
                    form._errors = {}


# ==========================================================
# THE FORMSET FOR MANAGING MULTIPLE BABIES (DEFINE THIS SECOND)
# ==========================================================
BabyFormSet = inlineformset_factory(
    Delivery, 
    Baby,
    fields=('gender', 'weight'),
    formset=BaseBabyFormSet, # <-- This now correctly refers to the class above
    extra=5,          
    max_num=5,        
    can_delete=False, 
    widgets={
        'gender': forms.Select(attrs={'class': 'form-select'}),
        'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight in grams'})
    }
)

class DashboardReportFilterForm(forms.Form):
    district = forms.ChoiceField(choices=DISTRICT_CHOICES, required=True, label="Select District")
    local_municipality = forms.ChoiceField(choices=[('', 'All Municipalities')], required=False, label="Select Local Municipality (Optional)")
    facility = forms.ChoiceField(choices=[('', 'All Facilities')], required=False, label="Select Facility (Optional)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This will be populated by JavaScript, similar to your other forms