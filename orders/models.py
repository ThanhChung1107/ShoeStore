from django.db import models

# Create your models here.
from django.utils import timezone
from cart.models import Cart
from django.contrib.auth import get_user_model
from products.models import Product
from discounts.models import Discount

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('unpaid','chưa thanh toán'),
        ('paid', 'đã thanh toán')
    ]
    PAYMENT_METHOD_CHOICES = [
        ('cod','thanh toán khi nhận hàng'),
        ('banking','chuyển khoản ngân hàng')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey('cart.Cart', on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    shipping_address = models.TextField()
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    selected_items = models.ManyToManyField('cart.CartItem')
    discount = models.ForeignKey(
        Discount, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Mã giảm giá áp dụng"
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Số tiền được giảm"
    )
    final_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Tổng thanh toán"
    )
    @property
    def total_price(self):
        # Sử dụng OrderItem để tính tổng thay vì CartItem
        return sum(item.subtotal for item in self.order_items.all())
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

    def mark_as_paid(self, transaction_id=None):
        """Đánh dấu đơn hàng đã thanh toán"""
        self.status = 'paid'
        self.payment_date = timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT,related_name="order_items")
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    size = models.CharField(max_length=50, blank=True, null=True)   # giá tại thời điểm đặt
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"