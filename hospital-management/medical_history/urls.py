from django.urls import path
from .views import (
    AllergieListCreateView,
    AllergieDetailView,
    AntecedentListCreateView,
    AntecedentDetailView,
)

urlpatterns = [
    # Allergies
    path('patients/<int:patient_id>/allergies/',  AllergieListCreateView.as_view(), name='allergie_list_create'),
    path('allergies/<int:allergie_id>/',          AllergieDetailView.as_view(),     name='allergie_detail'),

    # Antécédents
    path('patients/<int:patient_id>/antecedents/', AntecedentListCreateView.as_view(), name='antecedent_list_create'),
    path('antecedents/<int:antecedent_id>/',       AntecedentDetailView.as_view(),     name='antecedent_detail'),
]