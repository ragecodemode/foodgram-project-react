from rest_framework import permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class IsAuthenticatedOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Чтения любым пользователям.
    Создания, изменения, удаления только автору и администратору.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or request.user == obj.author
