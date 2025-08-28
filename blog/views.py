from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Post, PostLike, Comment, CommentLike
from .forms import PostForm, CommentForm
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count

from django.db.models import Sum
from django.db.models.functions import Coalesce
from products.models import Product

def post_list(request):
    current_user = None 
    if request.user.is_authenticated:
        current_user = request.user
    # Lấy danh sách bài viết
    posts = Post.objects.filter(published=True)\
                       .select_related('author')\
                       .prefetch_related('comments', 'comments__user', 'likes')\
                       .annotate(
                           total_likes=Count('likes'),
                           total_comments=Count('comments')
                       )\
                       .order_by('-created_at')
    #lấy danh sách các user đã like bài viết
    user_like_posts = {}
    if request.user.is_authenticated:
        user_like_posts = {
            like.post_id: True
            for like in PostLike.objects.filter(
                user = request.user,
                post__in = posts
            )
        }
    # Lấy danh sách sản phẩm bán chạy
    products_with_sales = Product.objects.annotate(
        total_sold=Coalesce(Sum('order_items__quantity'), 0)
    )
    best_selling_products = products_with_sales.filter(
        total_sold__gt=0
    ).order_by('-total_sold')[:4]

    if best_selling_products.count() < 4:
        newest_products = Product.objects.exclude(
            id__in=[p.id for p in best_selling_products]
        ).order_by('-created_at')[:4 - best_selling_products.count()]
        for product in newest_products:
            product.total_sold = 0
        best_selling_products = list(best_selling_products) + list(newest_products)

    return render(request, 'post_list.html', {
        'posts': posts,
        'best_selling_products': best_selling_products,
        'user_liked_posts': user_like_posts,
        'current_user': current_user,
    })

#chi tiết bài đăng
def post_detail(request,pk):
    post = get_object_or_404(Post,pk=pk, published=True)
    comments = post.comments.all().order_by('-created_at')
    comment_form = CommentForm()

    #kiểm tra user đã like bài viết chưa
    user_liked_post = False
    user_comment_likes = {} #lưu trạng thái like comment của user

    if request.user.is_authenticated:
        user_liked_post = PostLike.objects.filter(post=post, user=request.user).exists()

        #lấy tất cả comment likes của user
        user_comment_likes = {
            like.comment_id: True
            for like in CommentLike.objects.filter(
                comment__in= comments,
                user=request.user
            )
        }
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'user_liked_post': user_liked_post,
        'user_comment_likes': user_comment_likes
    })

@login_required
@require_POST
@csrf_exempt  # Tạm thời vô hiệu hóa CSRF để test, sau này nên xử lý đúng cách
def post_create_ajax(request):
    """Tạo bài viết mới qua AJAX"""
    try:
        # Lấy dữ liệu từ AJAX request
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')
        
        if not content and not image:
            return JsonResponse({
                'success': False,
                'message': 'Nội dung hoặc ảnh là bắt buộc'
            })
        
        # Tạo bài viết mới
        post = Post(
            author=request.user,
            content=content,
            image=image,
            published=True
        )
        post.save()
        
        # Trả về response JSON
        return JsonResponse({
            'success': True,
            'message': 'Bài viết đã được đăng thành công!',
            'post_id': post.id,
            'post_content': post.content,
            'post_image_url': post.image.url if post.image else None,
            'author_name': post.author.username,
            'created_at': post.created_at.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Có lỗi xảy ra: {str(e)}'
        })
    
@login_required
@require_POST
@csrf_exempt
def post_like(request,pk):
    try:
        post = get_object_or_404(Post,pk=pk)
        like, create = PostLike.objects.get_or_create(
            post = post,
            user = request.user
        )
        if not create:
            like.delete()
            liked = False
        else:
            liked = True
        return JsonResponse({
            'success': True,
            'liked': liked,
            'total_likes': post.likes.count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

import json
@login_required
@require_POST
@csrf_exempt
def post_comment(request, pk):
    try:
        post = get_object_or_404(Post, pk=pk)
        
        # Kiểm tra content-type
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            content = data.get('content', '').strip()
        else:
            # Fallback cho form data thông thường
            content = request.POST.get('content', '').strip()

        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Nội dung comment không được để trống'
            })
            
        comment = Comment.objects.create(
            post=post,
            user=request.user,
            content=content
        )

        return JsonResponse({
            'success': True,
            'comment_id': comment.id,
            'user_name': request.user.username,
            'user_avatar': request.user.avatar.url if request.user.avatar else '',
            'content': content,
            'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
@login_required
@require_POST
@csrf_exempt
def post_comment_reply(request, pk, parent_id):
    """Trả lời comment"""
    try:
        post = get_object_or_404(Post, pk=pk)
        parent_comment = get_object_or_404(Comment, pk=parent_id, post=post)
        
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            content = data.get('content', '').strip()
        else:
            content = request.POST.get('content', '').strip()

        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Nội dung comment không được để trống'
            })
            
        comment = Comment.objects.create(
            post=post,
            user=request.user,
            parent=parent_comment,
            content=content
        )

        return JsonResponse({
            'success': True,
            'comment_id': comment.id,
            'user_name': request.user.username,
            'user_avatar': request.user.avatar.url if request.user.avatar else '',
            'content': content,
            'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M'),
            'parent_id': parent_comment.id,
            'is_reply': True
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@require_POST
@csrf_exempt
def comment_like(request, pk):
    """Like/unlike comment"""
    try:
        comment = get_object_or_404(Comment, pk=pk)
        like, created = CommentLike.objects.get_or_create(
            comment=comment,
            user=request.user
        )
        
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
            
        return JsonResponse({
            'success': True,
            'liked': liked,
            'total_likes': comment.likes.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })