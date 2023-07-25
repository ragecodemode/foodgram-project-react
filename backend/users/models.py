from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from backend.settings import LIMITATION


class User(AbstractUser):
    """Модель пользователей."""

    email = models.EmailField(
        'Email',
        max_length=200,
        unique=True
    )
    first_name = models.CharField('Имя', max_length=LIMITATION)
    last_name = models.CharField('Фамилия', max_length=LIMITATION)
    username = models.CharField(
        validators=(UnicodeUsernameValidator(),),
        verbose_name='Имя пользователя',
        max_length=150,
        unique=True,
    )


class Follow(models.Model):
    """Модель подписок пользователя."""

    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follows"
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers"
    )

    def __str__(self) -> str:
        return f'{self.follower} подписан на {self.following}'
