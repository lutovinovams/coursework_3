from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Кастомная модель пользователя с полем для верификации email.
    """
    email = models.EmailField(unique=True, verbose_name="Email")
    verification_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Код верификации")
    is_verified = models.BooleanField(default=False, verbose_name="Почта подтверждена")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email
