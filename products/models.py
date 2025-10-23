from django.db import models
from categorys.models import Category
from brands.models import Brand
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User
from django.db.models import Avg, Count

class Size(models.Model):
    value = models.CharField(max_length=5, verbose_name="Size giày")

    def __str__(self):
        return self.value

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    def get_average_rating(self):
        avg = self.reviews.aggregate(average=Avg('rating'))['average']
        return avg if avg is not None else 0

    # 👉 Hàm đếm số lượng reviews
    def get_review_count(self):
        return self.reviews.count()
    def get_total_sold(self):
        from django.db.models import Sum
        from orders.models import OrderItem
        
        total = OrderItem.objects.filter(
            product=self,
            order__status='paid'
        ).aggregate(total_sold=Sum('quantity'))['total_sold']
    
        return total or 0

class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0, verbose_name="Số lượng tồn kho")

    class Meta:
        unique_together = ('product', 'size')  # Mỗi product + size chỉ có 1 bản ghi

    def __str__(self):
        return f"{self.product.name} - {self.size.value} ({self.stock})"

class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Sao - Rất tệ'),
        (2, '2 Sao - Tệ'),
        (3, '3 Sao - Bình thường'),
        (4, '4 Sao - Tốt'),
        (5, '5 Sao - Tuyệt vời'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    image = models.ImageField(upload_to="reviews/",blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #phản hồi từ shop
    shop_reply = models.TextField(blank=True)
    replied_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('product', 'user')  # Mỗi user chỉ đánh giá 1 lần
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating} sao"
    
    def user_has_purchased(self):
        from orders.models import OrderItem
        return OrderItem.objects.filter(
            order__user = self.user,
            product = self.product,
            order__tatus = 'paid'
        ).exists()
    
class ReviewImage(models.Model):
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.review}"


class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.CharField(max_length=200, verbose_name="Từ khóa tìm kiếm")
    searched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-searched_at']
        verbose_name = 'Lịch sử tìm kiếm'
        verbose_name_plural = 'Lịch sử tìm kiếm'
    
    def __str__(self):
        return f"{self.user.username} - {self.query}"