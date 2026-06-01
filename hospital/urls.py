from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views 

urlpatterns = [
    path('admin/',             admin.site.urls),
    path('api/users/',         include('users.urls')),
    path('api/consultations/', include('consultations.urls')),
    path('api/notifications/', include('notifications.urls')),

    path('api/documents/',     include('documents.urls')),
    path('api/medical/',       include('medical_history.urls')),
    path('api/patient/',       include('patients.urls')),
    path('api/doctor/',        include('doctors.urls')),
    path('secretaire/',views.secretaire_panel, name='secretaire'),
    path('api/admin-panel/',   include('admin_panel.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)