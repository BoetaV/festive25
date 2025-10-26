# births/forms.py

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from datetime import date, time
from .models import Delivery, Baby
from .data import LOCATION_DATA, DISTRICT_CHOICES

# --- STATIC CHOICES LISTS ---
FACILITY_TYPE_CHOICES = [("", "--Select Facility Type--"), ("Clinic", "Clinic"), ("Community Health Centre", "Community Health Centre"), ("District Hospital", "District Hospital"), ("Regional Hospital", "Regional Hospital"), ("Tertiary Hospital", "Tertiary Hospital"), ("Academic Hospital", "Academic Hospital"), ("Private Hospital", "Private Hospital")]
REPORT_DATE_CHOICES = [("", "--Select Report Date--"), ("25 December 2025", "25 December 2025"), ("01 January 2026", "01 January 2026")]
TIME_SLOT_CHOICES = [("", "--Select Time Slot--"), ("00:01 - 06:00", "00:01 - 06:00"), ("06:01 - 12:00", "06:01 - 12:00"), ("12:01 - 18:00", "12:01 - 18:00"), ("18:01 - 24:00", "18:01 - 24:00")]
BIRTH_MODE_CHOICES = [("", "--Select Birth Mode--"), ("Normal Vertex", "Normal Vertex"), ("Caesarean section Elective", "Caesarean section Elective"), ("Caesarean section Emergency", "Caesarean section Emergency"), ("Vacuum", "Vacuum"), ("Forceps", "Forceps"), ("Vaginal Breech", "Vaginal Breech")]

