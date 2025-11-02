from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the organizer of an event to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the organizer of the event.
        return obj.organizer.user == request.user

class IsInvitedForPrivateEvent(permissions.BasePermission):
    """
    Custom permission to only allow invited users to view private events.
    """
    def has_object_permission(self, request, view, obj):
        # Allow all requests if the event is public
        if obj.is_public:
            return True
            
        # Allow if user is the organizer
        if hasattr(request.user, 'profile') and obj.organizer == request.user.profile:
            return True
            
        # For authenticated users, check if they're invited
        if request.user.is_authenticated:
            return obj.rsvps.filter(user__user=request.user).exists()
            
        return False

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        if hasattr(obj, 'user'):
            return obj.user.user == request.user
        return False
