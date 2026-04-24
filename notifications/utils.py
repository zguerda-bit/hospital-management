from .models import Notification


def create_notification(user, type_notif, contenu, title='', appointment=None):
    """
    Helper to create a notification from anywhere in the project.

    FIX: views call this with (user=..., type_notif=..., contenu=...)
         so parameters are now named to match those calls.

    Usage:
        from notifications.utils import create_notification

        create_notification(
            user=doctor.user,
            type_notif='RDV',
            contenu='Nouveau rendez-vous...',
        )
    """
    # Map type_notif values from views ('RDV') to model choices
    TYPE_MAP = {
        'RDV':     'REMINDER',
        'RESULT':  'RESULT',
        'MESSAGE': 'MESSAGE',
    }
    notif_type = TYPE_MAP.get(type_notif, 'MESSAGE')

    Notification.objects.create(
        recipient=user,
        notif_type=notif_type,
        title=title or _default_title(notif_type),
        message=contenu,
        appointment=appointment,
    )


def _default_title(notif_type):
    titles = {
        'REMINDER':  'Rappel de rendez-vous',
        'RESULT':    'Résultat disponible',
        'MESSAGE':   'Nouveau message',
        'ADMISSION': 'Admission hospitalière',
        'DISCHARGE': 'Sortie hospitalière',
    }
    return titles.get(notif_type, 'Notification')