from django.conf import settings

def cdn_settings(request):
    return {
        'USE_CDN': getattr(settings, 'USE_CDN', False)
    }
    