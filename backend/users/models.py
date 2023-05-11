from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель пользователей."""

    email = models.EmailField(
        'Email',
        max_length=200,
        unique=True
    )
    first_name = models.CharField('Имя', max_length=200)
    last_name = models.CharField('Фамилия', max_length=200)


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
