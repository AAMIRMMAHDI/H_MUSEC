from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('manage/<int:user_id>/<str:action>/', views.manage_user, name='manage_user'),
]