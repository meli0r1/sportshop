from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import Product, Profile

# Главные страницы
def index_page(request):
    products = Product.objects.all()[:6]
    return render(request, 'index.html', {'products': products})

def about_page(request):
    return render(request, 'about.html')

def catalog_page(request):
    products = Product.objects.all()
    return render(request, 'catalog.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product.html', {'product': product})

# Корзина (в сессии)
def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)
        qty = item.get('quantity', 1)
        item_total = float(product.price) * qty
        total += item_total
        cart_items.append({'product': product, 'quantity': qty, 'total': item_total})
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        cart[pid]['quantity'] += 1
    else:
        cart[pid] = {'quantity': 1}
    request.session['cart'] = cart
    messages.success(request, f'"{product.name}" добавлен в корзину!')
    return redirect('product_detail', product_id=product_id)

# Регистрация
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        if password != password2:
            messages.error(request, 'Пароли не совпадают!')
            return render(request, 'registration/register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Логин занят!')
            return render(request, 'registration/register.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email уже зарегистрирован!')
            return render(request, 'registration/register.html')
        user = User.objects.create_user(username=username, email=email, password=password)
        code = get_random_string(6, '0123456789')
        request.session['confirmation_code'] = code
        request.session['user_id'] = user.id
        send_mail('Код подтверждения', f'Ваш код: {code}', settings.DEFAULT_FROM_EMAIL, [email])
        messages.success(request, 'Проверьте email и введите код.')
        return redirect('confirm_email')
    return render(request, 'registration/register.html')

def confirm_email(request):
    if request.method == 'POST':
        code = request.POST['code']
        if code == request.session.get('confirmation_code'):
            user = User.objects.get(id=request.session['user_id'])
            login(request, user)
            messages.success(request, 'Добро пожаловать!')
            return redirect('cabinet')
        messages.error(request, 'Неверный код!')
    return render(request, 'registration/confirm_email.html')

# ЛК
@login_required
def personal_cabinet(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'cabinet.html', {'profile': profile})

@login_required
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        user.email = request.POST.get('email', user.email)
        profile.phone = request.POST.get('phone', '')
        profile.address = request.POST.get('address', '')
        user.save()
        profile.save()
        messages.success(request, 'Данные обновлены!')
        return redirect('cabinet')

    # Теперь profile точно существует
    return render(request, 'edit_profile.html', {'profile': profile})

@login_required
def checkout_page(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Корзина пуста!')
        return redirect('cart')

    # Получаем профиль (гарантируем существование)
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Обновляем данные из формы
        profile.phone = request.POST.get('phone', profile.phone)
        profile.address = request.POST.get('address', profile.address)
        profile.save()

        # Здесь можно создать заказ в БД (пока просто очищаем корзину)
        request.session['cart'] = {}
        messages.success(request, 'Заказ успешно оформлен! Спасибо за покупку!')
        return redirect('cabinet')

    # Передаём профиль и корзину в шаблон
    cart_items = []
    total = 0
    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)
        qty = item.get('quantity', 1)
        item_total = float(product.price) * qty
        total += item_total
        cart_items.append({'product': product, 'quantity': qty, 'total': item_total})

    return render(request, 'checkout.html', {
        'profile': profile,
        'cart_items': cart_items,
        'total': total
    })