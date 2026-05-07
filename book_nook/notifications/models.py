from django.db import models
from accounts.models import NookUser, Friendship
from threads.models import Thread


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
    thread = models.ForeignKey(Thread, related_name="notifications", blank=True, null=True, on_delete=models.CASCADE)
    friendship = models.ForeignKey(Friendship, related_name="notifications", blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
      ordering = ['-created_at']