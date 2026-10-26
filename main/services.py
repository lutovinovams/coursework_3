from django.core.mail import send_mail
from django.utils import timezone
from config import settings
from main.models import Mailing, Log


def send_mailing_messages(mailing: Mailing) -> bool:
    """
    Проверяет временной интервал и отправляет сообщения, если рассылка не отключена менеджером.
    """
    if not mailing.is_active:
        return False

    now = timezone.now()
    if not (mailing.start_time <= now <= mailing.end_time):
        return False

    recipients_emails = [client.email for client in mailing.recipients.all()]

    for email in recipients_emails:
        try:
            send_mail(
                subject=mailing.message.title,
                message=mailing.message.body,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            Log.objects.create(
                status=Log.STATUS_SUCCESS,
                server_response="Сообщение успешно отправлено.",
                mailing=mailing
            )
        except Exception as e:
            Log.objects.create(
                status=Log.STATUS_FAILED,
                server_response=str(e),
                mailing=mailing
            )

    mailing.update_status()
    return True
