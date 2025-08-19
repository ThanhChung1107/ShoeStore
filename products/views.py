from django.shortcuts import render,get_object_or_404
from django.core.paginator import Paginator
from .models import Product, Category, Brand, ProductSize
from django.http import JsonResponse
from django.shortcuts import redirect
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
# Create your views here.
def product(request):
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all().order_by('name')
    brands = Brand.objects.all().order_by('name')
    total_products = products.count()
    category_id = request.GET.get('category')
    paginator = Paginator(products, 12)  # 12 sản phẩm mỗi trang
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'product.html', {'products': page_obj,
                                            'categories': categories,
                                            'brands': brands,
                                            'total_products': total_products,
                                            'current_category': category_id,

                                            })

def add_to_cart(request):
    """View kiểm tra login và redirect"""
    if request.method == 'POST':
        # Kiểm tra user có đăng nhập không
        if not request.user.is_authenticated:
            # Lưu URL hiện tại để quay lại sau khi login
            current_url = request.META.get('HTTP_REFERER') or '/'
            request.session['next_url'] = current_url
            
            # Thông báo và chuyển đến trang login
            messages.info(request, 'Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng!')
            return redirect('login')
        
        # User đã đăng nhập - xử lý logic add to cart của bạn ở đây
        # ... your add to cart logic ...
        
        messages.success(request, 'Đã thêm sản phẩm vào giỏ hàng!')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # Nếu không phải POST
    return redirect('/')


def filter_products(request):
    """Xử lý AJAX request cho bộ lọc - KHÔNG RELOAD TRANG"""
    
    # Kiểm tra nếu là AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        products = Product.objects.all()
        
        # Lọc theo categories
        categories = request.GET.getlist('categories[]')
        if categories:
            products = products.filter(category__id__in=categories)
        
        # Lọc theo brands
        brands = request.GET.getlist('brands[]')
        if brands:
            products = products.filter(brand__id__in=brands)
        
        # Lọc theo khoảng giá preset
        price_range = request.GET.get('price_range')
        if price_range:
            if price_range == '0-300000':
                products = products.filter(price__lt=300000)
            elif price_range == '300000-500000':
                products = products.filter(price__gte=300000, price__lte=500000)
            elif price_range == '500000-800000':
                products = products.filter(price__gte=500000, price__lte=800000)
            elif price_range == '800000-100000000':
                products = products.filter(price__gte=800000, price__lte=100000000)
        
        # Lọc theo giá tùy chỉnh
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            products = products.filter(price__gte=min_price)
        if max_price:
            products = products.filter(price__lte=max_price)
        
        # Sắp xếp
        sort_by = request.GET.get('sort', 'default')
        if sort_by == 'price-low':
            products = products.order_by('price')
        elif sort_by == 'price-high':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'popularity':
            products = products.order_by('-view_count')  # Giả sử có field view_count
        
        # Serialize products với thông tin brand
        products_data = []
        for product in products:
            product_dict = {
                'pk': product.pk,
                'fields': {
                    'name': product.name,
                    'price': float(product.price),
                    'image': product.image.url if product.image else '',
                    'brand_name': product.brand.name if product.brand else '',
                    'category_name': product.category.name if product.category else '',
                }
            }
            products_data.append(product_dict)
        
        return JsonResponse({
            'products': json.dumps(products_data),
            'count': len(products_data),
            'success': True
        })
    
    # Nếu không phải AJAX, redirect về trang product
    return redirect('product')

def product_details(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    available_sizes = ProductSize.objects.filter(product=product, stock__gt=0).select_related('size')
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    return render(request, 'product_detail.html', {
        'product': product,
        'available_sizes': available_sizes,
        'related_products': related_products
    })