# --- THE MAIN FORM FOR THE DELIVERY EVENT ---
class DeliveryForm(forms.ModelForm):
    number_of_babies = forms.ChoiceField(choices=[('', '--Select Number of Babies--')] + [(i, str(i)) for i in range(1, 6)], label="Number of Babies in this Delivery", required=False)
    district = forms.ChoiceField(choices=DISTRICT_CHOICES, required=True)
    local_municipality = forms.ChoiceField(choices=[], required=False)
    facility = forms.ChoiceField(choices=[], required=False)
    facility_type = forms.ChoiceField(choices=FACILITY_TYPE_CHOICES, required=True)
    report_date = forms.ChoiceField(choices=REPORT_DATE_CHOICES, required=True)
    time_slot = forms.ChoiceField(choices=TIME_SLOT_CHOICES, required=False)
    birth_mode = forms.ChoiceField(choices=BIRTH_MODE_CHOICES, required=False)

    class Meta:
        model = Delivery
        fields = ['district', 'local_municipality', 'facility', 'facility_type', 'report_date', 'time_slot', 'no_births_to_report', 'born_before_arrival', 'delivery_time', 'mother_name', 'mother_surname', 'mother_dob', 'birth_mode', 'gravidity', 'parity']
        widgets = {
            'mother_dob': forms.DateInput(attrs={'class': 'datepicker', 'placeholder': 'Select Mother D.O.B...'}),
            'delivery_time': forms.TimeInput(attrs={'class': 'timepicker', 'placeholder': 'Select Time of Delivery...'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['time_slot'].widget.attrs['disabled'] = True
        self.fields['time_slot'].help_text = 'This field is only for NIL reports. It is set automatically for live births.'
        
        self.fields['facility_type'].widget.attrs['disabled'] = True
        self.fields['facility_type'].help_text = 'This is set automatically when you select a Facility.'
        
        data = self.data
        instance = self.instance

        if data:
            try:
                district = data.get('district'); municipality = data.get('local_municipality')
                if district: self.fields['local_municipality'].choices = [(m, m) for m in LOCATION_DATA['municipalities'].get(district, [])]
                if municipality: self.fields['facility'].choices = [(f, f) for f in LOCATION_DATA['facilities'].get(municipality, [])]
            except (ValueError, TypeError, KeyError): pass
        elif instance and instance.pk:
            if instance.district: self.fields['local_municipality'].choices = [(m, m) for m in LOCATION_DATA['municipalities'].get(instance.district, [])]
            if instance.local_municipality: self.fields['facility'].choices = [(f, f) for f in LOCATION_DATA['facilities'].get(instance.local_municipality, [])]

        if user:
            if user.is_superuser or user.groups.filter(name='ProvinceUser').exists():
                return
            profile = user.profile
            if user.groups.filter(name='Admin').exists():
                self.fields['district'].initial = profile.district; self.fields['district'].choices = [(profile.district, profile.district)]; self.fields['district'].widget.attrs['readonly'] = True
            elif user.groups.filter(name='User').exists():
                self.fields['district'].initial = profile.district; self.fields['district'].choices = [(profile.district, profile.district)]; self.fields['district'].widget.attrs['readonly'] = True
                self.fields['local_municipality'].choices = [(profile.local_municipality, profile.local_municipality)]; self.fields['local_municipality'].initial = profile.local_municipality; self.fields['local_municipality'].widget.attrs['readonly'] = True
                self.fields['facility'].choices = [(profile.facility, profile.facility)]; self.fields['facility'].initial = profile.facility; self.fields['facility'].widget.attrs['readonly'] = True

    def clean_mother_dob(self):
        dob = self.cleaned_data.get('mother_dob')
        # Only require D.O.B if this is NOT a NIL report.
        if not self.cleaned_data.get('no_births_to_report') and not dob:
             raise forms.ValidationError("This field is required when reporting a birth.")
        if not dob: return dob
        today = date.today(); age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        MIN_AGE, MAX_AGE = 10, 65
        if not (MIN_AGE <= age <= MAX_AGE): raise forms.ValidationError(f"Mother's age must be between {MIN_AGE} and {MAX_AGE}. Calculated age is {age}.")
        return dob

    def clean(self):
        cleaned_data = super().clean()
        is_nil_report = cleaned_data.get('no_births_to_report')
        delivery_time = cleaned_data.get('delivery_time')
        time_slot = cleaned_data.get('time_slot')

        if is_nil_report:
            if not time_slot: self.add_error('time_slot', 'You must select a time slot for a NIL report.')
            for field in ['delivery_time', 'mother_name', 'mother_surname', 'mother_dob', 'birth_mode', 'gravidity', 'parity', 'number_of_babies']:
                cleaned_data[field] = None
            return cleaned_data
        else:
            required_fields = ['delivery_time', 'mother_name', 'mother_surname', 'birth_mode', 'number_of_babies', 'local_municipality', 'facility']
            for field in required_fields:
                if not cleaned_data.get(field): self.add_error(field, f'This field is required when reporting a birth.')
            
            if self.errors: return # Stop further validation if required fields are missing
            
            slot_map = {(time(0, 1), time(6, 0)): "00:01 - 06:00", (time(6, 1), time(12, 0)): "06:01 - 12:00", (time(12, 1), time(18, 0)): "12:01 - 18:00", (time(18, 1), time(23, 59)): "18:01 - 24:00"}
            correct_slot = next((slot for (start, end), slot in slot_map.items() if start <= delivery_time <= end), None)
            if delivery_time == time(0, 0): correct_slot = "18:01 - 24:00"
            
            if correct_slot: cleaned_data['time_slot'] = correct_slot
            else: self.add_error('delivery_time', 'The entered Time of Delivery is invalid.')
        return cleaned_data

# --- CUSTOM FORMSET & INLINEFORMSET FACTORY ---
class BaseBabyFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            for form in self.forms:
                if not form.has_changed(): form._errors = {}

BabyFormSet = inlineformset_factory(Delivery, Baby, formset=BaseBabyFormSet, fields=('gender', 'weight'), extra=5, max_num=5, can_delete=False, widgets={'gender': forms.Select(attrs={'class': 'form-select'}),'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight in grams'})})

# --- PDF REPORT FILTER FORM ---
class DashboardReportFilterForm(forms.Form):
    district = forms.ChoiceField(required=False, label="District")
    local_municipality = forms.ChoiceField(required=False, label="Local Municipality (Optional)")
    facility = forms.ChoiceField(required=False, label="Facility (Optional)")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['district'].choices = [('', 'All Districts')] + [(d[0], d[1]) for d in DISTRICT_CHOICES if d[0]]
        self.fields['local_municipality'].choices = [('', 'All Municipalities')]
        self.fields['facility'].choices = [('', 'All Facilities')]

        if user and not user.is_superuser and not user.groups.filter(name='ProvinceUser').exists():
            profile = user.profile
            if user.groups.filter(name='Admin').exists():
                self.fields['district'].choices = [(profile.district, profile.district)]; self.fields['district'].initial = profile.district; self.fields['district'].widget.attrs['readonly'] = True
                self.fields['local_municipality'].choices = [('', 'All Municipalities')] + [(m, m) for m in LOCATION_DATA['municipalities'].get(profile.district, [])]
            elif user.groups.filter(name='User').exists():
                self.fields['district'].choices = [(profile.district, profile.district)]; self.fields['district'].initial = profile.district; self.fields['district'].widget.attrs['readonly'] = True
                self.fields['local_municipality'].choices = [(profile.local_municipality, profile.local_municipality)]; self.fields['local_municipality'].initial = profile.local_municipality; self.fields['local_municipality'].widget.attrs['readonly'] = True
                self.fields['facility'].choices = [(profile.facility, profile.facility)]; self.fields['facility'].initial = profile.facility; self.fields['facility'].widget.attrs['readonly'] = True