from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """Extra data collected on the Register page (the 'Status' field)."""

    STATUS_CHOICES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f'{self.user.username} ({self.status})'
