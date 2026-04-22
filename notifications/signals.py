from django.db.models.signals import post_save
from django.dispatch import receiver

from consultations.models import Appointment
from .models import Notification


@receiver(post_save, sender=Appointment)
def appointment_notification(sender, instance, created, **kwargs):
    """
    Automatically fires notifications when an Appointment is created or updated.

    - created=True  → notify the doctor (new pending appointment)
    - CONFIRMED     → notify the parent
    - CANCELLED     → notify the parent
    """

    if created:
        # New appointment → notify the doctor
        Notification.objects.create(
            recipient=instance.doctor.user,
            notif_type='REMINDER',
            title='Nouveau rendez-vous',
            message=(
                f'Nouveau rendez-vous de {instance.patient.first_name} '
                f'{instance.patient.last_name} '
                f'le {instance.date_rdv.strftime("%d/%m/%Y à %H:%M")}.'
            ),
            appointment=instance,
        )
        return

    # Status changes → notify the parent
    if instance.status == 'CONFIRMED':
        already_sent = Notification.objects.filter(
            recipient=instance.patient.parent,
            notif_type='REMINDER',
            appointment=instance,
        ).exists()
        if not already_sent:
            Notification.objects.create(
                recipient=instance.patient.parent,
                notif_type='REMINDER',
                title='Rendez-vous confirmé',
                message=(
                    f'Le rendez-vous de {instance.patient.first_name} '
                    f'avec Dr. {instance.doctor.user.last_name} '
                    f'est confirmé pour le {instance.date_rdv.strftime("%d/%m/%Y à %H:%M")}.'
                ),
                appointment=instance,
            )

    elif instance.status == 'CANCELLED':
        Notification.objects.create(
            recipient=instance.patient.parent,
            notif_type='MESSAGE',
            title='Rendez-vous annulé',
            message=(
                f'Le rendez-vous de {instance.patient.first_name} '
                f'prévu le {instance.date_rdv.strftime("%d/%m/%Y")} a été annulé.'
            ),
            appointment=instance,
        )