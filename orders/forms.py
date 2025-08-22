# orders/forms.py
from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['shipping_address', 'payment_method']
        widgets = {
            'shipping_address': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Nhập địa chỉ giao hàng đầy đủ'
            }),
            'payment_method': forms.RadioSelect()
        }