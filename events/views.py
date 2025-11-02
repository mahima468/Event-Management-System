from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Event, RSVP, Review, UserProfile
from .serializers import EventSerializer, RSVPSerializer, ReviewSerializer
from .permissions import IsOrganizerOrReadOnly, IsInvitedForPrivateEvent, IsOwnerOrReadOnly

class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing events.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOrganizerOrReadOnly, IsInvitedForPrivateEvent]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EventSerializer
        return EventSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # For unauthenticated users or list view, only show public events
        if not self.request.user.is_authenticated or self.action == 'list':
            return queryset.filter(is_public=True)
            
        # For authenticated users, show public events + their private events
        return queryset.filter(
            Q(is_public=True) |
            Q(rsvps__user__user=self.request.user) |
            Q(organizer__user=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        # Automatically set the organizer to the current user's profile
        user_profile = self.request.user.profile
        serializer.save(organizer=user_profile)

    @action(detail=True, methods=['get', 'post'], permission_classes=[IsAuthenticated])
    def rsvp(self, request, pk=None):
        """
        Handle RSVP creation and updates.
        POST /events/{id}/rsvp/ {'status': 'going'|'maybe'|'not_going'}
        """
        event = self.get_object()
        user_profile = request.user.profile
        
        if request.method == 'POST':
            # Check if RSVP already exists
            rsvp, created = RSVP.objects.get_or_create(
                event=event,
                user=user_profile,
                defaults={'status': request.data.get('status', 'going')}
            )
            
            if not created:
                # Update existing RSVP
                serializer = RSVPSerializer(rsvp, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = RSVPSerializer(rsvp)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # GET request - return the user's RSVP status if it exists
        try:
            rsvp = RSVP.objects.get(event=event, user=user_profile)
            serializer = RSVPSerializer(rsvp)
            return Response(serializer.data)
        except RSVP.DoesNotExist:
            return Response({'status': 'not_going'})

class RSVPViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for managing RSVPs.
    Accessible at /events/{event_id}/rsvps/
    """
    serializer_class = RSVPSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        event_id = self.kwargs.get('event_id')
        return RSVP.objects.filter(event_id=event_id)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        event = get_object_or_404(Event, id=self.kwargs['event_id'])
        serializer.save(user=self.request.user.profile, event=event)

class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    Accessible at /events/{event_id}/reviews/
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        event_id = self.kwargs.get('event_id')
        return Review.objects.filter(event_id=event_id)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
        
    def perform_create(self, serializer):
        event = get_object_or_404(Event, id=self.kwargs['event_id'])
        serializer.save(user=self.request.user.profile, event=event)
        
    def create(self, request, *args, **kwargs):
        # Check if user has already reviewed this event
        event_id = self.kwargs.get('event_id')
        if Review.objects.filter(event_id=event_id, user=request.user.profile).exists():
            return Response(
                {"detail": "You have already reviewed this event."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)
