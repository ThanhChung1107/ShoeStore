from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Post, PostLike, Comment, CommentLike
from .forms import PostForm, CommentForm

#danh sách các bài đăng
def post_list(request):
    posts = Post.objects.filter(published=True).order_by('created_at') #lấy các bài đăng công khai và sắp xếp theo thời gain
    return render(request,'post_list.html',{
        'posts': posts
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
def post_create(request):
    """Tạo bài viết mới"""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Bài viết đã được đăng thành công!')
            return redirect('blog:post_detail', pk=post.pk)
    else:
        form = PostForm()
    
    return render(request, 'blog/post_form.html', {
        'form': form,
        'title': 'Tạo bài viết mới'
    })