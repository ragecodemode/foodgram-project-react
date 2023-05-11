from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef

from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.filters import SearchFilter
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.decorators import action

from .serializers import (
    TagSerializers,
    IngredientSerializers,
    ShoppingCartSerializers,
    FollowSerializers,
    RecipeShortSerializer,
    UserSerializers,
    RecipeListCreateSerializer,
    RecipeRetrieveUpdate,
)
from recipes.models import Tag, Ingredient, Favorite, Recipe, ShoppingCart
from users.models import Follow
from api.permissions import IsAuthenticatedOrReadOnly
from api.filters import RecipeFilter

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """
    ViewSet модели Tag.
    Предоставляет только действия list() и retrieve().
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializers
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    ViewSet модели Ingredient.
    Предоставляет только действия list() и retrieve().
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializers
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('name',)


class FavoriteView(APIView):
    """
    APIView класс.
    Предоставляет только действия post() и delete().
    Добавляет и удаляет рецепт из списка избранного.
    """
    
    def post(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        Favorite.objects.create(recipe=recipe, user=request.user)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        get_object_or_404(
            Favorite,
            user=request.user,
            recipe=get_object_or_404(Recipe, id=id)
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(APIView):
    """
    APIView класс.
    Предоставляет только действия post(), delete().
    Добавляет и удаляет рецепт из корзины покупок.
    """
    
    def post(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        ShoppingCart.objects.create(recipe=recipe, user=request.user)
        serializer = ShoppingCartSerializers(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
 
    def delete(self, request):
        get_object_or_404(
            ShoppingCart,
            user=request.user.id,
            recipe=get_object_or_404(Recipe, id=id)
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowView(APIView):
    """
    API класс.
    Предоставляет только действия post(), delete().
    Создания и удаления подписки.
    """

    def post(self, request, id):
        following_user = get_object_or_404(User, id=id)
        if User.objects.filter(user=request.user, following_user=following_user):
            raise ParseError(
                'Вы уже подписаны, подписываться на самого себя нельзя!'
            )
        else:
            Follow.objects.create(follower=request.user, following=following_user)
        serializer = FollowSerializers(following_user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
  
    def delete(self, request, id):
        following_user = get_object_or_404(User, id=id)
        follow = Follow.objects.filter(follower=request.user, following_user=following_user)
        if not follow:
            raise ParseError(
                'Вы не подписаны на этого пользователя!'
            )   
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(ReadOnlyModelViewSet):
    """
    ViewSet модели User.
    Полный набор действий.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializers()
    permission_classes = (AllowAny,)

    @action(('get',), detail=False, permission_classes=(IsAuthenticated,))
    def get_current_user(self, request):
        """
        Запрос к эндпоинту /me/.
        Получения информации о текущем пользователе.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(('post',), detail=False, permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        """
        Запрос к эндпоинту /set_password/.
        Изменения пfроля.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.user.set_password(serializer.data.get('new_password'))
        self.user.save()
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(('get',), detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """
        Запрос к эндпоинту /subscriptions/.
        Получения списка пользователей, 
        на которых подписан пользователь.
        """
        user = request.user
        queryset = user.subscribers.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RecipeViewSet(ModelViewSet):
    """
    ViewSet модели Recipe.
    Поддерживает полный набор действий.
    """
    
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_class = RecipeFilter()
    
    def get_serializer_class(self):
        if self.request.user.is_staff:
            return RecipeListCreateSerializer
        return RecipeRetrieveUpdate
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            user = None
        return (
            Recipe.objects.select_related('author')
            .prefetch_related(
                'tags', 'ingredients', 'recipe',
                'shopping_cart', 'favorite_recipe'
            )
            .annotate(
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user, recipes=OuterRef('id')
                    )
                ),
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=self.request.user, recipe=OuterRef('id')
                    )
                ),
            )
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create_ingredients_file():
        ingredients = ShoppingCart.objects.all()
        file_list = ''
        for ingredient in ingredients:
            file_list += ingredient.name
            file_list += 'n'
        return file_list
    
    def download_ingredients(self, request):
        file_list = self.create_ingredients_file()
        response = HttpResponse(file_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="ingredients.txt"'
        return response