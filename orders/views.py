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
            
            # Tạo các OrderItem từ các CartItem đã chọn - SỬA LẠI Ở ĐÂY
            for cart_item in selected_items:
                try:
                    order_item_data = {
                        'order': order,
                        'product': cart_item.product,
                        'quantity': cart_item.quantity,
                        'price': cart_item.product.price,
                        'size': cart_item.size
                    }
                        
                    order_item = OrderItem(**order_item_data)
                    order_item.save()  # Phương thức save() sẽ tự tính subtotal
                    print(f"Đã tạo OrderItem: {order_item.id}")  # Debug
                    
                except Exception as e:
                    print(f"Lỗi khi tạo OrderItem: {e}")  # Debug
                    messages.error(request, f"Có lỗi xảy ra với sản phẩm {cart_item.product.name}")
            # Xóa session sau khi sử dụng
            if 'selected_items' in request.session:
                del request.session['selected_items']
            
            payment_method = form.cleaned_data['payment_method']
            if payment_method == 'cod':
                messages.success(request, "Đặt hàng thành công! Bạn sẽ thanh toán khi nhận hàng.")
                return redirect('order_detail', order_id=order.id)
            elif payment_method == 'banking':
                return redirect('process_bank_payment', order_id=order.id)
        else:
            # Hiển thị lỗi form nếu có
            messages.error(request, "Vui lòng kiểm tra lại thông tin đơn hàng.")
                
    else:
        initial_data = {
            'shipping_address': request.user.address if hasattr(request.user, 'address') else '',
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

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.order_items.all()
    order_count = order_items.count()
    context = {
        'order': order,
        'order_items': order_items,
        'order_count': order_count,
    }
    return render(request,'order_detail.html',context)

@login_required
def order_list(request):
    """Hiển thị danh sách đơn hàng của người dùng"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_list.html', {'orders': orders})