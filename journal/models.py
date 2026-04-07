from tabnanny import verbose
from django.db import models
from django.utils.text import slugify
from pytils.translit import slugify as pytils_slugify
from django.contrib.auth.models import User
from django.db.models import Count, Q
from .tools import validate_img_size, wrapper_upload_to


class Category(models.Model):
    """Категория для записей (Python, Django, DevOps и т.д.)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = models.SlugField(unique=True, blank=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = pytils_slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class TagQuerySet(models.QuerySet):
    def popular(self, limit=5):
        return self.annotate(count=Count('entries', filter=Q(entries__is_published=True))).order_by('-count')[:limit]


class Tag(models.Model):
    """Тег для записей"""
    name = models.CharField(max_length=50, unique=True, verbose_name='Название')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Slug')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    objects = TagQuerySet.as_manager()

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = pytils_slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class EntryQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def drafts(self):
        return self.filter(is_published=False)

    def recent(self, limit=10):
        return self.order_by('-created_at')[:limit]

    def by_category(self, category):
        return self.filter(category=category)

    def with_details(self):
        return self.select_related('category', 'author').prefetch_related('tags')

    def with_full_details(self):
        return self.select_related('category', 'author').prefetch_related('tags', 'comments', 'comments__author_name')


class Entry(models.Model):
    """Запись в дневнике обучения"""
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='entries', 
        verbose_name='Автор'
    )
    content = models.TextField(verbose_name="Содержание")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name="Категория"
    )

    tags = models.ManyToManyField(Tag, blank=True, related_name='entries', verbose_name='Теги')
    image = models.ImageField(
        upload_to=wrapper_upload_to, 
        validators=[validate_img_size], 
        blank=True, 
        null=True, 
        verbose_name='Изображение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    
    objects = EntryQuerySet.as_manager()    # Custom QuerySet

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Комментарий к записи"""
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Запись'
    )
    # author_name = models.CharField(max_length=100, verbose_name='Имя автора', null=True)
    author_name = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='comments', 
        verbose_name='Имя автора'
    )
    content = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']

    def __str__(self):
        return f'Комментарий от {self.author_name} к {self.entry.title}'
    

class EntryLog(models.Model):
    """Лог записи"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
    ]    

    entry = models.ForeignKey(
        Entry,
        on_delete=models.SET_NULL,
        null=True,
        related_name='entry_logs',
        verbose_name='Запись'
    )
    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES,  # ← Добавить
        verbose_name='Действие'
        )
    entry_title = models.CharField(max_length=200, verbose_name="Заголовок")
    changed_entry_id = models.PositiveIntegerField(verbose_name='ID')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время')

    class Meta:
        verbose_name = 'Лог записи'
        verbose_name_plural = 'Логи записей'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.timestamp} - {self.entry_title} - {self.action}'
