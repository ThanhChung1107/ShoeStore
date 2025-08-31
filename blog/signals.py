from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from .models import Post

@receiver(post_save, sender=Post)
def post_created_notification(sender, instance, created, **kwargs):
    if created and instance.published:  # Chỉ gửi khi bài viết mới được tạo và published
        channel_layer = get_channel_layer()
        
        # Gửi cho tất cả users đã đăng nhập
        all_users = User.objects.filter(is_active=True)
        
        for user in all_users:
            if user != instance.author:  # Không gửi cho chính tác giả
                async_to_sync(channel_layer.group_send)(
                    f'user_{user.id}_notifications',
                    {
                        'type': 'new_post_notification',
                        'post_id': instance.id,
                        'author_name': instance.author.username,
                        'content': instance.title,  # Hoặc instance.content[:100]
                        'created_at': instance.created_at.isoformat()
                    }
                )