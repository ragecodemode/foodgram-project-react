from rest_framework import permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class IsAuthenticatedOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Чтения любым пользователям.
    Создания, изменения, удаления только автору и администратору.
    """

    def has_object_permission(self, request, view, obj):
        """
        Проверяет, имеет ли пользователь доступ к объекту.
        """
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff:
            return True

        return request.user == obj.author
