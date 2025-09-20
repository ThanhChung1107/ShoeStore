# discounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem
from .models import Discount
  # Giả sử bạn có app carts

@require_POST
@login_required
def apply_discount_ajax(request):
    """Xử lý AJAX request để áp dụng mã giảm giá"""
    discount_id = request.POST.get('discount_id')
    
    if not discount_id:
        return JsonResponse({'success': False, 'message': 'Vui lòng chọn mã giảm giá'})
    
    try:
        # Lấy giỏ hàng và items đã chọn từ session
        cart = Cart.objects.get(user=request.user)
        selected_items_ids = request.session.get('selected_items', [])
        selected_items = CartItem.objects.filter(id__in=selected_items_ids, cart=cart)
        
        if not selected_items.exists():
            return JsonResponse({'success': False, 'message': 'Không có sản phẩm nào được chọn'})
        
        order_total = sum(item.subtotal for item in selected_items)
        
        # Tìm và kiểm tra mã giảm giá
        discount = Discount.objects.get(id=discount_id, is_active=True)
        
        # Kiểm tra xem mã có còn hiệu lực không
        now = timezone.now()
        if not (discount.start_date <= now <= discount.end_date):
            return JsonResponse({'success': False, 'message': 'Mã giảm giá đã hết hạn'})
        
        # Kiểm tra số lần sử dụng
        if discount.current_usage >= discount.max_usage:
            return JsonResponse({'success': False, 'message': 'Mã giảm giá đã hết số lần sử dụng'})
        
        discount_amount = discount.calculate_discount_amount(order_total, selected_items)
        
        if discount_amount > 0:
            # Lưu mã giảm giá vào session
            request.session['applied_discount_code'] = discount.code
            request.session['applied_discount_id'] = discount.id
            request.session.modified = True
            
            return JsonResponse({
                'success': True, 
                'discount_amount': float(discount_amount),
                'final_amount': float(order_total - discount_amount),
                'discount_code': discount.code,
                'discount_name': discount.name
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': 'Mã giảm giá không áp dụng được cho đơn hàng này'
            })
            
    except Discount.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Mã giảm giá không hợp lệ'})
    except Exception as e:
        print(f"Lỗi khi áp dụng mã giảm giá: {e}")
        return JsonResponse({'success': False, 'message': 'Có lỗi xảy ra khi áp dụng mã giảm giá'})

@require_POST
@login_required
def remove_discount_ajax(request):
    """Xử lý AJAX request để xóa mã giảm giá"""
    if 'applied_discount_code' in request.session:
        del request.session['applied_discount_code']
    if 'applied_discount_id' in request.session:
        del request.session['applied_discount_id']
    request.session.modified = True
    
    # Lấy lại tổng tiền đơn hàng
    cart = Cart.objects.get(user=request.user)
    selected_items_ids = request.session.get('selected_items', [])
    selected_items = CartItem.objects.filter(id__in=selected_items_ids, cart=cart)
    order_total = sum(item.subtotal for item in selected_items) if selected_items.exists() else 0
    
    return JsonResponse({
        'success': True, 
        'final_amount': float(order_total),
        'message': 'Đã xóa mã giảm giá'
    })

