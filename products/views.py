from django.shortcuts import render,get_object_or_404
from django.core.paginator import Paginator
from .models import Product, Category, Brand, ProductSize, ProductReview, ReviewImage, SearchHistory
from django.http import JsonResponse
from django.shortcuts import redirect
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, Q
from .forms import ProductReviewForm, ReviewImageForm
from orders.models import OrderItem
from django.utils import timezone
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

from .models import ProductViewHistory

def track_product_view(request, product_id):
    """Lưu lịch sử xem sản phẩm (AJAX)"""
    print(f"=== START TRACK PRODUCT VIEW ===")
    print(f"Method: {request.method}")
    print(f"Is AJAX: {request.headers.get('X-Requested-With')}")
    print(f"Product ID: {product_id}")
    print(f"User: {request.user} (Authenticated: {request.user.is_authenticated})")
    print(f"Session key: {request.session.session_key}")
    print(f"Session exists: {hasattr(request, 'session')}")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            product = get_object_or_404(Product, id=product_id)
            print(f"Product found: {product.name}")
            
            # Tạo hoặc cập nhật lịch sử xem
            if request.user.is_authenticated:
                print("=== AUTHENTICATED USER ===")
                view_history, created = ProductViewHistory.objects.get_or_create(
                    user=request.user,
                    product=product,
                    defaults={'view_count': 1}
                )
                if not created:
                    print(f"Updating existing record - old count: {view_history.view_count}")
                    view_history.view_count += 1
                    view_history.viewed_at = timezone.now()
                    view_history.save()
                    print(f"Updated record - new count: {view_history.view_count}")
                else:
                    print("Created new record")
                
                # Verify the record was saved
                verify_record = ProductViewHistory.objects.filter(
                    user=request.user, 
                    product=product
                ).first()
                print(f"Verify record: {verify_record} (View count: {verify_record.view_count if verify_record else 'None'})")
                
            else:
                print("=== ANONYMOUS USER ===")
                # User chưa đăng nhập - dùng session
                if not request.session.session_key:
                    print("Creating new session...")
                    request.session.create()
                    print(f"New session key: {request.session.session_key}")
                
                session_key = request.session.session_key
                print(f"Using session key: {session_key}")
                
                view_history, created = ProductViewHistory.objects.get_or_create(
                    session_key=session_key,
                    product=product,
                    defaults={'view_count': 1}
                )
                if not created:
                    print(f"Updating existing record - old count: {view_history.view_count}")
                    view_history.view_count += 1
                    view_history.viewed_at = timezone.now()
                    view_history.save()
                    print(f"Updated record - new count: {view_history.view_count}")
                else:
                    print("Created new record")
                
                # Verify the record was saved
                verify_record = ProductViewHistory.objects.filter(
                    session_key=session_key, 
                    product=product
                ).first()
                print(f"Verify record: {verify_record} (View count: {verify_record.view_count if verify_record else 'None'})")
            
            # Test: Count total records
            total_records = ProductViewHistory.objects.count()
            print(f"Total ProductViewHistory records in DB: {total_records}")
            
            print("=== END TRACK PRODUCT VIEW ===")
            return JsonResponse({'success': True, 'message': 'Tracked product view'})
            
        except Exception as e:
            print(f"ERROR in track_product_view: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        print("Not an AJAX request")
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def get_recommendations(request):
    """Lấy sản phẩm đề xuất dựa trên lịch sử xem"""
    limit = int(request.GET.get('limit', 4))  # ĐỔI: 8 -> 4
    
    recommendations = []
    
    if request.user.is_authenticated:
        # User đã đăng nhập: dựa trên lịch sử của user
        user_viewed_products = ProductViewHistory.objects.filter(
            user=request.user
        ).order_by('-viewed_at')[:5]  # Có thể giảm xuống 5 để tối ưu
        
        if user_viewed_products.exists():
            # Lấy danh mục từ các sản phẩm đã xem
            viewed_categories = set([pv.product.category for pv in user_viewed_products])
            viewed_brands = set([pv.product.brand for pv in user_viewed_products if pv.product.brand])
            
            # Đề xuất sản phẩm cùng danh mục/thương hiệu - CHỈ LẤY 4
            recommendations = Product.objects.filter(
                Q(category__in=viewed_categories) | 
                Q(brand__in=viewed_brands)
            ).exclude(
                id__in=[pv.product.id for pv in user_viewed_products]
            ).distinct().order_by('-created_at')[:limit]  # Đã có limit=4
    
    else:
        # User chưa đăng nhập: dựa trên session
        session_key = request.session.session_key
        if session_key:
            session_viewed_products = ProductViewHistory.objects.filter(
                session_key=session_key
            ).order_by('-viewed_at')[:5]  # Giảm xuống 5
            
            if session_viewed_products.exists():
                viewed_categories = set([pv.product.category for pv in session_viewed_products])
                viewed_brands = set([pv.product.brand for pv in session_viewed_products if pv.product.brand])
                
                recommendations = Product.objects.filter(
                    Q(category__in=viewed_categories) | 
                    Q(brand__in=viewed_brands)
                ).exclude(
                    id__in=[pv.product.id for pv in session_viewed_products]
                ).distinct().order_by('-created_at')[:limit]  # Đã có limit=4
    
    # Nếu không có đủ đề xuất, thêm sản phẩm phổ biến - CHỈ LẤY ĐỦ 4
    if len(recommendations) < limit:
        popular_products = Product.objects.annotate(
            view_count=Count('productviewhistory')
        ).order_by('-view_count', '-created_at')[:limit]  # ĐỔI: limit - len(recommendations) -> limit
        
        # Kết hợp và loại bỏ trùng lặp
        existing_ids = [p.id for p in recommendations]
        additional_products = [p for p in popular_products if p.id not in existing_ids]
        recommendations = list(recommendations) + additional_products
    
    # Đảm bảo chỉ trả về đúng 4 sản phẩm
    recommendations = recommendations[:limit]
    
    # Serialize dữ liệu
    recommendations_data = []
    for product in recommendations:
        recommendations_data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image': product.image.url if product.image else '',
            'brand': product.brand.name if product.brand else '',
            'category': product.category.name,
            'url': f'/products/{product.id}/'
        })
    
    return JsonResponse({'recommendations': recommendations_data})


