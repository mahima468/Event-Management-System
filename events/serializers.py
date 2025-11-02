from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Event, RSVP, Review
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'full_name', 'bio', 'location', 'profile_picture']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data.get('email', ''),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', '')
        )
        profile = UserProfile.objects.create(user=user, **validated_data)
        return profile
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        
        # Update user fields
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

class EventSerializer(serializers.ModelSerializer):
    organizer = UserProfileSerializer(read_only=True)
    rsvp_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'organizer', 'location',
            'start_time', 'end_time', 'is_public', 'created_at', 'updated_at',
            'rsvp_count', 'average_rating'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'organizer']
    
    def get_rsvp_count(self, obj):
        return obj.rsvps.count()
    
    def get_average_rating(self, obj):
        from django.db.models import Avg
        return obj.reviews.aggregate(Avg('rating'))['rating__avg']
    
    def create(self, validated_data):
        # The organizer will be set to the current user's profile
        user = self.context['request'].user
        profile = user.profile
        return Event.objects.create(organizer=profile, **validated_data)

class RSVPSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    
    class Meta:
        model = RSVP
        fields = ['id', 'event', 'user', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def create(self, validated_data):
        # The user will be set to the current user's profile
        user = self.context['request'].user
        profile = user.profile
        event = validated_data['event']
        
        # Check if RSVP already exists
        rsvp, created = RSVP.objects.get_or_create(
            user=profile,
            event=event,
            defaults={'status': validated_data['status']}
        )
        
        if not created:
            # Update existing RSVP
            rsvp.status = validated_data['status']
            rsvp.save()
        
        return rsvp

class ReviewSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    
    class Meta:
        model = Review
        fields = ['id', 'event', 'user', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def create(self, validated_data):
        # The user will be set to the current user's profile
        user = self.context['request'].user
        profile = user.profile
        event = validated_data['event']
        
        # Check if review already exists
        review, created = Review.objects.get_or_create(
            user=profile,
            event=event,
            defaults={
                'rating': validated_data['rating'],
                'comment': validated_data.get('comment', '')
            }
        )
        
        if not created:
            # Update existing review
            review.rating = validated_data['rating']
            review.comment = validated_data.get('comment', review.comment)
            review.save()
        
        return review

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        
        # Add extra responses here
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['user'] = UserSerializer(self.user).data
        
        return data
