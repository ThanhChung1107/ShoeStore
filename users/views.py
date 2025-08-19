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

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import render, redirect

def custom_login(request):
    # Nếu user đã đăng nhập, chuyển hướng về trang chủ
    if request.user.is_authenticated:
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
    # Nếu user đã đăng nhập, chuyển hướng về trang chủ
    if request.user.is_authenticated:
        next_url = request.session.get('next_url', '/')
        if 'next_url' in request.session:
            del request.session['next_url']
        return redirect(next_url)
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
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
            # Hiển thị lỗi cụ thể từ form
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = AuthenticationForm()
    
    # Truyền next_url từ session vào template
    next_url = request.session.get('next_url', '')
    return render(request, 'users/login_signup.html', {
        'login_form': form,  # Đổi tên biến để phân biệt
        'next_url': next_url,
        'active_tab': 'login'  # Thêm biến để xác định tab active
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