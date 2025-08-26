from django.urls import path
from . import views


urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('create/', views.post_create, name='post_create'),
    path('<int:pk>/', views.post_detail, name='post_detail'),
    # path('<int:pk>/edit/', views.post_edit, name='post_edit'),
    # path('<int:pk>/delete/', views.post_delete, name='post_delete'),
    # path('<int:pk>/like/', views.post_like, name='post_like'),
    # path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    # path('comment/<int:pk>/like/', views.comment_like, name='comment_like'),  # 🆕 Like comment
    # path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
]