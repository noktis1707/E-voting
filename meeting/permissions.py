from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """
    Разрешает только администраторам создавать собрания,
    но позволяет всем авторизованным пользователям просматривать их.
    """

    def has_permission(self, request, view):
        # Разрешаем всем авторизованным пользователям читать данные (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        
        # Разрешаем создавать собрания только администраторам (POST, PUT, DELETE)
        return bool(request.user and request.user.is_staff)