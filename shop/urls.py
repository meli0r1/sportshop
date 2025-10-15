from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_page, name='home'),
    path('about/', views.about_page, name='about'),
    path('каталог товаров/', views.catalog_page, name='catalog'),
    path('товар/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('cabinet/', views.personal_cabinet, name='cabinet'),
]