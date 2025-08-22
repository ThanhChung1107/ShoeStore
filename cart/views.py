from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from products.models import Product
from .models import Cart, CartItem
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import redirect, render
from .models import Cart

def cart_detail(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Vui lòng đăng nhập để xem giỏ hàng!")
        request.session['next_url'] = 'cart_detail'  # để sau khi login quay lại giỏ
        return redirect('login')

    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart.html', {'cart': cart})


def add_to_cart(request, product_id):
    if request.method != "POST":
        return redirect('/')  # Chỉ cho phép POST

    # Nếu chưa login
    if not request.user.is_authenticated:
        current_url = request.META.get('HTTP_REFERER') or '/'
        request.session['next_url'] = current_url
        messages.info(request, "Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng!")
        return redirect('login')

    # Đã login → xử lý logic giỏ hàng
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # Nếu là AJAX → trả JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            "success": True,
            "message": f"Đã thêm {product.name} vào giỏ hàng",
            "cart_count": cart.items.count()
        })

    # Nếu là request bình thường → redirect và hiện message
    messages.success(request, f"Đã thêm {product.name} vào giỏ hàng!")
    return redirect(request.META.get('HTTP_REFERER', 'cart_detail'))

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Đã xóa sản phẩm khỏi giỏ hàng")
    return redirect('cart_detail')

@login_required
@csrf_exempt
@require_POST
def update_cart(request, item_id):
    """Cập nhật số lượng sản phẩm bằng AJAX"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Xử lý AJAX request
            import json
            data = json.loads(request.body)
            new_quantity = int(data.get('quantity', 1))
            
            if new_quantity > 0:
                cart_item.quantity = new_quantity
                cart_item.save()
                
                return JsonResponse({
                    'success': True,
                    'new_quantity': new_quantity,
                    'new_subtotal': cart_item.subtotal,
                    'message': 'Cập nhật thành công'
                })
            else:
                cart_item.delete()
                return JsonResponse({
                    'success': True,
                    'deleted': True,
                    'message': 'Đã xóa sản phẩm'
                })
        else:
            # Xử lý form thông thường
            quantity = request.POST.get('quantity', 1)
            # ... code cũ ...
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@login_required
def prepare_checkout(request):
    if request.method == 'POST':
        selected_items = request.POST.getlist('selected_items')
        
        if not selected_items:
            messages.error(request, "Vui lòng chọn ít nhất một sản phẩm để thanh toán!")
            return redirect('cart_detail')
        
        # Lưu danh sách sản phẩm đã chọn vào session
        request.session['selected_items'] = selected_items
        return redirect('checkout')
    
    return redirect('cart_detail')