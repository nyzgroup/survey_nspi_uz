from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MessageToResponsible
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=MessageToResponsible)
def notify_responsible_person(sender, instance, created, **kwargs):
    if created and instance.responsible_person and instance.responsible_person.email:
        send_mail(
            subject=f"Yangi murojaat: {instance.subject}",
            message=f"Sizga yangi murojaat yuborildi.\n\nMavzu: {instance.subject}\nTalaba: {instance.student}\n\n{instance.content}",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[instance.responsible_person.email],
            fail_silently=True,
        )
