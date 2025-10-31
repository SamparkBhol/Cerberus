from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('ingest/', views.IngestView.as_view(), name='ingest'),
    path('alerts/', views.AlertListView.as_view(), name='alerts'),
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('model/train/', views.ModelTrainingView.as_view(), name='model_train'),
    path('model/status/', views.ModelTrainingView.as_view(), name='model_status'),
]
