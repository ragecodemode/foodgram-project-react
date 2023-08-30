from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.expressions import Exists, OuterRef
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .serializers import (SubscriptionsSerializer, IngredientSerializer,
                          PasswordSerializer, RecipeListSerializer,
                          RecipeCreateUpdateSerializers, FavoriteSerializer,
                          ShoppingCartSerializer, TagSerializer,
                          UserCreateSerializer, UserSerializer,
                          SubscribeListSerializer)
from .filters import RecipeFilter
from api.permissions import IsAuthenticatedOrReadOnly
User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """
    ViewSet модели Tag.
    Предоставляет только действия list() и retrieve().
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    ViewSet модели Ingredient.
    Предоставляет только действия list() и retrieve().
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (SearchFilter,)
    search_fields = ("^name",)
    pagination_class = None


class UserViewSet(UserViewSet):
    """
    ViewSet модели User.
    Полный набор действий.
    """
    serializer_class = UserCreateSerializer()
    permission_classes = (AllowAny,)

    def get_queryset(self):
        queryset = User.objects.annotate(
            is_subscribed=Exists(
                Follow.objects.filter(
                    following=self.request.user, follower=OuterRef('id'))
            )).prefetch_related('follows', 'followers')

        if self.request.query_params.get('is_subscribed'):
            queryset = queryset.filter(is_subscribed=True)
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action == "set_password":
            return PasswordSerializer
        if self.action == "subscriptions":
            return SubscriptionsSerializer
        return UserSerializer

    @action(("get",), detail=False, permission_classes=(IsAuthenticated,))
    def get_current_user(self, request):
        """
        Запрос к эндпоинту /me/.
        Получения информации о текущем пользователе.
        """
        self.get_object = self.request.user
        return self.retrieve(request)

    @action(("post",), detail=False, permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        """
        Запрос к эндпоинту /set_password/.
        Изменения пfроля.
        """
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.data.get("new_password"))
        user.save()
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=("post", "delete",),
        permission_classes=(IsAuthenticated,),
        url_path=r"subscribe"
    )
    def subscribe(self, request, id=None):
        """
        Запрос к эндпоинту /subscribe/.
        Создание и удаление подписки на пользователя.
        """
        current_user = request.user
        following_user = get_object_or_404(User, id=id)
        follow = Follow.objects.filter(
            follower=current_user,
            following=following_user
        ).exists()

        if request.method == "POST":
            if current_user == following_user:
                return Response(
                    {"message": "Вы не можете подписываться на самого себя"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if follow:
                return Response(
                    {"message": "Вы уже подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(
                follower=current_user, following=following_user
            )
            serializer = SubscriptionsSerializer(following_user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            if follow:
                follow = Follow.objects.get(
                    follower=current_user, following=following_user
                ).delete()
            return Response(
                {"message": "Вы отписались от этого пользователя."},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {"message": "Вы не подписаны на этого пользователя!"},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path=r"subscriptions"
    )
    def subscriptions(self, request):
        """
        Запрос к эндпоинту /subscriptions/.
        Получения списка пользователей,
        на которых подписан пользователь.
        """
        user = request.user
        queryset = User.objects.filter(followers__id=user.id)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(ModelViewSet):
    """
    ViewSet модели Recipe.
    Поддерживает полный набор действий.
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        tags = self.request.query_params.getlist('tags')
        user_id = self.request.user.id
        queryset = Recipe.objects.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    user=user_id, recipe=OuterRef('pk'))),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=user_id, recipe=OuterRef('pk')))
        ).select_related('author').prefetch_related('tags', 'ingredients')

        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        if self.request.query_params.get('is_favorited'):
            queryset = queryset.filter(is_favorited=True)

        if self.request.query_params.get('is_in_shopping_cart'):
            queryset = queryset.filter(is_in_shopping_cart=True)

        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeListSerializer
        return RecipeCreateUpdateSerializers

    @action(
        detail=True,
        methods=("post", "delete",),
        permission_classes=(IsAuthenticated,),
        url_path=r"shopping_cart"
    )
    def shopping_cart(self, request, pk=None):
        """
        Запрос к эндпоинту /shopping_cart/.
        Добавление рецепта в корзину и удаление.
        """
        recipes = get_object_or_404(Recipe, pk=pk)
        cart = ShoppingCart.objects.filter(
            recipe=recipes, user=request.user
        ).exists()

        if request.method == "POST":
            if cart:
                return Response(
                    {"message": "Рецепт уже добавлен в корзину!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_cart = ShoppingCart.objects.create(
                recipe=recipes, user_id=request.user.id
            )
            serializer = ShoppingCartSerializer(shopping_cart)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            if not cart:
                return Response(
                    {"message": "Рецепт нет в корзине!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.filter(
                recipe=recipes, user_id=request.user.id
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=("post", "delete",),
        permission_classes=(IsAuthenticated,),
        url_path=r"favorite"
    )
    def favorite(self, request, pk=None):
        """
        Запрос к эндпоинту /favorite/.
        Добавление рецепта в избранное и удаление.
        """
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = Favorite.objects.filter(
            recipe=recipe, user=request.user
        ).exists()

        if request.method == "POST":
            if favorite:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            favorite_add = Favorite.objects.create(
                recipe=recipe, user_id=request.user.id
            )
            serializer = FavoriteSerializer(favorite_add)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            if favorite:
                favorite = Favorite.objects.get(
                    recipe=recipe, user=request.user
                ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def create_ingredients_file(self, request):
        ingredients = (
            RecipeIngredient.objects.all()
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(amount=Sum("amount"))
        )
        shopping_cart = []
        for ingredient in ingredients:
            shopping_cart.append(
                f'{ingredient["ingredient__name"]}'
                f'{ingredient["amount"]} '
                f'{ingredient["ingredient__measurement_unit"]}\n'
            )
        return shopping_cart

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path=r"download_shopping_cart"
    )
    def download_shopping_cart(self, request):
        try:
            ingredients = self.create_ingredients_file(request)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        content = self.create_ingredients_file(ingredients)
        response = FileResponse(content, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="ingredients.txt"'
        )
        return response
