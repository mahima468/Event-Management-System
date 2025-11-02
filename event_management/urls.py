"""
URL configuration for event_management project.

Includes API endpoints for events, RSVPs, and reviews with JWT authentication.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework_simplejwt.views import TokenVerifyView
from events.auth_views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    UserRegistrationView
)

urlpatterns = [
    # Root URL redirects to events list
    path('', RedirectView.as_view(url='/api/events/')),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('api/register/', UserRegistrationView.as_view(), name='register'),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # API endpoints
    path('api/', include('events.urls')),
]
