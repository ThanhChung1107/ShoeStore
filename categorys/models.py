from django.db import models
class Category(models.Model):
    STATUS_CHOICES = [
        ('active', 'Hoạt động'),
        ('inactive', 'Ngừng hoạt động'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="Trạng thái")

    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục"

    def __str__(self):
        return self.name