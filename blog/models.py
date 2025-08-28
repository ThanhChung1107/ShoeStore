from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
import os
from users.models import User

user = get_user_model()

def post_image_path(instance, filename):
    # Upload ảnh đến thư mục blog_posts/post_<id>/filename
    return f'blog_posts/post_{instance.id}/{filename}'

class Post(models.Model):
    author = models.ForeignKey(User,on_delete=models.CASCADE,related_name='blog_post')
    content = models.TextField(verbose_name='nội dung')
    image = models.ImageField(
        upload_to=post_image_path,
        blank=True,
        null=True,
        verbose_name='Ảnh minh họa'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')
    published = models.BooleanField(default=True, verbose_name='Công khai')

    class Meta:
        verbose_name = 'Bài viết'
        verbose_name_plural = 'Bài viết'
        ordering = ['-created_at']
    def __str__(self):
        return f"Bài viết của {self.author.username} - {self.created_at.strftime('%d/%m/%Y')}"
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.pk})
    
    def total_likes(self):
        return self.likes.count()
    
    def total_comments(self):
        return self.comments.count()
    
    def save(self, *args, **kwargs):
        # Xóa ảnh cũ nếu có ảnh mới
        if self.pk:
            try:
                old_post = Post.objects.get(pk=self.pk)
                if old_post.image and old_post.image != self.image:
                    if os.path.isfile(old_post.image.path):
                        os.remove(old_post.image.path)
            except Post.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Xóa ảnh khi bài viết bị xóa
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

class PostLike(models.Model):
    """Model cho lượt thích bài viết"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày giờ like')
    
    class Meta:
        verbose_name = 'Like bài viết'
        verbose_name_plural = 'Likes bài viết'
        unique_together = ['user', 'post']  # Mỗi user chỉ like 1 lần
    
    def __str__(self):
        return f"{self.user.username} thích bài viết #{self.post.id}"

class Comment(models.Model):
    """Model cho bình luận bài viết"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(verbose_name='Nội dung bình luận')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo bình luận')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        verbose_name = 'Bình luận'
        verbose_name_plural = 'Bình luận'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bình luận của {self.user.username} trên bài viết #{self.post.id}"
    
    def total_likes(self):
        return self.likes.count()
    
    def is_reply(self):
        return self.parent is not None
    
    def get_replies(self):
        return self.replies.all().order_by('created_at')

class CommentLike(models.Model):
    """Model cho lượt thích bình luận"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày giờ like')
    
    class Meta:
        verbose_name = 'Like bình luận'
        verbose_name_plural = 'Likes bình luận'
        unique_together = ['user', 'comment']  # Mỗi user chỉ like 1 lần
    
    def __str__(self):
        return f"{self.user.username} thích bình luận #{self.comment.id}"