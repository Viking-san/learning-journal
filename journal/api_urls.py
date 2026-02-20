from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('entries', views.EntryViewSet, basename='entry')
router.register('categories', views.CategoryViewSet, basename='category')
router.register('tags', views.TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
