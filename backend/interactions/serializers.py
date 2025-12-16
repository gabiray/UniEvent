from rest_framework import serializers
from .models import Ticket, Review, Favorite, Notification
from events.serializers import EventSerializer
from users.serializers import UserSerializer

# Serializer for Ticket model
class TicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)

    event_id = serializers.PrimaryKeyRelatedField(
        queryset=EventSerializer.Meta.model.objects.all(),
        source="event",
        write_only=True
    )

    class Meta:
        model = Ticket
        fields = [
            "id", "user", "event", "event_id",
            "qr_code_data", "is_checked_in", "purchased_at"
        ]
        read_only_fields = ["id", "user", "event", "qr_code_data", "is_checked_in", "purchased_at"]

# Serializer for Review model
class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)

    event_id = serializers.PrimaryKeyRelatedField(
        queryset=EventSerializer.Meta.model.objects.all(),
        source="event",
        write_only=True
    )

    class Meta:
        model = Review
        fields = ["id", "user", "event", "event_id", "rating", "comment", "created_at"]
        read_only_fields = ["id", "user", "event", "created_at"]

# Serializer for Favorite model
class FavoriteSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)

    event_id = serializers.PrimaryKeyRelatedField(
        queryset=EventSerializer.Meta.model.objects.all(),
        source="event",
        write_only=True
    )

    class Meta:
        model = Favorite
        fields = ["id", "user", "event", "event_id", "added_at"]
        read_only_fields = ["id", "user", "event", "added_at"]

# Serializer for Notification model
class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "user", "title", "message", "is_read", "created_at"]
        read_only_fields = ["id", "user", "created_at"]