from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import os

def user_avatar_path(instance, filename):
    # Upload avatar đến thư mục avatars/user_<id>/filename
    return f'avatars/user_{instance.id}/{filename}'

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email là bắt buộc')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser phải có is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser phải có is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(
        upload_to=user_avatar_path, 
        default='avatars/default_avatar.jpg',
        blank=True,
        null=True
    )
    
    objects = UserManager()

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # Xóa avatar cũ nếu có avatar mới
        if self.pk:
            try:
                old_avatar = User.objects.get(pk=self.pk).avatar
                if old_avatar and old_avatar != self.avatar and old_avatar.name != 'avatars/default_avatar.jpg':
                    if os.path.isfile(old_avatar.path):
                        os.remove(old_avatar.path)
            except User.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Xóa avatar khi user bị xóa
        if self.avatar and self.avatar.name != 'avatars/default_avatar.jpg':
            if os.path.isfile(self.avatar.path):
                os.remove(self.avatar.path)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Người dùng'

    # Phương thức kiểm tra quyền
    def is_customer(self):
        return not self.is_admin