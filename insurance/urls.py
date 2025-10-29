from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from insurance.views.RegisterView import RegisterView

schema_view = get_schema_view(
    openapi.Info(
        title="Insurance Company API",
        default_version='v1',
        description="🚀 REST API для страхових полісів, клієнтів, оплат і заявок",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@insurance.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny,],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/', include('insurance.api_urls')),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Swagger UI
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),

    # Redoc (альтернатива, більш стриманий стиль)
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
]
