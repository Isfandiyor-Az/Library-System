from rest_framework.permissions import BasePermission

'''class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'ADMIN'

class IsOperator(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'OPERATOR'

class IsUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'USER'
'''

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')

class IsOperator(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'OPERATOR')

class IsUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'USER')
