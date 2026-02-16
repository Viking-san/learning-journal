from django.db import models
from django.utils.text import slugify


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
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Entry(models.Model):
    """Запись в дневнике обучения"""
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='entries',
        verbose_name="Категория"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ['-created_at']  # Новые записи сверху

    def __str__(self):
        return self.title
