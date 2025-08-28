from django.urls import path
from . import views


urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('<int:pk>/', views.post_detail, name='post_detail'),
    path('post/create-ajax/', views.post_create_ajax, name='post_create_ajax'), 
    # path('<int:pk>/edit/', views.post_edit, name='post_edit'),
    # path('<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('post/<int:pk>/like/', views.post_like, name='post_like'),
    path('<int:pk>/comment/', views.post_comment, name='add_comment'),
    path('post/<int:pk>/comment/<int:parent_id>/reply/', views.post_comment_reply, name='post_comment_reply'),
    path('comment/<int:pk>/like/', views.comment_like, name='comment_like'),
]