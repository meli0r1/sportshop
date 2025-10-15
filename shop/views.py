from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Product, UserProfile, Order
import json


def index_page(request):
    return render(request, 'index.html')

def about_page(request):
    return render(request, 'about.html')

def catalog_page(request):
    products = Product.objects.all()
    return render(request, 'catalog.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product.html', {'product': product})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        cart[product_id_str]['quantity'] += 1
    else:
        cart[product_id_str] = {
            'quantity': 1
        }
    request.session['cart'] = cart
    messages.success(request, f'"{product.name}" добавлен в корзину!')
    return redirect('product_detail', product_id=product_id)


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0

    for product_id, item_data in cart.items():
        product = Product.objects.get(id=product_id)
        quantity = item_data['quantity']
        item_total = float(product.price) * quantity
        total += item_total
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total': item_total,
        })

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total
    })


def update_cart(request, product_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)

        if product_id_str in cart:
            if action == 'increase':
                cart[product_id_str]['quantity'] += 1
            elif action == 'decrease':
                if cart[product_id_str]['quantity'] > 1:
                    cart[product_id_str]['quantity'] -= 1
                else:
                    del cart[product_id_str]  # удаляем, если 0
            elif action == 'remove':
                del cart[product_id_str]

        request.session['cart'] = cart
    return redirect('cart')


def checkout(request):
    if request.method == 'POST':
        messages.success(request, 'Заказ успешно оформлен! Спасибо за покупку!')
        request.session['cart'] = {}
        return redirect('home')
    return redirect('cart')

def get_or_create_profile(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    profile, created = UserProfile.objects.get_or_create(
        session_key=session_key,
        defaults={'name': '', 'email': '', 'phone': '', 'address': ''}
    )
    return profile

def personal_cabinet(request):
    profile = get_or_create_profile(request)
    orders = Order.objects.filter(profile=profile).order_by('-created_at')

    if request.method == 'POST':
        profile.name = request.POST.get('name', '')
        profile.email = request.POST.get('email', '')
        profile.phone = request.POST.get('phone', '')
        profile.address = request.POST.get('address', '')
        profile.save()
        messages.success(request, 'Данные успешно обновлены!')
        return redirect('cabinet')

    return render(request, 'cabinet.html', {
        'profile': profile,
        'orders': orders
    })

def checkout(request):
    if request.method == 'POST':
        profile = get_or_create_profile(request)
        # Обновляем данные профиля из формы
        profile.name = request.POST.get('name')
        profile.email = request.POST.get('email')
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')
        profile.save()

        # Сохраняем заказ
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, 'Корзина пуста!')
            return redirect('cart')

        total = 0
        items_data = []
        for product_id, item in cart.items():
            product = Product.objects.get(id=product_id)
            qty = item['quantity']
            item_total = float(product.price) * qty
            total += item_total
            items_data.append({
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'quantity': qty,
                'total': item_total
            })

        order = Order.objects.create(
            profile=profile,
            total=total,
            items_data=items_data
        )

        # Очистить корзину
        request.session['cart'] = {}
        messages.success(request, f'Заказ #{order.id} успешно оформлен!')
        return redirect('cabinet')

    return redirect('cart')