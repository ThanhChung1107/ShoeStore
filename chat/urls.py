from django.urls import path
from . import views

urlpatterns = [
    path('room/<str:room_name>/', views.chat_room, name='chat_room'),
    path('admin/dashboard/', views.admin_chat_dashboard, name='admin_chat_dashboard'),
    path('api/create-room/', views.create_chat_room, name='create_chat_room'),
]