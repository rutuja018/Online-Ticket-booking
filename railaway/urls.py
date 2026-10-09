"""
URL configuration for railaway project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('railways/', include('railways.urls', namespace='railways')),
    path('airlines/', include('airlines.urls', namespace='airlines')),
    path('buses/', include('buses.urls', namespace='buses')),
    path('hotels/', include('hotels.urls', namespace='hotels')),
    path('food/', include('food_catering.urls', namespace='food_catering')),
    path('retiring-rooms/', include('retiring_rooms.urls', namespace='retiring_rooms')),
    path('experience/', include('experiences.urls', namespace='experiences')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('management/', include('admin_dashboard.urls', namespace='admin_dashboard')),
]

# Custom error handlers
handler400 = 'core.views.error_400'
handler403 = 'core.views.error_403'
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
