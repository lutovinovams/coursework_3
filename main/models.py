from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from config import settings

class Client(models.Model):
    """
    Модель получателя рассылки (клиента).
    """
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=255, verbose_name="Ф. И. О.")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Владелец", null=True, blank=True)

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    """
    Модель сообщения для рассылки.
    """
    title = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Владелец", null=True, blank=True)

    class Meta:
        verbose_name = "Сообщение для рассылки"
        verbose_name_plural = "Сообщения для рассылки"
        ordering = ['title']

    def __str__(self):
        return self.title


class Mailing(models.Model):
    """
    Модель управления рассылками сообщений.
    """
    STATUS_CREATED = 'Создана'
    STATUS_STARTED = 'Запущена'
    STATUS_COMPLETED = 'Завершена'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_STARTED, 'Запущена'),
        (STATUS_COMPLETED, 'Завершена'),
    ]

    start_time = models.DateTimeField(verbose_name="Дата и время начала отправки")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания отправки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name="Статус")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, verbose_name="Сообщение")
    recipients = models.ManyToManyField(Client, verbose_name="Получатели")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Владелец рассылки", null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активна (Менеджер)")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ['-start_time']
        permissions = [
            ("set_active_status", "Can toggle active status of mailing"),
        ]

    def __str__(self):
        return f"Рассылка #{self.pk} ({self.status})"

    def clean(self):
        super().clean()
        now = timezone.now()
        if self.start_time and self.start_time < now and not self.pk:
            raise ValidationError({'start_time': "Дата начала не может быть в прошлом."})
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({'end_time': "Дата окончания должна быть позже даты начала."})

    def update_status(self):
        if not self.is_active:
            return
        now = timezone.now()
        new_status = self.status
        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.STATUS_STARTED
        elif now > self.end_time:
            new_status = self.STATUS_COMPLETED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])


class Log(models.Model):
    """
    Модель логов попыток отправки сообщений.
    """
    STATUS_SUCCESS = 'Успешно'
    STATUS_FAILED = 'Не успешно'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAILED, 'Не успешно'),
    ]

    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Статус")
    server_response = models.TextField(blank=True, null=True, verbose_name="Ответ почтового сервера")
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='logs', verbose_name="Рассылка")

    class Meta:
        verbose_name = "Лог отправки"
        verbose_name_plural = "Логи отправки"
        ordering = ['-attempt_time']

    def __str__(self):
        return f"Попытка #{self.pk} - {self.status} ({self.attempt_time})"
