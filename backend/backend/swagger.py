# backend/swagger.py
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="UniEvent API",
        default_version="v1",
        description="API pentru gestionarea evenimentelor universitare (Users / Events / Interactions)",
        contact=openapi.Contact(email="dev@unievent.local"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
