# births/models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Delivery(models.Model):
    # Location Info
    district = models.CharField(max_length=100)
    local_municipality = models.CharField(max_length=100)
    facility = models.CharField(max_length=100)
    facility_type = models.CharField(max_length=100) # This field is correct as a simple CharField

    # ... (rest of your fields are correct) ...
    report_date = models.CharField(max_length=50)
    # ...
    captured_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    @property
    def mother_full_name(self):
        """Returns the concatenated full name of the mother."""
        parts = [self.mother_name, self.mother_surname]
        return " ".join(p for p in parts if p)

    def __str__(self):
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
    
