from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator

from backend.settings import LIMITATION, MIN_VALUE_COOKING_TIME, VALUE_AMOUNT

User = get_user_model()

MIN_VALUE_COOKING_TIME = 1

VALUE_AMOUNT = 1

LIMITATION = 200


class Tag(models.Model):
    """Модель тегов рецептов."""

    name = models.CharField(max_length=LIMITATION, unique=True)
    color = models.CharField(max_length=LIMITATION, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Модель ингридиентов."""

    name = models.CharField(max_length=200)
    measurement_unit = models.CharField('Единица измерения', max_length=LIMITATION)

    def __str__(self) -> str:
        return f'{self.name}, {self.measurement_unit}.'


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор'
    )
    name = models.CharField('Имя рецепта', max_length=LIMITATION)
    image = models.ImageField(
        'Изображение рецепта',
        upload_to='static/recipe',
        blank=True,
        null=True,
    )
    text = models.TextField('Описание рецепта')
    ingredients = models.ManyToManyField(Ingredient, 'Ингридиенты', verbose_name='ingredients')
    cooking_time = models.BigIntegerField(
        'Время готовки', 
        validators=(MinValueValidator(MIN_VALUE_COOKING_TIME),),
        error_messages={
            'errors': f'Минимальное время готовки {MIN_VALUE_COOKING_TIME} минута.'
        },
        default=MIN_VALUE_COOKING_TIME,
    )
    pub_date = models.DateField(auto_now_add=True)
    tags = models.ManyToManyField(Tag, verbose_name='Теги')

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = 'Рецепты'
        ordering = ('-pub_date',)


class RecipeIngridient(models.Model):
    """Моедль, связывающая количество ингридиентов и рецепт."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='Recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='Ingredients'
    )
    amount = models.FloatField(
        validators=(MinValueValidator(VALUE_AMOUNT),),
        error_messages={
            'errorse': 'Колличество не должно быть отрицательным.'
        },
        default=VALUE_AMOUNT,
    )

    class Meta:
        verbose_name = 'Колличество ингридиентов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='value_amount',
            ),
        ]


class Favorite(models.Model):
    """Модель избранного рецепта пользователя."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite'
    )

    def __str__(self) -> str:
        return f'{self.user} :: {self.recipe}'

    class Meta:
        verbose_name = 'Колличество ингридиентов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='favorite_recipe',
            ),
        ]
 

class ShoppingCart(models.Model):
    """Модель списка покупок."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='Рецепт'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='Пользователь'
    )

    def __str__(self) -> str:
        return f'{self.user} {self.recipe.name}'

    class Meta:
        verbose_name = 'Список покупок'
        ordering = ['-recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='shopping_list',
            ),
        ]
