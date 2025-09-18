from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Thread


@receiver(m2m_changed, sender=Thread.participants.through)
def set_group_name(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        if instance.participants.count() > 2 and not instance.name:
            instance.name = "Group Chat"
        elif instance.participants.count() == 2:
            instance.name = None
            
        instance.save(update_fields=['name'])

        