# tìm kiếm sản phẩm
def product_search(request):
    """Xử lý tìm kiếm sản phẩm"""
    
    products = Product.objects.all()
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    search_query = request.GET.get('q', '').strip()
    
    if search_query:
        # Lưu lịch sử tìm kiếm
        save_search_history(request, search_query)
        
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(brand__name__icontains=search_query)
        ).distinct()
    
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

def save_search_history(request, query):
    """Lưu lịch sử tìm kiếm"""
    if len(query) < 2:  # Không lưu query quá ngắn
        return
    
    if request.user.is_authenticated:
        # Kiểm tra xem query đã tồn tại chưa
        existing = SearchHistory.objects.filter(
            user=request.user,
            query__iexact=query
        ).first()
        
        if existing:
            # Cập nhật thời gian
            existing.created_at = timezone.now()
            existing.save()
        else:
            # Tạo mới
            SearchHistory.objects.create(
                user=request.user,
                query=query
            )
        
        # Giới hạn số lượng lịch sử (giữ 20 mục gần nhất)
        user_history = SearchHistory.objects.filter(user=request.user)
        if user_history.count() > 20:
            old_records = user_history[20:]
            SearchHistory.objects.filter(
                id__in=[record.id for record in old_records]
            ).delete()
    else:
        # Lưu theo session cho user chưa đăng nhập
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        
        existing = SearchHistory.objects.filter(
            session_key=session_key,
            query__iexact=query
        ).first()
        
        if existing:
            existing.created_at = timezone.now()
            existing.save()
        else:
            SearchHistory.objects.create(
                session_key=session_key,
                query=query
            )
        
        # Giới hạn số lượng
        session_history = SearchHistory.objects.filter(session_key=session_key)
        if session_history.count() > 20:
            old_records = session_history[20:]
            SearchHistory.objects.filter(
                id__in=[record.id for record in old_records]
            ).delete()

def get_search_history(request):
    """Lấy lịch sử tìm kiếm"""
    try:
        if request.user.is_authenticated:
            history = SearchHistory.objects.filter(
                user=request.user
            ).order_by('-created_at')[:10]
        else:
            if not request.session.session_key:
                return JsonResponse({'history': []})
            
            session_key = request.session.session_key
            history = SearchHistory.objects.filter(
                session_key=session_key
            ).order_by('-created_at')[:10]
        
        history_data = [
            {
                'query': item.query,
                'id': item.id
            }
            for item in history
        ]
        
        return JsonResponse({'history': history_data, 'success': True})
    except Exception as e:
        return JsonResponse({'history': [], 'success': False, 'error': str(e)})
    
def delete_search_history(request):
    """Xóa một mục lịch sử tìm kiếm"""
    try:
        # Debug: In ra để kiểm tra
        print("DELETE REQUEST RECEIVED")
        print("Method:", request.method)
        print("POST data:", request.POST)
        print("Body:", request.body)
        
        # Lấy ID từ POST data
        history_id = request.POST.get('id')
        
        # Nếu không có trong POST, thử lấy từ JSON body
        if not history_id:
            try:
                data = json.loads(request.body)
                history_id = data.get('id')
            except:
                pass
        
        print("History ID:", history_id)
        
        if not history_id:
            return JsonResponse({
                'success': False, 
                'error': 'Missing ID parameter'
            })
        
        if request.user.is_authenticated:
            deleted_count = SearchHistory.objects.filter(
                id=history_id,
                user=request.user
            ).delete()[0]
            
            print(f"Deleted {deleted_count} items for user {request.user.username}")
        else:
            session_key = request.session.session_key
            if not session_key:
                return JsonResponse({
                    'success': False, 
                    'error': 'No session key'
                })
            
            deleted_count = SearchHistory.objects.filter(
                id=history_id,
                session_key=session_key
            ).delete()[0]
            
            print(f"Deleted {deleted_count} items for session {session_key}")
        
        if deleted_count > 0:
            return JsonResponse({'success': True, 'message': 'Deleted successfully'})
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Item not found or already deleted'
            })
            
    except Exception as e:
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'error': str(e)
        })

def clear_search_history(request):
    """Xóa toàn bộ lịch sử tìm kiếm"""
    if request.method == 'POST':
        try:
            if request.user.is_authenticated:
                SearchHistory.objects.filter(user=request.user).delete()
            else:
                session_key = request.session.session_key
                SearchHistory.objects.filter(session_key=session_key).delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Tìm sản phẩm phù hợp
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
    ).select_related('brand')[:5]
    
    # Tìm danh mục phù hợp
    categories = Category.objects.filter(
        name__icontains=query
    )[:3]
    
    suggestions = []
    
    # Thêm sản phẩm vào suggestions
    for product in products:
        suggestions.append({
            'type': 'product',
            'text': product.name,
            'url': f'/products/product/{product.id}/',  # Điều chỉnh theo URL pattern
            'image': product.image.url if product.image else '',
            'price': f'{product.price:,.0f}₫'
        })
    
    # Thêm danh mục vào suggestions
    for category in categories:
        suggestions.append({
            'type': 'category',
            'text': category.name,
            'url': f'/products/?category={category.id}'
        })
    
    return JsonResponse({'suggestions': suggestions})
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

