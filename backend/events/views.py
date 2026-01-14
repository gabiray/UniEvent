from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from .models import Event, Faculty, Department, Category
from interactions.models import Ticket, Review
from .serializers import (
    EventSerializer,
    EventCreateSerializer,
    FacultySerializer,
    DepartmentSerializer,
    CategorySerializer,
)
from .permissions import IsEventOrganizer

# Project-wide imports
from users.permissions import IsOrganizer

# List and Create Events
class EventListCreateView(generics.ListCreateAPIView):   
    """
    Listare evenimente publicate (GET) și creare evenimente noi (POST).
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['faculty', 'category', 'status', 'start_date']
    search_fields = ["title", "description"]
        
    def get_queryset(self):
        """
        Această metodă decide ce evenimente sunt returnate.
        Pentru lista publică (GET), vrem doar evenimentele PUBLICATE.
        """
        return Event.objects.filter(status='published').annotate(tickets_count=Count('tickets')).order_by('-start_date')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EventCreateSerializer
        return EventSerializer

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsOrganizer()] 
        return [permissions.AllowAny()] 

# Retrieve Faculties, Departments, Categories - DIANA
class FacultyListView(generics.ListAPIView):
    """ Listare facultăți. """

    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    permission_classes = [permissions.AllowAny] 

class DepartmentListView(generics.ListAPIView):
    """ Listare departamente. """

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]

class CategoryListView(generics.ListAPIView):
    """ Listare categorii. """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

# 06.01.2026 List Events Organized by the Authenticated User
class MyEventsListView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user).annotate(tickets_count=Count('tickets')).order_by("-created_at")


# Retrieve, Update, Delete Event
class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vizualizare, editare și ștergere eveniment.
    """
    queryset = Event.objects.annotate(tickets_count=Count('tickets'))

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return EventCreateSerializer
        return EventSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsEventOrganizer()]
        return [permissions.AllowAny()]
    
class EventStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            ev = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            raise NotFound("Eveniment inexistent.")

        # doar organizer-ul eventului poate vedea stats
        if ev.organizer_id != request.user.id:
            raise PermissionDenied("Nu ai acces la statisticile acestui eveniment.")

        # recomandat: stats doar după ce s-a terminat (poți scoate regula dacă vrei live)
        if ev.end_date and ev.end_date > timezone.now():
            return Response(
                {"detail": "Statisticile sunt disponibile după ce evenimentul s-a terminat."},
                status=400,
            )

        tickets_qs = Ticket.objects.filter(event=ev)
        tickets_total = tickets_qs.count()
        checked_in_total = tickets_qs.filter(is_checked_in=True).count()

        checkin_rate = 0
        if tickets_total > 0:
            checkin_rate = checked_in_total / tickets_total

        reviews_qs = Review.objects.filter(event=ev).select_related("user").order_by("-created_at")
        reviews_count = reviews_qs.count()
        avg_rating = reviews_qs.aggregate(avg=Avg("rating"))["avg"] or 0

        breakdown_raw = (
            reviews_qs.values("rating")
            .annotate(c=Count("id"))
            .order_by("rating")
        )
        breakdown = {str(i): 0 for i in range(1, 6)}
        for row in breakdown_raw:
            breakdown[str(row["rating"])] = row["c"]

        latest_reviews = []
        for r in reviews_qs[:10]:
            latest_reviews.append(
                {
                    "id": r.id,
                    "rating": r.rating,
                    "comment": r.comment,
                    "created_at": r.created_at,
                    "user": {
                        "id": r.user.id,
                        "first_name": r.user.first_name,
                        "last_name": r.user.last_name,
                        "email": r.user.email,
                    },
                }
            )

        return Response(
            {
                "event": {
                    "id": ev.id,
                    "title": ev.title,
                    "start_date": ev.start_date,
                    "end_date": ev.end_date,
                },
                "tickets_total": tickets_total,
                "checked_in_total": checked_in_total,
                "checkin_rate": checkin_rate,
                "reviews_count": reviews_count,
                "avg_rating": float(avg_rating),
                "rating_breakdown": breakdown,
                "latest_reviews": latest_reviews,
            }
        )


