from django.urls import path
from .views import (
    InboxView, SentView, SendMessageView,
    ConversationView, UnreadCountView,
    MarkAsReadView, DeleteMessageView,
)

urlpatterns = [
    path('inbox/',                      InboxView.as_view(),        name='inbox'),
    path('sent/',                       SentView.as_view(),         name='sent'),
    path('send/',                       SendMessageView.as_view(),  name='send-message'),
    path('unread-count/',               UnreadCountView.as_view(),  name='msg-unread-count'),
    path('conversation/<int:user_id>/', ConversationView.as_view(), name='conversation'),
    path('<int:pk>/read/',              MarkAsReadView.as_view(),   name='msg-mark-read'),
    path('<int:pk>/',                   DeleteMessageView.as_view(),name='msg-delete'),
]