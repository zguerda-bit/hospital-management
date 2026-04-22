from django.urls import path
from .views import (
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationUnreadCountView,
)

urlpatterns = [
    path('',               NotificationListView.as_view(),       name='notifications'),
    path('count/',         NotificationUnreadCountView.as_view(), name='notif-count'),
    path('read-all/',      NotificationMarkAllReadView.as_view(), name='notif-read-all'),
    path('<int:pk>/read/', NotificationMarkReadView.as_view(),    name='notif-read'),
]
