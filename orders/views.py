from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from cart.models import Cart, CartItem
from .models import Order,OrderItem 
from .forms import OrderForm
# Create your views here.
@login_required
def checkout(request):
    """Xử lý trang thanh toán"""
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, "Giỏ hàng của bạn đang trống!")
        return redirect('cart_detail')
    
    # Lấy danh sách sản phẩm đã chọn từ session
    selected_items_ids = request.session.get('selected_items', [])
    
    if not selected_items_ids:
        messages.error(request, "Vui lòng chọn sản phẩm để thanh toán!")
        return redirect('cart_detail')
    
    # Lọc các sản phẩm đã chọn
    selected_items = CartItem.objects.filter(
        id__in=selected_items_ids, 
        cart=cart
    )
    
    if not selected_items.exists():
        messages.error(request, "Không tìm thấy sản phẩm đã chọn!")
        return redirect('cart_detail')
    
    # Tính tổng tiền chỉ cho các sản phẩm đã chọn
    selected_total = sum(item.subtotal for item in selected_items)
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.cart = cart
            order.save()
            
            # Lưu thông tin sản phẩm đã chọn vào order
            order.selected_items.set(selected_items)
            
            # Tạo các OrderItem từ các CartItem đã chọn
            for cart_item in selected_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,  # Lưu giá tại thời điểm đặt
                    subtotal=cart_item.subtotal
                )
            
            # Xóa session sau khi sử dụng
            if 'selected_items' in request.session:
                del request.session['selected_items']
            
            payment_method = form.cleaned_data['payment_method']
            if payment_method == 'cod':
                messages.success(request, "Đặt hàng thành công! Bạn sẽ thanh toán khi nhận hàng.")
                return redirect('order_detail', order_id=order.id)  # Chuyển hướng đến trang chi tiết đơn hàng
            elif payment_method == 'banking':
                return redirect('process_bank_payment', order_id=order.id)
                
    else:
        initial_data = {
            'shipping_address': request.user.address,
            'payment_method': 'cod'
        }
        form = OrderForm(initial=initial_data)
    
    context = {
        'form': form,
        'cart': cart,
        'selected_items': selected_items,
        'selected_total': selected_total
    }
    return render(request, 'checkout.html', context)