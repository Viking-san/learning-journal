from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView, TemplateView, View
from .models import Entry, Category, EntryLog, Tag, Comment
from .forms import EntryForm, CommentForm, CustomUserCreationForm, ImportEntryForm
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.db.models.functions import TruncWeek, TruncDate
from datetime import timedelta, datetime
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import EntrySerializer, CategorySerializer, TagSerializer
from django.utils import timezone
from collections import defaultdict
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.http import HttpResponse
import frontmatter
from urllib.parse import quote
from django.utils.text import slugify
from django.views.generic import FormView
from django.contrib import messages


def export_entry(request, pk):
    entry = get_object_or_404(Entry, pk=pk)

    filename = f'{slugify(entry.title, allow_unicode=True)}.md'
    encoded_title = quote(filename)

    # metadata
    title=entry.title
    category = entry.category.name
    tags = [tag.name for tag in entry.tags.all()]
    
    md_content = entry.content
    post = frontmatter.Post(md_content, tags=tags, category=category, title=title)
    md_content = frontmatter.dumps(post)

    # Отправляем как файл
    response = HttpResponse(md_content, content_type='text/markdown')
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_title}"
    return response


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


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
                Q(author__username__icontains=q) |
                Q(content__icontains=q)
            ).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Все записи'
        context['categories'] = Category.objects.filter(entries__is_published=True).annotate(
            entry_count=Count('entries')
        )
        context['total_entries'] = Entry.objects.published().count()
        context['tags'] = Tag.objects.popular()
        return context

    
class DraftListView(LoginRequiredMixin, ListView):
    model = Entry
    template_name = 'journal/draft_list.html'
    context_object_name = 'drafts'
    paginate_by = 10

    def get_queryset(self):
        queryset = Entry.objects.drafts().with_details().filter(author=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_drafts'] = Entry.objects.drafts().filter(author=self.request.user).count()

        return context


class PublishDraftView(LoginRequiredMixin, View):
    """
    Опубликовать черновик
    """
    def post(self, request, pk):
        entry = get_object_or_404(Entry, pk=pk)
        if entry.author != request.user:
            raise PermissionDenied
        if not entry.is_published:
            entry.is_published = True
            entry.save()

        return redirect('journal:entry_detail', pk=pk)
    

class EntryDetailView(DetailView):
    model = Entry
    template_name = 'journal/entry_detail.html'
    context_object_name = 'entry'
    queryset = Entry.objects.with_full_details()

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
            if self.request.user.is_authenticated:
                comment.author_name = self.request.user
            else:
                comment.author_name = None
            comment.save()
            return redirect('journal:entry_detail', pk=self.object.pk)

        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)
    

class ImportEntryView(LoginRequiredMixin, FormView):
    form_class = ImportEntryForm
    success_url = reverse_lazy('journal:entry_list')

    def get(self, request, *args, **kwargs):
        return redirect('journal:entry_create')

    def form_valid(self, form):
        try:
            # Читаем файл
            md_file = self.request.FILES['md_file']
            md_content = md_file.read().decode('utf-8')
            post = frontmatter.loads(md_content)

            # передаем данные в форму через session для get_initial
            self.request.session['import_content'] = post.content
            self.request.session['import_metadata'] = post.metadata
            return redirect('journal:entry_create')

        except Exception as e:
            messages.error(self.request, f"Ошибка при импорте файла")
            return redirect('journal:entry_create')

    def form_invalid(self, form):
        return redirect('journal:entry_create')


class EntryCreateView(LoginRequiredMixin, CreateView):
    model = Entry
    form_class = EntryForm
    template_name = 'journal/entry_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_form'] = ImportEntryForm()
        return context
    
    def get_initial(self):
        initial = super().get_initial()

        metadata = self.request.session.pop('import_metadata', None)
        content = self.request.session.pop('import_content', None)
        
        if metadata:
            if metadata.get('title'):
                initial['title'] = metadata['title']

            metadata_category = metadata.get('category')
            if metadata_category:
                category = Category.objects.filter(name=metadata_category).first()
                if category:
                    initial['category'] = category
                else:
                    messages.info(self.request, f"Категория '{metadata_category}' не найдена, выберите вручную")

            metadata_tags = metadata.get('tags')
            if metadata_tags:
                existing_tags = Tag.objects.filter(name__in=metadata['tags'])
                initial['tags'] = existing_tags
                if len(existing_tags) != len(metadata_tags):
                    difference_set = set(metadata_tags) - {tag.name for tag in existing_tags}
                    messages.info(self.request, f"Следующие теги не найдены: {', '.join(map(str, difference_set))}")

        if content:
            initial['content'] = content
        
        return initial

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('journal:entry_detail', kwargs={'pk': self.object.pk})


class EntryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Entry
    form_class = EntryForm
    template_name = 'journal/entry_form.html'

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user or self.request.user.groups.filter(name='Administrator').exists()

    def get_success_url(self):
        return reverse_lazy('journal:entry_detail', kwargs={'pk': self.object.pk})


class EntryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Entry
    template_name = 'journal/entry_confirm_delete.html'
    success_url = reverse_lazy('journal:entry_list')

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user or self.request.user.groups.filter(name='Administrator').exists()


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'journal/comment_form.html'

    def test_func(self):
        obj = self.get_object()
        return obj.author_name == self.request.user or self.request.user.groups.filter(name='Administrator').exists()

    def get_success_url(self):
        return reverse_lazy('journal:entry_detail', kwargs={'pk': self.object.entry.pk})
    

class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'journal/comment_confirm_delete.html'

    def test_func(self):
        obj = self.get_object()
        return obj.author_name == self.request.user or self.request.user.groups.filter(name='Administrator').exists()

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
        context['page_title'] = f'Все записи в категории: {self.category}'
        context['categories'] = Category.objects.filter(entries__is_published=True).annotate(
            entry_count=Count('entries')
        )
        context['current_category'] = self.category
        context['total_entries'] = Entry.objects.published().count()
        context['tags'] = Tag.objects.popular()
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
        context['page_title'] = f'Все записи с тегом: {self.tag}'
        context['categories'] = Category.objects.filter(entries__is_published=True).annotate(
            entry_count=Count('entries')
        )
        context['total_entries'] = Entry.objects.published().count()
        context['current_tag'] = self.tag
        context['tags'] = Tag.objects.popular()
        return context


class AuthorEntriesView(ListView):
    model = Entry
    template_name = 'journal/entry_list.html'
    context_object_name = 'entries'
    paginate_by = 10

    def get_queryset(self):
        self.author = get_object_or_404(User, username=self.kwargs['username'])
        return Entry.objects.published().filter(author=self.author).with_details()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Все записи пользователя: {self.author}'
        context['categories'] = Category.objects.filter(entries__is_published=True).annotate(
            entry_count=Count('entries')
        )
        context['total_entries'] = Entry.objects.published().filter(author=self.author).count()
        context['current_author'] = self.author
        context['tags'] = Tag.objects.popular()
        return context


class EntryLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = EntryLog
    template_name = 'journal/entry_log_list.html'
    context_object_name = 'logs'
    paginate_by = 18
    ordering = ['-timestamp']

    def test_func(self):
        return self.request.user.groups.filter(name='Administrator').exists()
    
    def handle_no_permission(self):
        return redirect('journal:entry_list')

    def get_queryset(self):        
        action = self.request.GET.get('action')
        title_search = self.request.GET.get('title_search', '').strip()
        id_search = self.request.GET.get('id_search', '').strip()
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        queryset = super().get_queryset().select_related('entry')

        if action:
            queryset = queryset.filter(action=action)
        if title_search:
            queryset = queryset.filter(entry_title__icontains=title_search)
        if id_search:
            queryset = queryset.filter(changed_entry_id=id_search)
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = EntryLog.objects.values('action').annotate(count=Count('id'))
        context['stats'] = {item['action']: item['count'] for item in stats}

        seven_days_ago = timezone.now() - timedelta(days=7)
        activity_by_day = (
            EntryLog.objects
            .filter(timestamp__gte=seven_days_ago)
            .annotate(date=TruncDate('timestamp'))
            .values('date', 'action')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        data_by_date = defaultdict(lambda: {'created': 0, 'updated': 0, 'deleted': 0})

        for item in activity_by_day:
            day = item['date'].strftime('%d.%m')
            data_by_date[day][item['action']] = item['count']

        context['dates'] = list(data_by_date.keys())
        context['created_counts'] = [data_by_date[d]['created'] for d in context['dates']]
        context['updated_counts'] = [data_by_date[d]['updated'] for d in context['dates']]
        context['deleted_counts'] = [data_by_date[d]['deleted'] for d in context['dates']]

        return context
    

class StatsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'journal/stats.html'

    def test_func(self):
        return self.request.user.groups.filter(name='Administrator').exists()
    
    def handle_no_permission(self):
        return redirect('journal:entry_list')

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
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category', 'tags']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'title']


class CategoryViewSet(viewsets.ModelViewSet):
    """API endpoint для категорий"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class TagViewSet(viewsets.ModelViewSet):
    """API endpoint для тегов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
