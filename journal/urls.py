from django.urls import path
from . import views


app_name = 'journal'

urlpatterns = [
    path('', views.EntryListView.as_view(), name='entry_list'),
    path('entry/<int:pk>/', views.EntryDetailView.as_view(), name='entry_detail'),
    path('entry/create/', views.EntryCreateView.as_view(), name='entry_create'),
    path('entry/<int:pk>/edit/', views.EntryUpdateView.as_view(), name='entry_update'),
    path('entry/<int:pk>/delete/', views.EntryDeleteView.as_view(), name='entry_delete'),    
    path('comment/<int:pk>/edit/', views.CommentUpdateView.as_view(), name='comment_update'),
    path('comment/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
    path('category/<slug:slug>/', views.CategoryEntriesView.as_view(), name='category_entries'),
    path('tag/<slug:slug>/', views.TagEntriesView.as_view(), name='tag_entries'),
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('logs/', views.EntryLogListView.as_view(), name='entry_logs'),
    path('drafts/', views.DraftListView.as_view(), name='drafts'),
    path('drafts/<int:pk>/publish/', views.PublishDraftView.as_view(), name='publish_draft'),
    path('author/<str:username>/', views.AuthorEntriesView.as_view(), name='author_entries'),
    path('entry/<int:pk>/download/', views.export_entry, name='export_entry'),
    path('entry/import/', views.ImportEntryView.as_view(), name='import_entry'),
    ]
