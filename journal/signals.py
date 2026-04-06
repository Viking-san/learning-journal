from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Entry, EntryLog
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate


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
    print(f'[log] {instance.title} - {action}')


@receiver(pre_delete, sender=Entry)
def log_entry_delete(sender, instance, **kwargs):
    EntryLog.objects.create(
        entry=instance, 
        entry_title=instance.title, 
        action='deleted', 
        changed_entry_id=instance.id
    )
    print(f'[log] {instance.title} - deleted')


# Создать группу администраторов и заполнить её всеми доступными разрешениями
@receiver(post_migrate)
def create_groups(sender, **kwargs):
    if sender.name != 'journal':
        return
    
    group, _ = Group.objects.get_or_create(name='Administrator')
    all_permissions = Permission.objects.all()
    group.permissions.set(all_permissions)