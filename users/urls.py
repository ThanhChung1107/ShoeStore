from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),  # Thêm dòng này
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('account/',views.account_detail,name = 'account_detail'),
    path('upload-avartar/',views.upload_avatar,name='upload_avatar'),
    path('upload_profile',views.update_profile,name='update_profile'),
]