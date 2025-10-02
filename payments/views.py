# payments/views.py - Fixed version
import hashlib
import hmac
import json
import urllib.parse  # Thay đổi từ urllib
import random
import requests
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
# from django.utils.http import urlquote  # XÓA dòng này - không cần thiết
from orders.models import Order
from payments.forms import PaymentForm
from payments.vnpay import vnpay
from django.utils import timezone
from cart.models import Cart


def index(request):
    return render(request, "payment/index.html", {"title": "Danh sách demo"})


def hmacsha512(key, data):
    byteKey = key.encode('utf-8')
    byteData = data.encode('utf-8')
    return hmac.new(byteKey, byteData, hashlib.sha512).hexdigest()


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '127.0.0.1'


def payment(request):
    if request.method == 'POST':
        # Process input data and build url payment
        form = PaymentForm(request.POST)
        if form.is_valid():
            order_type = form.cleaned_data['order_type']
            order_id = form.cleaned_data['order_id']
            amount = form.cleaned_data['amount']
            order_desc = form.cleaned_data['order_desc']
            bank_code = form.cleaned_data['bank_code']
            language = form.cleaned_data['language']
            ipaddr = get_client_ip(request)
            
            # Build URL Payment
            vnp = vnpay()
            vnp.requestData['vnp_Version'] = '2.1.0'
            vnp.requestData['vnp_Command'] = 'pay'
            vnp.requestData['vnp_TmnCode'] = settings.VNPAY_TMN_CODE
            vnp.requestData['vnp_Amount'] = amount * 100
            vnp.requestData['vnp_CurrCode'] = 'VND'
            vnp.requestData['vnp_TxnRef'] = order_id
            vnp.requestData['vnp_OrderInfo'] = order_desc
            vnp.requestData['vnp_OrderType'] = order_type
            
            
            # Check language, default: vn
            if language and language != '':
                vnp.requestData['vnp_Locale'] = language
            else:
                vnp.requestData['vnp_Locale'] = 'vn'
                
            # Check bank_code, if bank_code is empty, customer will be selected bank on VNPAY
            if bank_code and bank_code != "":
                vnp.requestData['vnp_BankCode'] = bank_code

            vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
            vnp.requestData['vnp_IpAddr'] = ipaddr
            vnp.requestData['vnp_ReturnUrl'] = settings.VNPAY_RETURN_URL
            
            vnpay_payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET_KEY)
            print(vnpay_payment_url)
            return redirect(vnpay_payment_url)
        else:
            print("Form input not validate")
    else:
        # 🟢 LẤY ORDER_ID TỪ SESSION NẾU CÓ (từ checkout)
        pending_order_id = request.session.get('pending_order_id')
        initial_data = {}
        
        if pending_order_id:
            try:
                order = Order.objects.get(id=pending_order_id, user=request.user)
                initial_data = {
                    'order_id': order.id,
                    'amount': float(order.total_price),
                    'order_desc': f'Thanh toán đơn hàng #{order.id} từ RedStore',
                    'order_type': 'other',
                    'language': 'vn'
                }
            except Order.DoesNotExist:
                pass
        
        form = PaymentForm(initial=initial_data)
    
    return render(request, "payment/payment.html", {
        "title": "Thanh toán VNPay", 
        "form": form
    })


def payment_ipn(request):
    inputData = request.GET
    if inputData:
        vnp = vnpay()
        vnp.responseData = inputData.dict()
        order_id = inputData['vnp_TxnRef']
        amount = inputData['vnp_Amount']
        order_desc = inputData['vnp_OrderInfo']
        vnp_TransactionNo = inputData['vnp_TransactionNo']
        vnp_ResponseCode = inputData['vnp_ResponseCode']
        vnp_TmnCode = inputData['vnp_TmnCode']
        vnp_PayDate = inputData['vnp_PayDate']
        vnp_BankCode = inputData['vnp_BankCode']
        vnp_CardType = inputData['vnp_CardType']
        
        if vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
            # Check & Update Order Status in your Database
            # Your code here
            firstTimeUpdate = True
            totalamount = True
            if totalamount:
                if firstTimeUpdate:
                    if vnp_ResponseCode == '00':
                        print('Payment Success. Your code implement here')
                    else:
                        print('Payment Error. Your code implement here')

                    # Return VNPAY: Merchant update success
                    result = JsonResponse({'RspCode': '00', 'Message': 'Confirm Success'})
                else:
                    # Already Update
                    result = JsonResponse({'RspCode': '02', 'Message': 'Order Already Update'})
            else:
                # invalid amount
                result = JsonResponse({'RspCode': '04', 'Message': 'invalid amount'})
        else:
            # Invalid Signature
            result = JsonResponse({'RspCode': '97', 'Message': 'Invalid Signature'})
    else:
        result = JsonResponse({'RspCode': '99', 'Message': 'Invalid request'})

    return result


