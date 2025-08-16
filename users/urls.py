from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),  # Thêm dòng này
    path('login/', views.custom_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html',
             next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
]