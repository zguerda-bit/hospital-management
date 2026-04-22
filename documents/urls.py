from django.urls import path
from .views import PatientDocumentsView, UploadDocumentView, DeleteDocumentView

urlpatterns = [
    path('upload/',                      UploadDocumentView.as_view(),   name='upload-document'),
    path('patient/<int:patient_id>/',    PatientDocumentsView.as_view(), name='patient-documents'),
    path('<int:pk>/',                    DeleteDocumentView.as_view(),   name='delete-document'),
]
