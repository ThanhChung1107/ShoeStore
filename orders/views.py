from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from cart.models import Cart, CartItem
from discounts.models import Discount
from .models import Order,OrderItem 
from .forms import OrderForm
from django.db import models

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
    
    # Lấy mã giảm giá từ session nếu có
    discount_code = request.session.get('applied_discount_code', '')
    discount_amount = 0
    final_amount = selected_total
    
    # Lấy danh sách mã giảm giá có thể áp dụng
    available_discounts = get_available_discounts(selected_items, selected_total)
    
    if discount_code:
        try:
            discount = Discount.objects.get(code=discount_code, is_active=True)
            discount_amount = discount.calculate_discount_amount(selected_total, selected_items)
            if discount_amount > 0:
                final_amount = selected_total - discount_amount
        except Discount.DoesNotExist:
            # Nếu mã không tồn tại, xóa khỏi session
            if 'applied_discount_code' in request.session:
                del request.session['applied_discount_code']
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.cart = cart
            order.total_amount = selected_total
            
            # Áp dụng giảm giá nếu có
            if discount_code and discount_amount > 0:
                order.discount_code = discount_code
                order.discount_amount = discount_amount
            
            order.final_amount = final_amount
            order.save()
            
            # Lưu thông tin sản phẩm đã chọn vào order
            order.selected_items.set(selected_items)
            
            # Tạo các OrderItem từ các CartItem đã chọn
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
                    order_item.save()
                    
                except Exception as e:
                    print(f"Lỗi khi tạo OrderItem: {e}")
                    messages.error(request, f"Có lỗi xảy ra với sản phẩm {cart_item.product.name}")
            
            # Xóa session sau khi sử dụng
            if 'selected_items' in request.session:
                del request.session['selected_items']
            
            # Xóa mã giảm giá khỏi session sau khi sử dụng
            if 'applied_discount_code' in request.session:
                del request.session['applied_discount_code']
            
            payment_method = form.cleaned_data['payment_method']
            if payment_method == 'cod':
                messages.success(request, "Đặt hàng thành công! Bạn sẽ thanh toán khi nhận hàng.")
                return redirect('order_detail', order_id=order.id)
            elif payment_method == 'banking':
                # Lưu order ID vào session
                request.session['pending_order_id'] = order.id
                request.session.modified = True
                
                return redirect('payment')
        else:
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
        'selected_total': selected_total,
        'final_amount': final_amount,
        'discount_amount': discount_amount,
        'discount_code': discount_code,
        'available_discounts': available_discounts  # Thêm danh sách mã giảm giá
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

def get_available_discounts(selected_items, order_total):
    """Lấy danh sách mã giảm giá có thể áp dụng cho sản phẩm đã chọn"""
    from django.utils import timezone
    from django.db import models
    
    now = timezone.now()
    
    # Lấy tất cả mã giảm giá còn hiệu lực
    active_discounts = Discount.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now,
        current_usage__lt=models.F('max_usage')
    )
    
    available_discounts = []
    
    for discount in active_discounts:
        # Kiểm tra điều kiện giá trị đơn hàng tối thiểu
        if order_total < discount.min_order_value:
            continue
        
        # Kiểm tra xem mã có áp dụng cho sản phẩm/danh mục cụ thể không
        if discount.products.exists() or discount.categories.exists():
            applicable = False
            for item in selected_items:
                # Kiểm tra sản phẩm
                if discount.products.filter(id=item.product.id).exists():
                    applicable = True
                    break
                
                # Kiểm tra danh mục
                if discount.categories.filter(id=item.product.category.id).exists():
                    applicable = True
                    break
            
            if not applicable:
                continue
        
        # Tính toán số tiền giảm giá
        discount_amount = discount.calculate_discount_amount(order_total, selected_items)
        
        if discount_amount > 0:
            # Tạo tên mã giảm giá từ code và description
            discount_name = discount.code
            if discount.description:
                discount_name = f"{discount.code} - {discount.description[:50]}"
            
            discount_info = {
                'id': discount.id,
                'code': discount.code,
                'name': discount_name,
                'description': discount.description or f"Giảm {discount.value}{'%' if discount.discount_type == 'percentage' else '₫'}",
                'discount_type': discount.discount_type,
                'value': discount.value,
                'min_order_value': discount.min_order_value,
                'max_discount_amount': discount.max_discount_amount,
                'discount_amount': discount_amount,
                'final_amount': order_total - discount_amount
            }
            available_discounts.append(discount_info)
    
    return available_discounts