from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from products.models import Product, Size
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
        return redirect('/')

    if not request.user.is_authenticated:
        current_url = request.META.get('HTTP_REFERER') or '/'
        request.session['next_url'] = current_url
        
        # XỬ LÝ AJAX REQUEST KHI CHƯA ĐĂNG NHẬP
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "success": False,
                "redirect": True,
                "login_required": True,
                "login_url": reverse('login'),
                "message": "Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng!"
            }, status=200)  # Để status 200 để JavaScript dễ xử lý
        
        messages.info(request, "Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng!")
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    # LẤY QUANTITY VÀ SIZE TỪ FORM
    quantity = int(request.POST.get('quantity', 1))
    size_id = request.POST.get('size')  # Lấy size ID từ radio button
    
    # LẤY SIZE OBJECT thay vì chỉ lưu ID
    selected_size = None
    if size_id:
        try:
            selected_size = Size.objects.get(id=size_id)
            print(f"DEBUG: Size object: {selected_size} (value: {selected_size.value})")
        except Size.DoesNotExist:
            # XỬ LÝ AJAX REQUEST CHO LỖI SIZE
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    "success": False,
                    "message": "Size không hợp lệ!"
                })
            messages.error(request, "Size không hợp lệ!")
            return redirect(request.META.get('HTTP_REFERER', 'product_detail'))
    
    print(f"DEBUG: Quantity from form: {quantity}")
    print(f"DEBUG: Size ID from form: {size_id}")
    print(f"DEBUG: Selected size object: {selected_size}")

    # Tìm hoặc tạo cart item với Size object
    try:
        cart_item = CartItem.objects.get(
            cart=cart,
            product=product,
            size=selected_size  # Dùng Size object, không phải ID
        )
        # Nếu tìm thấy, cộng thêm quantity
        cart_item.quantity += quantity
        cart_item.save()
        created = False
        print(f"DEBUG: Updated existing item, new quantity: {cart_item.quantity}")
        
    except CartItem.DoesNotExist:
        # Nếu không tìm thấy, tạo mới
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
            size=selected_size  # Lưu Size object
        )
        created = True
        print(f"DEBUG: Created new item, quantity: {cart_item.quantity}, size: {cart_item.size}")

    # Response cho AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        size_text = f" (Size: {selected_size.value})" if selected_size else ""
        return JsonResponse({
            "success": True,
            "message": f"Đã thêm {quantity} x {product.name}{size_text} vào giỏ hàng",
            "cart_count": cart.items.count(),
            "quantity_added": quantity
        })

    # Response cho normal request
    size_text = f" (Size: {selected_size.value})" if selected_size else ""
    messages.success(request, f"Đã thêm {quantity} x {product.name}{size_text} vào giỏ hàng!")
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