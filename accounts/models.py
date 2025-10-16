# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    TITLE_CHOICES = [('Mr', 'Mr'), ('Ms', 'Ms'), ('Mrs', 'Mrs'), ('Miss', 'Miss'), ('Dr', 'Dr'), ('Prof', 'Prof')]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=10, choices=TITLE_CHOICES, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    persal_number = models.CharField(max_length=8, unique=True)
    mobile_number = models.CharField(max_length=10, null=True, blank=True)
    district = models.CharField(max_length=100)
    local_municipality = models.CharField(max_length=100, null=True, blank=True)
    facility = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} ({self.persal_number})'