def payment_return(request):
    inputData = request.GET
    if inputData:
        vnp = vnpay()
        vnp.responseData = inputData.dict()
        order_id = inputData['vnp_TxnRef']
        amount = int(inputData['vnp_Amount']) / 100
        order_desc = inputData['vnp_OrderInfo']
        vnp_TransactionNo = inputData['vnp_TransactionNo']
        vnp_ResponseCode = inputData['vnp_ResponseCode']
        vnp_TmnCode = inputData['vnp_TmnCode']
        vnp_PayDate = inputData['vnp_PayDate']
        vnp_BankCode = inputData['vnp_BankCode']
        vnp_CardType = inputData['vnp_CardType']
        
        if vnp.validate_response(settings.VNPAY_HASH_SECRET_KEY):
            if vnp_ResponseCode == "00":
                # 🟢 CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG THÀNH "ĐÃ THANH TOÁN"
                try:
                    order = Order.objects.get(id=int(order_id))
                    order.status = 'paid'
                    order.payment_date = timezone.now()
                    order.transaction_id = vnp_TransactionNo
                    
                    # Xóa session
                    session_keys = ['selected_items', 'pending_order_id']
                    for key in session_keys:
                        if key in request.session:
                            del request.session[key]
                    order.save()
                    print("DEBUG USER:", request.user, request.user.is_authenticated)
                    print("SESSION KEYS:", request.session.keys())
                    # Hiển thị trang thành công
                    return render(request, "payment/payment_return.html", {
                        "title": "Kết quả thanh toán",
                        "result": "Thành công", 
                        "order_id": order_id,
                        "amount": amount,
                        "order_desc": order_desc,
                        "vnp_TransactionNo": vnp_TransactionNo,
                        "vnp_ResponseCode": vnp_ResponseCode
                    })
                    
                except Order.DoesNotExist:
                    return render(request, "payment/payment_return.html", {
                        "title": "Kết quả thanh toán",
                        "result": "Lỗi", 
                        "message": "Đơn hàng không tồn tại"
                    })
            else:
                return render(request, "payment/payment_return.html", {
                    "title": "Kết quả thanh toán",
                    "result": "Lỗi", 
                    "order_id": order_id,
                    "amount": amount,
                    "order_desc": order_desc,
                    "vnp_TransactionNo": vnp_TransactionNo,
                    "vnp_ResponseCode": vnp_ResponseCode
                })
        else:
            return render(request, "payment/payment_return.html", {
                "title": "Kết quả thanh toán", 
                "result": "Lỗi", 
                "order_id": order_id, 
                "amount": amount,
                "order_desc": order_desc, 
                "vnp_TransactionNo": vnp_TransactionNo,
                "vnp_ResponseCode": vnp_ResponseCode, 
                "msg": "Sai checksum"
            })
    else:
        return render(request, "payment/payment_return.html", {
            "title": "Kết quả thanh toán", 
            "result": ""
        })

# Generate random number for request ID
n = random.randint(10**11, 10**12 - 1)
n_str = str(n)
while len(n_str) < 12:
    n_str = '0' + n_str


