from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index_page, name='home'),
    path('about/', views.about_page, name='about'),
    path('каталог товаров/', views.catalog_page, name='catalog'),
    path('товар/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),


    # Аккаунт
    path('accounts/register/', views.register, name='register'),
    path('accounts/confirm/', views.confirm_email, name='confirm_email'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # ЛК
    path('cabinet/', views.personal_cabinet, name='cabinet'),
    path('cabinet/edit/', views.edit_profile, name='edit_profile'),
    path('checkout/', views.checkout_page, name='checkout_page'),
]