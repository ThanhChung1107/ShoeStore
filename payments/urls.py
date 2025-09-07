from django.contrib import admin
from django.urls import path
import payments.views

urlpatterns = [
    path('', payments.views.index, name='index'),
    path('payment/', payments.views.payment, name='payment'),
    path('payment_ipn/', payments.views.payment_ipn, name='payment_ipn'),
    path('payment_return/', payments.views.payment_return, name='payment_return'),
    path('query/', payments.views.query, name='query'),
    path('refund/', payments.views.refund, name='refund'),
    path('admin/', admin.site.urls),

    # URLs mới cho checkout integration
    path('create_payment_from_checkout/', payments.views.create_payment_from_checkout, name='create_payment_from_checkout'),
    path('payment_success/', payments.views.payment_success_page, name='payment_success'),
    path('payment_failed/', payments.views.payment_failed_page, name='payment_failed'),
]

# Ngân hàng	NCB
# Số thẻ	9704198526191432198
# Tên chủ thẻ	NGUYEN VAN A
# Ngày phát hành	07/15
# Mật khẩu OTP	123456