from rest_framework.permissions import SAFE_METHODS, BasePermission


class CategoryPermission(BasePermission):


    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if obj.user_id is None:
            return False
        return request.user.is_staff or obj.user_id == request.user.id