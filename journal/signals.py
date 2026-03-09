from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Entry, EntryLog


# @receiver(post_save, sender=Entry)
# def notify_new_entry(sender, instance, created, **kwargs):
#     """
#     Отправить email при создании новой записи
#     """
#     if created:
#         subject = f'Новая запись: {instance.title}'
#         message = f'Создана запись в категории {instance.category.name}\n\n{instance.content[:200]}...'

#         # Пока просто принтим
#         print(f'[email] {subject}')
#         print(f'[email] {message}')



# Логирование активности записей
@receiver(post_save, sender=Entry)
def log_entry_change(sender, instance, created, **kwargs):
    if created:
        EntryLog.objects.create(entry=instance, entry_title=instance.title, action='created')
        print(f'[log] {instance.title} created')
    else:
        EntryLog.objects.create(entry=instance, entry_title=instance.title, action='updated')
        print(f'[log] {instance.title} updated')


@receiver(pre_delete, sender=Entry)
def log_entry_delete(sender, instance, **kwargs):
    EntryLog.objects.create(entry=instance, entry_title=instance.title, action='deleted')
    print(f'[log] {instance.title} deleted')
