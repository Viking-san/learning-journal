from django.conf import settings

def cdn_settings(request):
    return {
        'USE_CDN': getattr(settings, 'USE_CDN', False)
    }

def user_groups(request):
    is_admin = (
        request.user.is_authenticated and 
        request.user.groups.filter(name='Administrator').exists()
    )
    return {'is_admin': is_admin}