from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="Referral API",
        default_version='v1',
        description="Test project for Hammer Systems",
        #terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="advixum@gmail.com"),
        license=openapi.License(name="AGPL-3.0 license"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

app_name = 'api'

urlpatterns = [
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('verify/', views.VerifyView.as_view(), name='verify'),
    path('data/', views.DataView.as_view(), name='data'),
]