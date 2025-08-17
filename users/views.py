from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import UserRegisterForm
from products.models import Product
from categorys.models import Category

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Chào mừng {username} đến với ShoeStore!')
                return redirect('home')  # Thay bằng trang chủ sau này
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không đúng.")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Đăng ký thành công!')
            return redirect('home')  # Thay bằng trang chủ sau này
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

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