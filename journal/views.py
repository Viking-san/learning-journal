from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView, TemplateView
from rest_framework.decorators import action
from .models import Entry, Category, EntryLog, Tag, Comment
from .forms import EntryForm, CommentForm
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.db.models.functions import TruncWeek, TruncDate
from datetime import timedelta, datetime
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .serializers import EntrySerializer, CategorySerializer, TagSerializer
from django.utils import timezone


class EntryListView(ListView):
    model = Entry
    template_name = 'journal/entry_list.html'
    context_object_name = 'entries'
    paginate_by = 10
    

    def get_queryset(self):
        q = self.request.GET.get('q', '').strip()
        queryset = Entry.objects.published().with_details()

        if q:
            queryset = queryset.filter(
                Q(category__name__icontains=q) |
                Q(tags__name__icontains=q) |
                Q(title__icontains=q) |
                Q(content__icontains=q)
            ).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(entries__is_published=True).annotate(
            entry_count=Count('entries')
        )
        context['total_entries'] = Entry.objects.published().count()
        context['tags'] = Tag.objects.all()
        return context


class EntryDetailView(DetailView):
    model = Entry
    template_name = 'journal/entry_detail.html'
    context_object_name = 'entry'
    queryset = Entry.objects.published().with_full_details()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all()
        context['form'] = CommentForm()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.entry = self.object
            comment.save()
            return redirect('journal:entry_detail', pk=self.object.pk)

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


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


class CommentUpdateView(UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'journal/comment_form.html'

    def get_success_url(self):
        return reverse_lazy('journal:entry_detail', kwargs={'pk': self.object.entry.pk})
    

class CommentDeleteView(DeleteView):
    model = Comment
    template_name = 'journal/comment_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('journal:entry_detail', kwargs={'pk': self.object.entry.pk})


class CategoryEntriesView(ListView):
    model = Entry
    template_name = 'journal/entry_list.html'
    context_object_name = 'entries'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Entry.objects.published().by_category(self.category).with_details()


    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(entries__is_published=True).annotate(
            entry_count=Count('entries')
        )
        context['current_category'] = self.category
        context['total_entries'] = Entry.objects.published().count()
        context['tags'] = Tag.objects.all()
        return context
    

class TagEntriesView(ListView):
    model = Entry
    template_name = 'journal/entry_list.html'
    context_object_name = 'entries'
    paginate_by = 10

    def get_queryset(self):
        self.tag = Tag.objects.get(slug=self.kwargs['slug'])
        return Entry.objects.published().filter(tags=self.tag).with_details()


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(entries__is_published=True).annotate(
            entry_count=Count('entries')
        )
        context['total_entries'] = Entry.objects.published().count()
        context['current_tag'] = self.tag
        context['tags'] = Tag.objects.all()
        return context


class EntryLogListView(ListView):
    model = EntryLog
    template_name = 'journal/entry_log_list.html'
    context_object_name = 'logs'
    paginate_by = 18
    ordering = ['-timestamp']

    def get_queryset(self):
        queryset = super().get_queryset()

        # фильтрация по действию
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # фильтрация по заголовку
        q = self.request.GET.get('title_search', '').strip()
        if q:
            queryset = queryset.filter(Q(entry_title__icontains=q))

        # фильтрация по id
        q = self.request.GET.get('id_search', '').strip()
        if q:
            queryset = queryset.filter(Q(changed_entry_id__icontains=q))

        # фильтрация по дате
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['created'] = EntryLog.objects.filter(action='created').count()
        context['updated'] = EntryLog.objects.filter(action='updated').count()
        context['deleted'] = EntryLog.objects.filter(action='deleted').count()

        seven_days_ago = timezone.now() - timedelta(days=7)
        activity_by_day = (
            EntryLog.objects
            .filter(timestamp__gte=seven_days_ago)
            .annotate(date=TruncDate('timestamp'))
            .values('date', 'action')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        context['activity_data'] = activity_by_day

        dates = []
        counts = []
        for item in activity_by_day:
            dates.append(item['date'].strftime('%d.%m'))
            counts.append(item['count'])

        context['dates'] = dates
        context['counts'] = counts

        return context
    

class StatsView(TemplateView):
    template_name = 'journal/stats.html'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)

        # totals
        context['total_entries'] = Entry.objects.published().count()
        context['total_categories'] = Category.objects.count()
        context['total_tags'] = Tag.objects.count()

        # entries by categories
        context['entries_by_categories'] = (
            Category.objects
            .filter(entries__is_published=True)
            .annotate(count=Count('entries'))
            .order_by('-count')
        )

        # entries by weeks(12 weeks)
        twelve_weeks_ago = timezone.now() - timedelta(weeks=12)
        entries_by_week = (
            Entry.objects.published()
            .filter(created_at__gte=twelve_weeks_ago)
            .annotate(week=TruncWeek('created_at'))
            .values('week')
            .annotate(count=Count('id'))
            .order_by('week')
        )

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
    # Не забудь что objects показывает все, а published только опубликованное
    queryset = Entry.objects.select_related('category').prefetch_related('tags').order_by('-created_at')
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
