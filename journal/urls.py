from django.urls import path
from . import views


app_name = 'journal'

urlpatterns = [
    path('', views.EntryListView.as_view(), name='entry_list'),
    path('entry/<int:pk>/', views.EntryDetailView.as_view(), name='entry_detail'),
    path('entry/create/', views.EntryCreateView.as_view(), name='entry_create'),
    path('entry/<int:pk>/edit/', views.EntryUpdateView.as_view(), name='entry_update'),
    path('entry/<int:pk>/delete/', views.EntryDeleteView.as_view(), name='entry_delete'),
    path('category/<slug:slug>/', views.CategoryEntriesView.as_view(), name='category_entries'),
    path('tag/<slug:slug>/', views.TagEntriesView.as_view(), name='tag_entries'),
    path('stats/', views.StatsView.as_view(), name='stats')
    ]
