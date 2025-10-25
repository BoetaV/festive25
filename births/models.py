from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Delivery(models.Model):
    # Location Info
    district = models.CharField(max_length=100)
    local_municipality = models.CharField(max_length=100)
    facility = models.CharField(max_length=100)
    facility_type = models.CharField(max_length=100)

    # Reporting Info
    report_date = models.CharField(max_length=50)
    time_slot = models.CharField(max_length=50)

    # Delivery Status Flags
    no_births_to_report = models.BooleanField(default=False, verbose_name="No Births to Report")
    born_before_arrival = models.BooleanField(default=False, verbose_name="Born Before Arrival (BBA)")
    
    # Mother and Delivery Details
    delivery_time = models.TimeField(null=True, blank=True)
    mother_name = models.CharField(max_length=100, null=True, blank=True)
    mother_surname = models.CharField(max_length=100, null=True, blank=True)
    mother_dob = models.DateField(null=True, blank=True, verbose_name="Mother's D.O.B.")
    birth_mode = models.CharField(max_length=100, null=True, blank=True)
    gravidity = models.PositiveIntegerField(null=True, blank=True)
    parity = models.PositiveIntegerField(null=True, blank=True)
    
    # Metadata
    captured_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.no_births_to_report:
            return f"NIL Report for {self.facility} on {self.report_date}"
        return f"Delivery at {self.facility} - {self.mother_surname}, {self.mother_name}"

    def get_absolute_url(self):
        return reverse('birth_list')
    
    # =============================================
    # NEW PROPERTY FOR FULL NAME
    # =============================================
    @property
    def mother_full_name(self):
        """
        Returns the concatenated full name of the mother.
        Handles cases where one or both names might be missing.
        """
        parts = [self.mother_name, self.mother_surname]
        # This will join only the non-empty parts with a space.
        return " ".join(p for p in parts if p)

    def __str__(self):
        # You can even use the new property here for a cleaner string representation!
        if self.no_births_to_report:
            return f"NIL Report for {self.facility} on {self.report_date}"
        full_name = self.mother_full_name
        return f"Delivery at {self.facility} - {full_name or 'N/A'}"

    def get_absolute_url(self):
        return reverse('delivery_list')

class Baby(models.Model):
    GENDER_CHOICES = [("Male", "Male"), ("Female", "Female")]

    delivery = models.ForeignKey(Delivery, related_name='babies', on_delete=models.CASCADE)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    weight = models.PositiveIntegerField(null=True, blank=True, help_text="Weight in grams")

    def __str__(self):
        return f"Baby ({self.gender}, {self.weight}g) for Delivery {self.delivery.id}"
    
