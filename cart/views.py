from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from products.models import Product
from .models import Cart, CartItem
from django.contrib import messages
from django.http import JsonResponse

@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)

    return render(request, 'cart.html', {'cart': cart,
                                         'cart_count': cart.items.count()})

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
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = request.POST.get('quantity', 1)
    
    try:
        quantity = int(quantity)
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Đã cập nhật số lượng")
        else:
            cart_item.delete()
            messages.success(request, "Đã xóa sản phẩm khỏi giỏ hàng")
    except ValueError:
        messages.error(request, "Số lượng không hợp lệ")
    
    return redirect('cart_detail')