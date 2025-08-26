from django.contrib import admin
from .models import Post, PostLike, Comment, CommentLike

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'short_content', 'created_at', 'published', 'total_likes', 'total_comments']
    list_filter = ['published', 'created_at', 'author']
    search_fields = ['content', 'author__username']
    readonly_fields = ['created_at', 'updated_at', 'total_likes', 'total_comments']
    fieldsets = (
        (None, {
            'fields': ('author', 'content', 'image', 'published')
        }),
        ('Thông tin meta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def short_content(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    short_content.short_description = 'Nội dung'

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__id']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at', 'short_content', 'total_likes']
    list_filter = ['created_at', 'post']
    search_fields = ['user__username', 'post__id', 'content']
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Nội dung'

@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'comment__id']