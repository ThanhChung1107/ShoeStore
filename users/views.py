from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import UserRegisterForm
from products.models import Product
from categorys.models import Category
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import User
from django.http import JsonResponse
from .forms import AvatarUploadForm
from django.views.decorators.csrf import csrf_exempt

def custom_login(request):
    # Nếu user đã đăng nhập, chuyển hướng về trang chủ
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('/admin/')
        next_url = request.session.get('next_url', '/')
        if 'next_url' in request.session:
            del request.session['next_url']
        return redirect(next_url)
    
    if request.method == 'POST':
        # SỬA LẠI: Sử dụng đúng cách khởi tạo form
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                if user.is_staff or user.is_superuser:
                    return redirect('/admin/')
                
                # Lấy next_url từ nhiều nguồn
                next_url = (
                    request.session.get('next_url') or
                    request.POST.get('next') or 
                    request.GET.get('next') or 
                    '/'
                )
                
                # Xóa next_url khỏi session
                if 'next_url' in request.session:
                    del request.session['next_url']
                    
                messages.success(request, 'Đăng nhập thành công!')
                return redirect(next_url)
        else:
            # HIỂN THỊ LỖI CỤ THỂ
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    if 'invalid login' in error.lower() or 'please enter a correct' in error.lower():
                        error_messages.append('Tên đăng nhập hoặc mật khẩu không đúng!')
                    else:
                        error_messages.append(error)
            
            # Chỉ hiển thị một thông báo lỗi duy nhất
            if error_messages:
                messages.error(request, error_messages[0])
    
    else:
        form = AuthenticationForm()
    
    # Truyền next_url từ session vào template
    next_url = request.session.get('next_url', '')
    return render(request, 'users/login_signup.html', {
        'next_url': next_url,
        'active_tab': 'login'
    })
    
def custom_logout(request):
    logout(request)
    # Chuyển hướng đến trang chủ hoặc trang đăng nhập
    return redirect('home') 

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Đăng ký thành công!')
            
            # Lấy next_url từ session nếu có
            next_url = request.session.get('next_url', 'home')
            if 'next_url' in request.session:
                del request.session['next_url']
                
            return redirect(next_url)
        else:
            # Xử lý lỗi cụ thể
            if 'username' in form.errors:
                messages.error(request, 'Tên đăng nhập đã tồn tại!')
            elif 'email' in form.errors:
                messages.error(request, 'Email đã được sử dụng!')
            elif 'password2' in form.errors:
                messages.error(request, 'Mật khẩu xác nhận không khớp!')
            else:
                # Hiển thị tất cả lỗi khác
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{error}")
    else:
        form = UserRegisterForm()
    
    # Truyền next_url từ session vào template
    next_url = request.session.get('next_url', '')
    return render(request, 'users/login_signup.html', {
        'form': form,
        'next_url': next_url
    })
def home(request):
    # Lấy sản phẩm nổi bật
    featured_products = Product.objects.order_by('created_at')[:4]
    
    # Lấy sản phẩm mới nhất
    latest_products = Product.objects.order_by('created_at')[:8]
    
    # Lấy danh mục
    categories = Category.objects.all()
    
    return render(request, 'home.html', {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories
    })
@login_required
def account_detail(request):
    user = get_object_or_404(User, id=request.user.id)
    
    if request.method == 'POST' and 'avatar' in request.FILES:
        form = AvatarUploadForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật avatar thành công!")
            return redirect('users:account_detail')
        else:
            messages.error(request, "Có lỗi xảy ra khi cập nhật avatar.")
    
    context = {
        'user_profile': user,
        'avatar_form': AvatarUploadForm(instance=user)
    }
    
    return render(request, 'users/account_detail.html', context)

@login_required
def upload_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        user = request.user
        form = AvatarUploadForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Cập nhật avatar thành công!',
                'avatar_url': user.avatar.url
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Có lỗi xảy ra: ' + str(form.errors)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Yêu cầu không hợp lệ'
    })

@login_required
def update_profile(request):
    if request.method == 'POST':
        try:
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.phone_number = request.POST.get('phone_number', '')
            user.address = request.POST.get('address', '')
            
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Cập nhật thông tin thành công!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Có lỗi xảy ra: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Yêu cầu không hợp lệ'
    })