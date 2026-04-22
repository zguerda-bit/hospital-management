from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Message
from .serializers import MessageSerializer, SendMessageSerializer


class InboxView(APIView):
    """GET /api/messages/inbox/ — all messages received by the logged-in user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        messages = Message.objects.filter(destinataire=request.user)
        return Response(MessageSerializer(messages, many=True).data)


class SentView(APIView):
    """GET /api/messages/sent/ — all messages sent by the logged-in user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        messages = Message.objects.filter(expediteur=request.user)
        return Response(MessageSerializer(messages, many=True).data)


class SendMessageView(APIView):
    """POST /api/messages/send/ — send a message to another user."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(expediteur=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class ConversationView(APIView):
    """GET /api/messages/conversation/<user_id>/ — full conversation with one user."""
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        messages = Message.objects.filter(
            Q(expediteur=request.user,   destinataire_id=user_id) |
            Q(expediteur_id=user_id, destinataire=request.user)
        ).order_by('date_envoi')
        # mark received messages as read
        messages.filter(destinataire=request.user, lu=False).update(lu=True)
        return Response(MessageSerializer(messages, many=True).data)


class UnreadCountView(APIView):
    """GET /api/messages/unread-count/ — number of unread messages."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Message.objects.filter(destinataire=request.user, lu=False).count()
        return Response({'unread_count': count})


class MarkAsReadView(APIView):
    """PATCH /api/messages/<id>/read/ — mark a single received message as read."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            message = Message.objects.get(pk=pk, destinataire=request.user)
        except Message.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        message.lu = True
        message.save(update_fields=['lu'])
        return Response({'detail': 'Message marqué comme lu.'})


class DeleteMessageView(APIView):
    """DELETE /api/messages/<id>/ — delete a message you sent or received."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            message = Message.objects.get(
                pk=pk,
                # user must be either sender or receiver
                **{'expediteur': request.user} if Message.objects.filter(pk=pk, expediteur=request.user).exists()
                else {'destinataire': request.user}
            )
        except Message.DoesNotExist:
            return Response({'detail': 'Not found or not allowed.'}, status=404)
        message.delete()
        return Response({'detail': 'Message supprimé.'}, status=204)