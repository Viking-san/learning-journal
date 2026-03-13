from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Entry, EntryLog


# Логирование активности записей
@receiver(post_save, sender=Entry)
def log_entry_change(sender, instance, created, **kwargs):
    action = 'created' if created else 'updated'
    EntryLog.objects.create(
        entry=instance, 
        entry_title=instance.title, 
        action=action, 
        changed_entry_id=instance.id
    )


@receiver(pre_delete, sender=Entry)
def log_entry_delete(sender, instance, **kwargs):
    EntryLog.objects.create(
        entry=instance, 
        entry_title=instance.title, 
        action='deleted', 
        changed_entry_id=instance.id
    )
