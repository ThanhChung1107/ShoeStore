# 🔧 FIX: Giữ Session Khi Thanh Toán VNPAY

## 🎯 Vấn đề
Khi thanh toán qua VNPAY, session người dùng bị mất sau khi VNPAY redirect về website. Điều này khiến người dùng bị logout hoặc mất thông tin đăng nhập.

## ❌ Nguyên nhân
1. **Session không được save trước khi redirect** tới VNPAY
2. **Cookie session không được gửi lại** từ VNPAY vì SameSite policy
3. **Xóa session keys quá sớm** hoặc không lưu lại session
4. **CSRF token mismatch** khi VNPAY gửi GET request callback

## ✅ Cách Khắc Phục

### 1️⃣ Cập Nhật Django Settings (`ShoeStore/settings.py`)

```python
# ⚠️ SESSION CONFIGURATION - QUAN TRỌNG ĐỂ GIỮ SESSION KHI REDIRECT VNPAY
SESSION_SAVE_EVERY_REQUEST = True  # ✅ Lưu session sau mỗi request
SESSION_COOKIE_AGE = 1209600  # 2 tuần (giây)
SESSION_COOKIE_HTTPONLY = True  # Chỉ HTTP, không cho JavaScript truy cập
SESSION_COOKIE_SECURE = False  # Set False nếu dùng HTTP (localhost), True nếu HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'  # ✅ Cho phép gửi cookie khi redirect từ VNPAY
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Lưu session vào database
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Session tồn tại sau khi đóng browser

# CSRF & Cookie configuration cho VNPAY redirect
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000', 'https://sandbox.vnpayment.vn']
```

**Giải thích:**
- `SESSION_SAVE_EVERY_REQUEST = True`: Đảm bảo session được lưu sau mỗi request
- `SESSION_COOKIE_SAMESITE = 'Lax'`: Cho phép browser gửi cookie khi redirect từ domain khác
- `SESSION_COOKIE_SECURE = False`: Dùng HTTP cho localhost (True nếu production HTTPS)

---

### 2️⃣ Sửa Hàm `payment()` - Thêm `request.session.save()`

**File:** `payments/views.py`

```python
def payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # ... (code xử lý form) ...
            
            # ⚠️ QUAN TRỌNG: LUÔN SAVE SESSION TRƯỚC KHI REDIRECT
            request.session.save()
            
            vnpay_payment_url = vnp.get_payment_url(...)
            return redirect(vnpay_payment_url)
```

**Tại sao cần?**
- Khi gọi `request.session.save()`, Django **tường minh** lưu session vào database
- Đảm bảo session được persist trước khi redirect tới VNPAY

---

### 3️⃣ Sửa Hàm `payment_return()` - Gọi `request.session.save()` Sau Khi Xóa Keys

**File:** `payments/views.py`

```python
@csrf_exempt  # ⚠️ VNPAY gửi GET request mà không có CSRF token
def payment_return(request):
    inputData = request.GET
    if inputData:
        # ... (code validate VNPAY response) ...
        
        if vnp_ResponseCode == "00":
            try:
                order = Order.objects.get(id=int(order_id))
                
                if order.status != 'paid':
                    order.status = 'paid'
                    order.payment_date = timezone.now()
                    order.transaction_id = vnp_TransactionNo
                    order.save()
                    
                    # Xóa cart items
                    selected_items_ids = request.session.get('selected_items', [])
                    if selected_items_ids:
                        CartItem.objects.filter(id__in=selected_items_ids).delete()
                    
                    # ✅ XÓA SESSION KEYS (CHỈ XÓA CUSTOM KEYS, KHÔNG XÓA AUTH)
                    session_keys = ['selected_items', 'pending_order_id', 'applied_discount_code']
                    for key in session_keys:
                        if key in request.session:
                            del request.session[key]
                    
                    # ⚠️ QUAN TRỌNG: LUÔN SAVE SESSION SAU KHI THAY ĐỔI
                    request.session.save()
                
                # Render trang thành công
                return render(request, "payment/payment_return.html", {
                    "title": "Kết quả thanh toán",
                    "result": "Thành công", 
                    "order": order
                })
            except Order.DoesNotExist:
                return render(request, "payment/payment_return.html", {
                    "result": "Lỗi", 
                    "message": "Đơn hàng không tồn tại"
                })
```

**Tại sao cần?**
- `request.session.save()` đảm bảo Django **lưu lại session sau khi xóa keys**
- Không xóa session hoàn toàn, chỉ xóa các custom keys (selected_items, pending_order_id)
- Auth session (user info) **vẫn được giữ lại**

---

### 4️⃣ Thêm `@csrf_exempt` Decorator

```python
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # ⚠️ VNPAY gửi GET request mà không có CSRF token
def payment_return(request):
    # ...
```

**Tại sao cần?**
- VNPAY gửi GET request callback mà không có CSRF token
- Nếu không thêm `@csrf_exempt`, Django sẽ reject request và throw 403 Forbidden

---

## 🔄 Flow Hoàn Chỉnh

```
1. User đăng nhập ✅
   ↓ (session: user_id, cart, selected_items)
   
2. User chọn sản phẩm thanh toán
   ↓ (session được lưu vào database)
   
3. User click "Thanh Toán VNPAY"
   ↓ payment() view:
   ├─ request.session.save() ✅ (QUAN TRỌNG)
   └─ redirect(vnpay_url)
   
4. VNPAY xử lý thanh toán
   ↓ (session tồn tại vì được lưu tương minh)
   
5. VNPAY redirect về payment_return URL
   ├─ Browser gửi session cookie (SameSite=Lax ✅)
   └─ Django load session thành công
   
6. payment_return() xử lý callback
   ├─ Verify chữ ký VNPAY
   ├─ Cập nhật Order status
   ├─ Xóa custom session keys
   └─ request.session.save() ✅ (PERSIST lại)
   
7. User được redirect về trang thành công
   ✅ Session vẫn tồn tại (user vẫn đăng nhập)
```

---

## 🧪 Test

### Cách test:
1. Đăng nhập vào account
2. Chọn sản phẩm → Thanh toán
3. Trên trang VNPAY, click "Thanh toán thử nghiệm" hoặc dùng thẻ test
4. VNPAY redirect về
5. **Kiểm tra:** Người dùng vẫn còn đăng nhập? ✅

### Debug:
Nếu session vẫn mất, hãy check:
```python
# Thêm vào payment_return() để debug
print(f"Session user: {request.user}")
print(f"Session keys: {list(request.session.keys())}")
print(f"Is authenticated: {request.user.is_authenticated}")
```

---

## 📋 Tóm Tắt Changes

| File | Changes |
|------|---------|
| `ShoeStore/settings.py` | Thêm SESSION config + SAMESITE=Lax + CSRF_TRUSTED_ORIGINS |
| `payments/views.py` | Import csrf_exempt + thêm @csrf_exempt + request.session.save() |

---

## ⚠️ Production Notes

- **HTTPS:** Set `SESSION_COOKIE_SECURE = True` khi deploy HTTPS
- **Domain:** Cập nhật `VNPAY_RETURN_URL` với domain thực
- **SameSite:** Nếu dùng Chrome, `Lax` là tốt nhất (cho phép top-level navigation)
- **Session Backend:** Có thể dùng Redis nếu cần performance (thay `db` backend)

