from django.shortcuts import render
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView,TemplateView
from .models import Entry, Category, Tag
from .forms import EntryForm
from django.urls import reverse_lazy
from django.db.models import Count
from django.db.models.functions import TruncWeek
from datetime import timedelta, datetime
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .serializers import EntrySerializer, CategorySerializer, TagSerializer


class EntryListView(ListView):
    model = Entry
    template_name = 'journal/entry_list.html'
    context_object_name = 'entries'
    ordering = ['-created_at']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['total_entries'] = Entry.objects.count()
        context['tags'] = Tag.objects.all()
        return context


class EntryDetailView(DetailView):
    model = Entry
    template_name = 'journal/entry_detail.html'
    context_object_name = 'entry'


class EntryCreateView(CreateView):
    model = Entry
    form_class = EntryForm
    template_name = 'journal/entry_form.html'
    
    def get_success_url(self):
        return reverse_lazy('journal:entry_detail', kwargs={'pk': self.object.pk})


class EntryUpdateView(UpdateView):
    model = Entry
    form_class = EntryForm
    template_name = 'journal/entry_form.html'

    def get_success_url(self):
        return reverse_lazy('journal:entry_detail', kwargs={'pk': self.object.pk})


class EntryDeleteView(DeleteView):
    model = Entry
    template_name = 'journal/entry_confirm_delete.html'
    success_url = reverse_lazy('journal:entry_list')


class CategoryEntriesView(ListView):
    model = Entry
    template_name = 'journal/entry_list.html'
    context_object_name = 'entries'
    paginate_by = 10

    def get_queryset(self):
        self.category = Category.objects.get(slug=self.kwargs['slug'])
        return Entry.objects.filter(category=self.category).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.category
        context['total_entries'] = Entry.objects.count()
        context['tags'] = Tag.objects.all()
        return context
    

class TagEntriesView(ListView):
    model = Entry
    template_name = 'journal/entry_list.html'
    context_object_name = 'entries'
    paginate_by = 10

    def get_queryset(self):
        self.tag = Tag.objects.get(slug=self.kwargs['slug'])
        return Entry.objects.filter(tags=self.tag).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['total_entries'] = Entry.objects.count()
        context['current_tag'] = self.tag
        context['tags'] = Tag.objects.all()
        return context
    

class StatsView(TemplateView):
    template_name = 'journal/stats.html'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)

        # totals
        context['total_entries'] = Entry.objects.count()
        context['total_categories'] = Category.objects.count()
        context['total_tags'] = Tag.objects.count()

        # entries by categories
        context['entries_by_categories'] = Category.objects.annotate(count=Count('entries')).order_by('-count')

        # entries by weeks(12 weeks)
        twelve_weeks_ago = datetime.now() - timedelta(weeks=12)
        entries_by_week = Entry.objects.filter(
            created_at__gte=twelve_weeks_ago
        ).annotate(
            week=TruncWeek('created_at')
        ).values('week').annotate(
            count=Count('id')
        ).order_by('week')

        context['entries_by_week'] = entries_by_week

        return context


class EntryViewSet(viewsets.ModelViewSet):
    """
    API endpoint для записей.
    
    Фильтрация:
    - /api/entries/?category=1
    - /api/entries/?tags=2
    
    Поиск:
    - /api/entries/?search=django
    
    Сортировка:
    - /api/entries/?ordering=-created_at
    - /api/entries/?ordering=title
    """
    queryset = Entry.objects.all().order_by('-created_at')
    serializer_class = EntrySerializer
    permission_classes = [AllowAny]
    filterset_fields = ['category', 'tags']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'title']


class CategoryViewSet(viewsets.ModelViewSet):
    """API endpoint для категорий"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class TagViewSet(viewsets.ModelViewSet):
    """API endpoint для тегов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
