# births/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Delivery(models.Model):
    # Location Info
    district = models.CharField(max_length=100)
    local_municipality = models.CharField(max_length=100, blank=True, null=True) # Allow blank
    facility = models.CharField(max_length=100, blank=True, null=True) # Allow blank
    facility_type = models.CharField(max_length=100, blank=True, null=True) # Allow blank

    # Reporting Info
    report_date = models.CharField(max_length=50)
    time_slot = models.CharField(max_length=50, blank=True, null=True) # Allow blank

    # --- MISSING FIELDS ---
    no_births_to_report = models.BooleanField(default=False)
    born_before_arrival = models.BooleanField(default=False)
    delivery_time = models.TimeField(null=True, blank=True)
    mother_name = models.CharField(max_length=100, null=True, blank=True)
    mother_surname = models.CharField(max_length=100, null=True, blank=True)
    mother_dob = models.DateField(null=True, blank=True)
    birth_mode = models.CharField(max_length=100, null=True, blank=True)
    gravidity = models.PositiveIntegerField(null=True, blank=True)
    parity = models.PositiveIntegerField(null=True, blank=True)
    
    # Metadata
    captured_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def mother_full_name(self):
        parts = [self.mother_name, self.mother_surname]
        return " ".join(p for p in parts if p)

    def __str__(self):
        if self.no_births_to_report:
            return f"NIL Report for {self.facility} on {self.report_date}"
        return f"Delivery at {self.facility} - {self.mother_full_name or 'N/A'}"

    def get_absolute_url(self):
        return reverse('delivery_list')

class Baby(models.Model):
    GENDER_CHOICES = [("Male", "Male"), ("Female", "Female")]

    delivery = models.ForeignKey(Delivery, related_name='babies', on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    weight = models.PositiveIntegerField(null=True, blank=True, help_text="Weight in grams")

    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Baby ({self.gender}, {self.weight}g) for Delivery {self.delivery.id}"
    
