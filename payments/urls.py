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
]
