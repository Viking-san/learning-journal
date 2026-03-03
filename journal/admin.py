from django.contrib import admin
from .models import Category, Entry, Tag, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_at', 'updated_at']
    list_filter = ['category', 'created_at']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'
    filter_horizontal = ['tags']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'entry', 'created_at']
    list_filter = ['created_at']
    search_fields = ['author_name', 'content']