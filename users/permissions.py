from rest_framework import permissions


class IsAdminOrTeacher(permissions.BasePermission):
    """
    Custom permission to only allow admin or teacher users to access certain views.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow admin and teacher users
        return request.user.role in ['ADMIN', 'TEACHER']


class IsAdminOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access certain views.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow only admin users
        return request.user.role == 'ADMIN'


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow admin users
        if request.user.role == 'ADMIN':
            return True
        
        # Allow owners
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False
