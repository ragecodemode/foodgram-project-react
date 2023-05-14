from drf_extra_fields.fields import Base64ImageField

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from recipes.models import Tag, Ingredient, Recipe, RecipeIngridient, Favorite, ShoppingCart, LIMITATION

User = get_user_model()


class UserSerializers(serializers.ModelSerializer):
    """
    Сериализатор модели User.
    Вывод информации о пользователях.
    """
    
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        
    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if obj.following.filter(user=user).exists():
            return True
        return False


class TagSerializers(serializers.ModelSerializer):
    """
    Сериализатор модели Tag.
    Вывод информации о тегах.
    """
    
    class Meta:
        model = Tag
        feilds = ('__all__')


class IngredientSerializers(serializers.ModelSerializer):
    """
    Сериализатор модели Ingredient.
    Вывод информации об ингридиентов.
    """
    
    class Meta:
        model = Ingredient
        feilds = ('__all__')


class RecipeIngridientSerializers(serializers.ModelSerializer):
    """
    Сериализатор модели RecipeIngridient.
    Запись о количестве ингредиента.
    """

    id = serializers.IntegerField()
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.FloatField()
    
    class Meta:
        model = RecipeIngridient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Recipe.
    Вывод неполной информации о рецептах.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        
        
class RecipeListCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Recipe.
    Вывод информации о рецептах.
    """

    tags = TagSerializers()
    ingredient = RecipeIngridientSerializers(many=True)
    author = UserSerializers()
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()
    
    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
            'pub_date',
        )

    def get_ingredients(self, obj):
        """
        Метод для получения списка ингредиентов, связанных с рецептом.
        """
        ingredient = RecipeIngridient.objects.filter(recipe=obj)
        return IngredientSerializers(ingredient).data


class RecipeRetrieveUpdate(serializers.ModelSerializer):
    """
    Сериализатор модели Recipe.
    Изменения рецепта.
    """
    
    ingredient = RecipeIngridientSerializers(many=True)
    author = UserSerializers()
    image = Base64ImageField()
    
    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    @staticmethod
    def create_ingredient_list(recipe, ingredients):
        ingredients_list = [
            RecipeIngridient(
                amount=ingredient['amount'],
                ingredient=Ingredient.objects.get(id=ingredient["id"]),
                recipe=recipe
            ) for ingredient in ingredients
        ]
        RecipeIngridient.objects.bulk_create(ingredients_list)
    
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe_new = Recipe.objects.create(**validated_data)
        recipe_new.tags.set(tags)

        self.get_ingredient_list(recipe_new, ingredients)
        
        return recipe_new

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        
        instance.update(**validated_data)
        instance.tags.set(tags)

        self.get_ingredient_list(instance, ingredients)
        
        return instance


class FavoriteSerializers(serializers.ModelSerializer):
    """
    Сериализатор модели Favorite.
    Добавление рецепта в избранное.
    """

    class Meta:
        model = Favorite
        fields = (
            'id',
            'name',
            'iamge',
            'cooking_time',
            'username',
        )
        
    def validate_favorite(self, data):
       user = data['user']
       recipe=data['recipe']
       if user.favorites.filter(recipe).exists():
           raise serializers.ValidateErrore(
               'Рецепт уже в избранном.'
           )
       return data


class ShoppingCartSerializers(serializers.ModelSerializer):
    """
    Сериализатор модели ShoppingCart.
    Вывод информации об списке покупак.
    """
    
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe',)
        
    def validate(self, data):
        user = data['user']
        recipe=data['recipe']
        if user.shopping_cart.filter(recipe).exists():
            raise serializers.ValidateErrore(
                'Рецепт уже есть в списке покупок.'
            )
        return data

    
class FollowSerializers(serializers.ModelSerializer):
    """
    Сериализатор модели Follow.
    Вывод подписок пользователя.
    """

    is_subscribed = serializers.BooleanField(default=True)
    recipe = RecipeShortSerializer(many=True)
    
    class Meta:
        model = User
        feilds = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'recipe'
            'is_subscribed',
            'recipes_count',
        )

class PasswordSerializers(serializers.ModelSerializer):
    """
    Сериализатор, предназначенный для проверки пароля.
    """
    
    new_password = serializers.CharField(max_length=LIMITATION, write_only=True, required=True)
    current_password = serializers.CharField(max_length=LIMITATION, write_only=True, required=True)
    
    def validate_new_password(self, value):
        user = self.context['request'].user
        validate_password(
            password_value=value, password_fields='new_password', user=user
        )
        return value
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Не верный пароль.Введите пороль ещё раз.'
            )
        return value
