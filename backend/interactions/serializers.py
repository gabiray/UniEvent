from django.utils import timezone
from rest_framework import serializers

from .models import Ticket, Review, Favorite, Notification

from events.serializers import EventSerializer
from users.serializers import UserSerializer

from events.models import Event

# Serializer for Ticket model
class TicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)
    has_review = serializers.SerializerMethodField()

    def get_has_review(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
          return False
        return Review.objects.filter(user=user, event=obj.event).exists()

    class Meta:
        model = Ticket
        fields = [
            "id", "user", "event", "event_id",
            "qr_code_data", "is_checked_in", "purchased_at",
            "has_review",
        ]
        read_only_fields = ["id", "user", "event", "qr_code_data", "is_checked_in", "purchased_at", "has_review"]

# Serializer for creating Ticket with validations
class TicketCreateSerializer(serializers.ModelSerializer):
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        source="event",
        write_only=True
    )

    class Meta:
        model = Ticket
        fields = ["id", "event_id", "qr_code_data", "is_checked_in", "purchased_at"]
        read_only_fields = ["id", "qr_code_data", "is_checked_in", "purchased_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        event = attrs["event"]

        # 1) doar evenimente publicate
        if getattr(event, "status", None) != "published":
            raise serializers.ValidationError({"event_id": "Evenimentul nu este disponibil pentru înscriere."})

        # 2) doar inainte de start
        if event.start_date and event.start_date <= timezone.now():
            raise serializers.ValidationError({"event_id": "Evenimentul a început deja (nu te mai poți înscrie)."})

        # 3) un singur bilet per user/event
        if Ticket.objects.filter(user=user, event=event).exists():
            raise serializers.ValidationError({"event_id": "Ai deja bilet pentru acest eveniment."})

        # 4) locuri disponibile
        if event.max_participants is not None:
            sold = Ticket.objects.filter(event=event).count()
            if sold >= event.max_participants:
                raise serializers.ValidationError({"event_id": "Nu mai sunt locuri disponibile."})

        return attrs

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