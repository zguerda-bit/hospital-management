from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from users.permissions import IsDoctor, IsParent
from .models import Document
from .serializers import DocumentSerializer


class PatientDocumentsView(APIView):
    """GET /api/documents/patient/<patient_id>/ — all documents for a patient."""
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        user = request.user

        # FIX: role is a CharField, not an object — was user.role.nom_role == 'PARENT'
        if user.role == 'PARENT':
            docs = Document.objects.filter(
                patient_id=patient_id,
                patient__parent=user,
            )
        else:
            # DOCTOR or ADMIN can see any patient's documents
            docs = Document.objects.filter(patient_id=patient_id)

        return Response(DocumentSerializer(docs, many=True).data)


class UploadDocumentView(APIView):
    """POST /api/documents/upload/ — upload a document (doctors and parents only)."""
    permission_classes = [IsAuthenticated, IsDoctor | IsParent]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class DeleteDocumentView(APIView):
    """DELETE /api/documents/<id>/ — delete a document (doctors only)."""
    permission_classes = [IsAuthenticated, IsDoctor]

    def delete(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        doc.fichier.delete(save=False)
        doc.delete()
        return Response({'detail': 'Document supprimé.'}, status=204)