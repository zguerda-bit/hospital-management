from .models import Notification


def create_notification(user, notif_type, title, message, appointment=None):
    """
    Helper to create a notification from anywhere in the project.

    Usage:
        from notifications.utils import create_notification

        create_notification(
            user=some_user,
            notif_type='REMINDER',
            title='Rappel',
            message='Votre rendez-vous est demain.',
            appointment=appointment_instance,  # optional
        )
    """
    Notification.objects.create(
        recipient=user,
        notif_type=notif_type,
        title=title,
        message=message,
        appointment=appointment,
    )