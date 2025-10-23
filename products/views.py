from django.shortcuts import render,get_object_or_404
from django.core.paginator import Paginator
from .models import Product, Category, Brand, ProductSize, ProductReview, ReviewImage
from django.http import JsonResponse
from django.shortcuts import redirect
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q
from .forms import ProductReviewForm, ReviewImageForm
from orders.models import OrderItem
from .models import SearchHistory
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
    product = get_object_or_404(Product, id=product_id)
    available_sizes = ProductSize.objects.filter(product=product, stock__gt=0)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]
    
    # Kiểm tra user đã mua sản phẩm chưa
    can_review = False
    if request.user.is_authenticated:
        can_review = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='paid'
        ).exists() and not ProductReview.objects.filter(
            product=product, 
            user=request.user
        ).exists()
    
    context = {
        'product': product,
        'available_sizes': available_sizes,
        'related_products': related_products,
        'can_review': can_review,
    }
    
    return render(request, 'product_detail.html', context)
# tìm kiếm sản phẩm
# products/views.py - Cập nhật các function này

from .models import SearchHistory

def product_search(request):
    """Xử lý tìm kiếm sản phẩm"""
    products = Product.objects.all()
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    search_query = request.GET.get('q', '').strip()
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(brand__name__icontains=search_query)
        ).distinct()
        
        # 👉 LƯU LỊCH SỬ TÌM KIẾM
        if request.user.is_authenticated:
            SearchHistory.objects.create(
                user=request.user,
                query=search_query
            )
    
    total_products = products.count()
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'brands': brands,
        'search_query': search_query,
        'total_products': total_products,
    }
    
    return render(request, 'product.html', context)

def search_suggestions(request):
    """API trả về gợi ý tìm kiếm"""
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    if request.user.is_authenticated:
        if query:
            # Lọc lịch sử theo query
            history = SearchHistory.objects.filter(
                user=request.user,
                query__icontains=query
            ).values('query').distinct()[:5]
        else:
            # Lấy lịch sử gần đây
            history = SearchHistory.objects.filter(
                user=request.user
            ).values('query').distinct()[:8]
        
        for item in history:
            suggestions.append({
                'type': 'history',
                'text': item['query'],
                'url': f'/products/search/?q={item["query"]}'
            })
    
    # Gợi ý từ sản phẩm
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:5]
        
        for product in products:
            suggestions.append({
                'type': 'product',
                'text': product.name,
                'price': f'{product.price:,.0f}₫',
                'image': product.image.url if product.image else '',
                'url': f'/products/{product.id}/'
            })
    
    return JsonResponse({'suggestions': suggestions})

@login_required
def clear_search_history(request):
    """Xóa lịch sử tìm kiếm"""
    if request.method == 'POST':
        SearchHistory.objects.filter(user=request.user).delete()
        return JsonResponse({'success': True, 'message': 'Đã xóa lịch sử tìm kiếm'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def delete_search_item(request):
    """Xóa 1 item trong lịch sử"""
    if request.method == 'POST':
        query = request.POST.get('query')
        SearchHistory.objects.filter(user=request.user, query=query).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

#lấy danh sách review của sản phẩm
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Product, ProductReview
from orders.models import OrderItem

def product_reviews(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all().select_related('user')

    can_review = False
    if request.user.is_authenticated:
        # DEBUG: In ra thông tin để kiểm tra
        print(f"User: {request.user.username}")
        print(f"Product: {product.name}")
        
        # Kiểm tra user đã mua sản phẩm này chưa
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='paid'
        ).exists()
        
        print(f"Has purchased: {has_purchased}")
        
        # Kiểm tra user đã review sản phẩm chưa
        has_reviewed = product.reviews.filter(user=request.user).exists()
        print(f"Has reviewed: {has_reviewed}")
        
        can_review = has_purchased and not has_reviewed
        print(f"Can review: {can_review}")

    context = {
        'product': product,
        'reviews': reviews,
        'can_review': can_review,
        'average_rating': product.get_average_rating(),
        'total_reviews': reviews.count(),
    }
    return render(request, 'product_detail.html', context)

def add_review(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Bạn cần đăng nhập để đánh giá'})
    
    product = get_object_or_404(Product, id=product_id)
    
    # Kiểm tra user đã mua sản phẩm chưa
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        product=product,
        order__status='paid'
    ).exists()
    
    if not has_purchased:
        return JsonResponse({'success': False, 'error': 'Bạn cần mua sản phẩm trước khi đánh giá'})
    
    # Kiểm tra user đã đánh giá chưa
    if ProductReview.objects.filter(product=product, user=request.user).exists():
        return JsonResponse({'success': False, 'error': 'Bạn đã đánh giá sản phẩm này rồi'})
    
    if request.method == 'POST':
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            
            # Xử lý ảnh đính kèm
            images = request.FILES.getlist('images')
            for image in images:
                ReviewImage.objects.create(review=review, image=image)
            
            return JsonResponse({'success': True, 'message': 'Đánh giá thành công!'})
        
        return JsonResponse({'success': False, 'error': 'Dữ liệu không hợp lệ'})
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'})

