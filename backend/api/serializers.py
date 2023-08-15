from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (LIMITATION, Favorite, Ingredient, Recipe,
                            RecipeIngridient, ShoppingCart, Tag)
from users.models import Follow

from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели User.
    Вывод информации о пользователях.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        return (
            user.is_authenticated and user.follows.filter(
                following=obj
            ).exists()
        ) or False


class UserCreateSerializer(UserCreateSerializer):
    """
    Сериализатор модели User.
    Предназначен для регистрации пользователей.
    """

    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Tag.
    Вывод информации о тегах.
    """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Ingredient.
    Вывод информации об ингридиентов.
    """

    class Meta:
        model = Ingredient
        fields = "__all__"


class RecipeIngridientSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели RecipeIngridient.
    Запись о количестве ингредиента.
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngridient
        fields = ('id', 'name', 'measurement_unit', 'quantity')


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Recipe.
    Вывод неполной информации о рецептах.
    """

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )


class RecipeListCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Recipe.
    Вывод информации о рецептах.
    """

    tags = TagSerializer()
    ingredient = RecipeIngridientSerializer(many=True)
    author = UserSerializer()
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "ingredient",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
            "pub_date",
        )

    def get_ingredients(self, obj):
        """
        Метод для получения списка ингредиентов, связанных с рецептом.
        """
        ingredient = RecipeIngridient.objects.filter(recipe=obj)
        return IngredientSerializer(ingredient).data


class RecipeRetrieveUpdate(serializers.ModelSerializer):
    """
    Сериализатор модели Recipe.
    Создание и изменения рецепта.
    """
    ingredient = RecipeIngridientSerializer(many=True, required=False)
    author = UserSerializer(required=False)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = "__all__"

    @staticmethod
    def create_ingredient_list(recipe, ingredients):
        """
        Метод для создания
        или обновления списка ингредиентов для рецепта.
        """

        ingredients_list = [
            RecipeIngridient(
                amount=ingredient["amount"],
                ingredient=Ingredient.objects.get(id=ingredient["id"]),
                recipe=recipe,
            )
            for ingredient in ingredients
        ]
        RecipeIngridient.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredient", [])
        tags = validated_data.pop("tags", [])

        recipe_new = Recipe.objects.create(**validated_data)

        recipe_new.tags.set(tags)

        self.create_ingredient_list(recipe_new, ingredients)

        return recipe_new

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredient")
        tags = validated_data.pop("tags")

        instance.update(**validated_data)
        instance.tags.set(tags)

        self.create_ingredient_list(instance, ingredients)

        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Favorite.
    Добавление рецепта в избранное.
    """

    class Meta:
        model = Favorite
        fields = ("user", "recipe")

    def validate_favorite(self, data):
        """
        Метод  проверяет,
        находится ли рецепт уже в избранном у пользователя.
        """

        user = data["user"]
        recipe = data["recipe"]
        if user.favorites.filter(recipe).exists():
            raise serializers.ValidationError("Рецепт уже в избранном.")
        return data

    def to_representation(self, instance):
        """
        Метод используется для преобразования
        сериализованных данных обратно в словарь.
        """

        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели ShoppingCart.
    Вывод информации об списке покупак.
    """

    class Meta:
        model = ShoppingCart
        fields = (
            "user",
            "recipe",
        )

    def validate(self, data):
        user = data["user"]
        recipe = data["recipe"]
        if user.shopping_cart.filter(recipe).exists():
            raise serializers.ValidateErrore(
                "Рецепт уже есть в списке покупок."
            )
        return data

    def to_representation(self, instance):
        """
        Метод используется для преобразования
        сериализованных данных обратно в словарь.
        """

        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class SubscriptionsSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели User.
    Вывод подписок пользователя.
    """
    follower = serializers.ReadOnlyField(source='user')
    following = serializers.ReadOnlyField(source='user')

    class Meta:
        model = Follow
        fields = (
            "id",
            "follower",
            "following"
        )


class PasswordSerializer(serializers.ModelSerializer):
    """
    Сериализатор, предназначенный для проверки пароля.
    """

    new_password = serializers.CharField(
        max_length=LIMITATION, write_only=True, required=True
    )
    current_password = serializers.CharField(
        max_length=LIMITATION, write_only=True, required=True
    )

    class Meta:
        model = User
        fields = ('new_password', 'current_password')

    def validate_new_password(self, value):
        user = self.context["request"].user
        validate_password(value, user=user)
        return value

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Не верный пароль. Введите пороль ещё раз."
            )
        return value
