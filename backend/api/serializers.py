from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (LIMITATION, Favorite, Ingredient, Recipe,
                            RecipeIngridient, ShoppingCart, Tag)
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
        feilds = ('id', 'name', 'measurement_unit')


class RecipeIngridientSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели RecipeIngridient.
    Запись о количестве ингредиента.
    """

    id = serializers.IntegerField()
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )
    amount = serializers.FloatField()

    class Meta:
        model = RecipeIngridient
        fields = (
            "id",
            "name",
            "measurement_unit",
            "amount",
        )


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
            "ingredients",
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
    Изменения рецепта.
    """

    ingredient = RecipeIngridientSerializer(many=True)
    author = UserSerializer()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    @staticmethod
    def create_ingredient_list(recipe, ingredients):
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
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe_new = Recipe.objects.create(**validated_data)
        recipe_new.tags.set(tags)

        self.get_ingredient_list(recipe_new, ingredients)

        return recipe_new

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")

        instance.update(**validated_data)
        instance.tags.set(tags)

        self.get_ingredient_list(instance, ingredients)

        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Favorite.
    Добавление рецепта в избранное.
    """

    class Meta:
        model = Favorite
        fields = (
            "id",
            "name",
            "iamge",
            "cooking_time",
            "username",
        )

    def validate_favorite(self, data):
        user = data["user"]
        recipe = data["recipe"]
        if user.favorites.filter(recipe).exists():
            raise serializers.ValidateErrore("Рецепт уже в избранном.")
        return data


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


class SubscriptionsSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Follow.
    Вывод подписок пользователя.
    """

    is_subscribed = serializers.BooleanField(default=True)
    recipe = RecipeShortSerializer(many=True)

    class Meta:
        model = User
        feilds = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "recipe" "is_subscribed",
            "recipes_count",
        )

    def get_recipes_count(self, obj):
        """
        Метод для получения количества рецептов,
        созданных пользователем.
        """
        return obj.recipes.count()

    def get_recipes(self, obj):
        """
        Метод для получения списка рецептов,
        связанных с автором.
        """
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        queryset = Recipe.objects.filter(author=obj.author)
        if limit is not None:
            queryset = Recipe.objects.filter(author=obj.author)[: int(limit)]

        return RecipeShortSerializer(queryset, many=True).data


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


class FollowSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели User.
    Предназначен для вывода информации о пользователях и их рецептах,
    на которых подписан текущий авторизованный пользователь.
    """

    is_subscribed = serializers.BooleanField(default=True)
    recipes = RecipeShortSerializer(many=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
        )
