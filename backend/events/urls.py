from django.urls import path
from .views import EventListCreateView, EventDetailView

urlpatterns = [
    path("", EventListCreateView.as_view()),
    path("<int:pk>/", EventDetailView.as_view()),
]
