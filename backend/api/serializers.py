from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField

from rest_framework.validators import UniqueTogetherValidator
from rest_framework.serializers import (
    PrimaryKeyRelatedField, ReadOnlyField, ImageField, IntegerField
)
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
        fields = "__all__"


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
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """
    Вложенный сериализатор для RecipeRetrieveUpdate.
    Обеспечивает работу с моделью RecipeIngredien.
    """

    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngridient
        fields = (
            "id",
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

    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

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

    def get_recipe(self, obj):
        recipe = RecipeIngridient.objects.filter(recipe=obj)
        return RecipeIngridientSerializer(recipe, many=True).data

    def get_ingredients(self, obj):
        ingredients = []
        for ingredient in obj.ingredients.all():
            ingredient_json = {
                "id": ingredient.id,
                "name": ingredient.name,
                "measurement_unit": ingredient.measurement_unit,
            }
            ingredients.append(ingredient_json)
        return ingredients

    def get_is_favorited(self, obj):
        """
        Проверка - находится ли рецепт в избранном.
        """
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """
        Проверка - находится ли рецепт в списке  покупок.
        """
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=request.user, recipe_id=obj
        ).exists()


class RecipeRetrieveUpdate(serializers.ModelSerializer):
    """
    Сериализатор модели Recipe.
    Создание и изменения рецепта.
    """
    ingredients = RecipeIngredientWriteSerializer(many=True)
    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    tags = PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get('request')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=request.user, **validated_data)

        for tag in tags:
            recipe.tags.add(tag)

        for ingredient in ingredients:
            amount = ingredient.get('amount')
            RecipeIngridient.objects.create(
                amount=amount,
                ingredient=ingredient['id'],
                recipe=recipe
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")

        if tags is not None:
            instance.tags.set(tags)

        for ingredient in ingredients:
            amount = ingredient.get('amount')
            RecipeIngridient.objects.update_or_create(
                recipe=instance,
                ingredient=ingredient['id'],
                amount=amount
            )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeListCreateSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Favorite.
    Добавление рецепта в избранное.
    """
    id = PrimaryKeyRelatedField(source="recipe", read_only=True)
    name = ReadOnlyField(source="recipe.name")
    image = ImageField(source="recipe.image", read_only=True)
    cooking_time = IntegerField(source="recipe.cooking_time", read_only=True)

    class Meta:
        model = Favorite
        fields = (
            "id", "name", "image", "cooking_time",
        )

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
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели ShoppingCart.
    Вывод информации об списке покупак.
    """

    id = PrimaryKeyRelatedField(source="recipe", read_only=True)
    name = ReadOnlyField(source="recipe.name")
    image = ImageField(source="recipe.image", read_only=True)
    cooking_time = IntegerField(source="recipe.cooking_time", read_only=True)

    class Meta:
        model = ShoppingCart
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
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
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class SubscriptionsSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели User.
    Вывод списка подписок пользователя.
    """
    is_subscribed = serializers.SerializerMethodField()
    recipe = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipe',
            'recipes_count'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            follower=request.user, following=obj).exists()

    def get_recipe(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipe = obj.recipe.filter(author=obj)
        seriailizer = RecipeShortSerializer(recipe, many=True)
        return seriailizer.data

    def get_recipes_count(self, obj):
        return obj.recipe.count()


class SubscribeListSerializer(serializers.ModelSerializer):
    """ Сериализатор подписок. """

    class Meta:
        model = Follow
        fileds = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=['user', 'author'],
            )
        ]

    def to_representation(self, instance):
        return SubscriptionsSerializer(instance.author, context={
            'request': self.context.get('request')
        }).data


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
