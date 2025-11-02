from django.urls import path, include
from rest_framework_nested import routers
from rest_framework_simplejwt.views import TokenVerifyView

from . import views

# Create a router for events
router = routers.DefaultRouter()
router.register(r'events', views.EventViewSet, basename='event')

# Create nested routers for RSVPs and Reviews
events_router = routers.NestedSimpleRouter(router, r'events', lookup='event')
events_router.register(r'rsvps', views.RSVPViewSet, basename='event-rsvps')
events_router.register(r'reviews', views.ReviewViewSet, basename='event-reviews')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    path('', include(events_router.urls)),
]
