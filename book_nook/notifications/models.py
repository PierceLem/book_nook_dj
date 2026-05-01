from django.db import models
from accounts.models import NookUser


class Notification(models.Model):

    NOTIFICATION_TYPES = [
      ('success', 'Success'),   
      ('info', 'Info'),         
      ('error', 'Error'),   
    ]

    recipient = models.ForeignKey(
      NookUser,
      on_delete=models.CASCADE,
      related_name='notifications'
    )
    type = models.CharField(
      max_length=20,
      choices=NOTIFICATION_TYPES
    )
    title = models.CharField(max_length=255, default='Alert')
    content = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
      ordering = ['-created_at']