from django.conf import settings
from datetime import datetime

def global_context(request):
    """
    Provides global variables to all templates:
    Site metadata, current year, user role check, active currency & language.
    """
    is_admin_user = False
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            is_admin_user = True
        elif hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN':
            is_admin_user = True

    active_currency = request.COOKIES.get('railaway_currency', 'INR')
    active_language = request.COOKIES.get('railaway_language', 'en')

    return {
        'SITE_NAME': 'RailAway',
        'SITE_TAGLINE': 'Multi-Modal Online Ticket Booking System',
        'CURRENT_YEAR': datetime.now().year,
        'IS_ADMIN_USER': is_admin_user,
        'ACTIVE_CURRENCY': active_currency,
        'ACTIVE_LANGUAGE': active_language,
    }

