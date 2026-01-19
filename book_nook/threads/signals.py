from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Thread


@receiver(m2m_changed, sender=Thread.participants.through)
def set_group_name(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        print('signal triggered')
        instance.reconcile_name()

        
