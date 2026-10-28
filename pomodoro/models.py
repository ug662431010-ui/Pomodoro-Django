from django.db import models
from django.contrib.auth.models import User


class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=255)
    task_description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.task_name


class TimerSession(models.Model):
    """One run of the timer in one mode (Focus, Short Break or Long Break)."""

    MODE_CHOICES = [
        ('focus', 'Focus (25m)'),
        ('short_break', 'Short Break (5m)'),
        ('long_break', 'Long Break (15m)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # The task the user was working on (empty if the user had already ended it)
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, null=True, blank=True, related_name='sessions'
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)  # seconds really counted down
    completed = models.BooleanField(default=False)     # True = ran all the way to 00:00

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f'{self.get_mode_display()} - {self.user.username}'