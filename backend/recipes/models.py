from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.db import models
from backend.settings import LIMITATION, MIN_VALUE_COOKING_TIME, VALUE_AMOUNT

User = get_user_model()


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        max_length=LIMITATION,
        unique=True,
        verbose_name="Тэг"
    )
    color = models.CharField(
        max_length=LIMITATION,
        unique=True,
        verbose_name="Цвет"
    )
    slug = models.SlugField(unique=True, verbose_name="Слаг тэга",)

    class Meta:
        ordering = ('id', 'name')
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Модель ингридиентов."""

    name = models.CharField(max_length=200, verbose_name="Ингридиент",)
    measurement_unit = models.CharField(
        "Единица измерения", max_length=LIMITATION
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return f"{self.name}, {self.measurement_unit}."


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipe",
        verbose_name="Автор",
    )
    name = models.CharField("Имя рецепта", max_length=LIMITATION)
    image = models.ImageField(
        "Изображение рецепта",
        upload_to="static/recipe"
    )
    text = models.TextField("Описание рецепта")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient"
    )
    cooking_time = models.BigIntegerField(
        "Время готовки",
        validators=(MinValueValidator(MIN_VALUE_COOKING_TIME),),
        error_messages={
            "errors":
            f"Минимальное время готовки {MIN_VALUE_COOKING_TIME} минута."
        },
        default=MIN_VALUE_COOKING_TIME,
    )
    pub_date = models.DateField(auto_now_add=True)
    tags = models.ManyToManyField(
        Tag,
        verbose_name="Теги",
        related_name="recipes"
    )

    class Meta:
        ordering = ('-pub_date', 'id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}'


class RecipeIngredient(models.Model):
    """Модель, связывающая количество ингреядиентов и рецепт."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient'
    )
    amount = models.IntegerField(
        'Количество',
        validators=(MinValueValidator(VALUE_AMOUNT),),
        error_messages={"errors": "Количество не может быть отрицательным!"},
        default=VALUE_AMOUNT,
    )

    class Meta:
        ordering = ('id',)
        verbose_name = "Колличество ингридиентов"
        verbose_name_plural = "Колличество ингридиентов"

    def __str__(self):
        return (
            f"{self.recipe.name} {self.ingredient.name} "
            f"{self.amount} {self.ingredient.measurement_unit}"
        )


class Favorite(models.Model):
    """Модель избранного рецепта пользователя."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Понравившиеся рецепты",
        on_delete=models.CASCADE,
        related_name="favorite"
    )
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="favorite",
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = [["recipe", "user"]]

    def __str__(self):
        return f"{self.recipe}"


class ShoppingCart(models.Model):
    """Модель списка покупок."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепты в списке покупок",
        on_delete=models.CASCADE,
        related_name="shopping_cart"
    )
    user = models.ForeignKey(
        User,
        verbose_name="Владелец списка",
        on_delete=models.CASCADE,
        related_name="shopping_cart"
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Список покупок"
        ordering = ["-recipe"]
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "user"],
                name="shopping_list",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} {self.recipe.name}"
