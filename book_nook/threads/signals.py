from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Thread

@receiver(m2m_changed, sender=Thread.participants.through)
def set_group_name(sender, instance, action, **kwargs):
    if action == "post_add" and not instance.name:
        if instance.participants.count() > 2:
            instance.name = "Group Chat"
            instance.save(update_fields=["name"])