def query(request):
    if request.method == 'GET':
        return render(request, "payment/query.html", {"title": "Kiểm tra kết quả giao dịch"})

    url = settings.VNPAY_API_URL
    secret_key = settings.VNPAY_HASH_SECRET_KEY
    vnp_TmnCode = settings.VNPAY_TMN_CODE
    vnp_Version = '2.1.0'

    vnp_RequestId = n_str
    vnp_Command = 'querydr'
    vnp_TxnRef = request.POST['order_id']
    vnp_OrderInfo = 'kiem tra gd'
    vnp_TransactionDate = request.POST['trans_date']
    vnp_CreateDate = datetime.now().strftime('%Y%m%d%H%M%S')
    vnp_IpAddr = get_client_ip(request)

    hash_data = "|".join([
        vnp_RequestId, vnp_Version, vnp_Command, vnp_TmnCode,
        vnp_TxnRef, vnp_TransactionDate, vnp_CreateDate,
        vnp_IpAddr, vnp_OrderInfo
    ])

    secure_hash = hmac.new(secret_key.encode(), hash_data.encode(), hashlib.sha512).hexdigest()

    data = {
        "vnp_RequestId": vnp_RequestId,
        "vnp_TmnCode": vnp_TmnCode,
        "vnp_Command": vnp_Command,
        "vnp_TxnRef": vnp_TxnRef,
        "vnp_OrderInfo": vnp_OrderInfo,
        "vnp_TransactionDate": vnp_TransactionDate,
        "vnp_CreateDate": vnp_CreateDate,
        "vnp_IpAddr": vnp_IpAddr,
        "vnp_Version": vnp_Version,
        "vnp_SecureHash": secure_hash
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = json.loads(response.text)
    else:
        response_json = {"error": f"Request failed with status code: {response.status_code}"}

    return render(request, "payment/query.html", {
        "title": "Kiểm tra kết quả giao dịch", 
        "response_json": response_json
    })


def refund(request):
    if request.method == 'GET':
        return render(request, "payment/refund.html", {"title": "Hoàn tiền giao dịch"})

    url = settings.VNPAY_API_URL
    secret_key = settings.VNPAY_HASH_SECRET_KEY
    vnp_TmnCode = settings.VNPAY_TMN_CODE
    vnp_RequestId = n_str
    vnp_Version = '2.1.0'
    vnp_Command = 'refund'
    vnp_TransactionType = request.POST['TransactionType']
    vnp_TxnRef = request.POST['order_id']
    vnp_Amount = request.POST['amount']
    vnp_OrderInfo = request.POST['order_desc']
    vnp_TransactionNo = '0'
    vnp_TransactionDate = request.POST['trans_date']
    vnp_CreateDate = datetime.now().strftime('%Y%m%d%H%M%S')
    vnp_CreateBy = 'user01'
    vnp_IpAddr = get_client_ip(request)

    hash_data = "|".join([
        vnp_RequestId, vnp_Version, vnp_Command, vnp_TmnCode, vnp_TransactionType, vnp_TxnRef,
        vnp_Amount, vnp_TransactionNo, vnp_TransactionDate, vnp_CreateBy, vnp_CreateDate,
        vnp_IpAddr, vnp_OrderInfo
    ])

    secure_hash = hmac.new(secret_key.encode(), hash_data.encode(), hashlib.sha512).hexdigest()

    data = {
        "vnp_RequestId": vnp_RequestId,
        "vnp_TmnCode": vnp_TmnCode,
        "vnp_Command": vnp_Command,
        "vnp_TxnRef": vnp_TxnRef,
        "vnp_Amount": vnp_Amount,
        "vnp_OrderInfo": vnp_OrderInfo,
        "vnp_TransactionDate": vnp_TransactionDate,
        "vnp_CreateDate": vnp_CreateDate,
        "vnp_IpAddr": vnp_IpAddr,
        "vnp_TransactionType": vnp_TransactionType,
        "vnp_TransactionNo": vnp_TransactionNo,
        "vnp_CreateBy": vnp_CreateBy,
        "vnp_Version": vnp_Version,
        "vnp_SecureHash": secure_hash
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = json.loads(response.text)
    else:
        response_json = {"error": f"Request failed with status code: {response.status_code}"}

    return render(request, "payment/refund.html", {
        "title": "Kết quả hoàn tiền giao dịch", 
        "response_json": response_json
    })


# Thêm các view mới cho integration với checkout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from datetime import datetime
import hashlib
import hmac
import urllib.parse

from cart.models import Cart, CartItem
from orders.models import Order, OrderItem 
from orders.forms import OrderForm
# payments/views.py - FIXED create_payment_from_checkout

@login_required
def create_payment_from_checkout(request):
    print(f"🔍 Method: {request.method}")
    print(f"🔍 POST data: {request.POST}")
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        shipping_address = request.POST.get('shipping_address')
        amount = request.POST.get('amount', 0)
        
        print(f"🔍 Debug - payment_method: {payment_method}")
        print(f"🔍 Debug - shipping_address: {shipping_address}")
        print(f"🔍 Debug - amount: {amount}")

        if not payment_method or not shipping_address:
            print("❌ Missing payment_method or shipping_address")
            messages.error(request, 'Thông tin thanh toán không hợp lệ!')
            return redirect('checkout')

        # 🟢 CHỈ CHẤP NHẬN BANKING CHO VIEW NÀY
        if payment_method != 'banking':
            print("❌ Wrong payment method for this view")
            messages.error(request, 'Phương thức thanh toán không hợp lệ!')
            return redirect('checkout')

        try:
            amount = float(amount)
            print(f"✅ Amount converted: {amount}")
        except (ValueError, TypeError):
            print("❌ Invalid amount")
            messages.error(request, 'Số tiền không hợp lệ!')
            return redirect('checkout')

        # 🟢 TẠO ĐƠN HÀNG
        try:
            # Lấy cart hiện tại của user
            cart = Cart.objects.get(user=request.user)
            
            # Lấy selected items từ session
            selected_items_ids = request.session.get('selected_items', [])
            if not selected_items_ids:
                messages.error(request, 'Không tìm thấy sản phẩm đã chọn!')
                return redirect('checkout')
            
            selected_items = cart.items.filter(id__in=selected_items_ids)
            if not selected_items.exists():
                messages.error(request, 'Sản phẩm đã chọn không tồn tại!')
                return redirect('checkout')
            
            # Tạo order
            order = Order.objects.create(
                user=request.user,
                cart=cart,
                shipping_address=shipping_address,
                payment_method='banking',  # 🟢 Vì đây là VNPay
                status='unpaid'
            )
            
            # Thêm selected items
            order.selected_items.set(selected_items)
            
            # 🟢 TẠO ORDER ITEMS
            for cart_item in selected_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price,
                    size=cart_item.size if cart_item.size else None
                )
            
            print(f"✅ Created Order ID: {order.id}, Total: {order.total_price}")
            
        except Cart.DoesNotExist:
            messages.error(request, 'Giỏ hàng không tồn tại!')
            return redirect('checkout')
        except Exception as e:
            print(f"❌ Error creating order: {str(e)}")
            messages.error(request, f'Lỗi tạo đơn hàng: {str(e)}')
            return redirect('checkout')

        # 🟢 XỬ LÝ VNPAY
        if payment_method == 'banking':
            try:
                vnp = vnpay()
                vnp.requestData['vnp_Version'] = '2.1.0'
                vnp.requestData['vnp_Command'] = 'pay'
                vnp.requestData['vnp_TmnCode'] = settings.VNPAY_TMN_CODE
                vnp.requestData['vnp_Amount'] = int(order.total_price * 100)
                vnp.requestData['vnp_CurrCode'] = 'VND'
                vnp.requestData['vnp_TxnRef'] = str(order.id)
                vnp.requestData['vnp_OrderInfo'] = f'Thanh toán đơn hàng #{order.id} RedStore'
                vnp.requestData['vnp_OrderType'] = 'other'
                vnp.requestData['vnp_Locale'] = 'vn'
                vnp.requestData['vnp_CreateDate'] = datetime.now().strftime('%Y%m%d%H%M%S')
                vnp.requestData['vnp_IpAddr'] = get_client_ip(request)
                vnp.requestData['vnp_ReturnUrl'] = settings.VNPAY_RETURN_URL

                # Lưu order ID vào session
                request.session['pending_order_id'] = order.id
                request.session.modified = True
                

                payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET_KEY)
                print(f"🔗 VNPay URL: {payment_url}")
                
                return redirect(payment_url)
                
            except Exception as e:
                print(f"❌ VNPay Error: {str(e)}")
                # Xóa order nếu lỗi tạo URL
                order.delete()
                messages.error(request, f'Lỗi tạo URL thanh toán: {str(e)}')
                return redirect('checkout')

    # Nếu không phải POST hoặc có lỗi
    return redirect('checkout')


# 🟢 THÊM FUNCTION GET_CLIENT_IP NỮA
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def payment_success_page(request):
    """Trang thành công"""
    return render(request, 'payment/payment_success.html')


def payment_failed_page(request):
    """Trang thất bại"""
    return render(request, 'payment/payment_failed.html')