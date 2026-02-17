from django.shortcuts import render
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView
from .models import Entry
from .forms import EntryForm
from django.urls import reverse_lazy


class EntryListView(ListView):
    model = Entry
    template_name = 'journal/entry_list.html'
    context_object_name = 'entries'
    ordering = ['-created_at']
    paginate_by = 10


class EntryDetailView(DetailView):
    model = Entry
    template_name = 'journal/entry_detail.html'
    context_object_name = 'entry'


class EntryCreateView(CreateView):
    model = Entry
    form_class = EntryForm
    template_name = 'journal/entry_form.html'
    success_url = reverse_lazy('journal:entry_list')


class EntryUpdateView(UpdateView):
    model = Entry
    form_class = EntryForm
    template_name = 'journal/entry_form.html'
    # success_url = reverse_lazy('journal:entry_list')

    def get_success_url(self):
        return reverse_lazy('journal:entry_detail', kwargs={'pk': self.object.pk})


class EntryDeleteView(DeleteView):
    model = Entry
    template_name = 'journal/entry_confirm_delete.html'
    success_url = reverse_lazy('journal:entry_detail')
