from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import Product, Profile, Order
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Product, StockNotification

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

    # Обработка запроса на уведомление
    if request.method == 'POST' and request.user.is_authenticated:
        if product.stock <= 0:
            email = request.user.email
            if not StockNotification.objects.filter(product=product, email=email).exists():
                StockNotification.objects.create(product=product, email=email)
                messages.success(request, 'Вы будете уведомлены, когда товар поступит.')
            else:
                messages.info(request, 'Вы уже подписаны на уведомление.')
            return redirect('product_detail', product_id=product_id)

    return render(request, 'product.html', {'product': product})

# Корзина (в сессии)
def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)
        qty = item.get('quantity', 1)
        # Применяем скидку
        _, discounted_price = product.get_discount_info()
        item_total = discounted_price * qty
        total += item_total
        cart_items.append({
            'product': product,
            'quantity': qty,
            'total': round(item_total, 2)
        })
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': round(total, 2)})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.stock <= 0:
        messages.error(request, 'Товар закончился!')
        return redirect('product_detail', product_id=product_id)

    cart = request.session.get('cart', {})
    pid = str(product_id)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1

        # Ограничиваем количеством на складе
        if quantity > product.stock:
            messages.error(request, f'Нельзя добавить больше {product.stock} шт. (в наличии только {product.stock})')
            return redirect('product_detail', product_id=product_id)

        if pid in cart:
            new_qty = cart[pid]['quantity'] + quantity
            if new_qty > product.stock:
                messages.warning(request, f'В корзине уже есть товары. Максимум можно добавить ещё {product.stock - cart[pid]["quantity"]} шт.')
                return redirect('product_detail', product_id=product_id)
            cart[pid]['quantity'] = new_qty
        else:
            cart[pid] = {'quantity': quantity}

        request.session['cart'] = cart
        messages.success(request, f'"{product.name}" ({quantity} шт.) добавлен в корзину!')
    else:
        # Старый способ (без количества) — для совместимости
        cart[pid] = cart.get(pid, {'quantity': 0})
        if cart[pid]['quantity'] < product.stock:
            cart[pid]['quantity'] += 1
            request.session['cart'] = cart
            messages.success(request, f'"{product.name}" добавлен в корзину!')

    return redirect('product_detail', product_id=product_id)

def update_cart(request, product_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        cart = request.session.get('cart', {})
        pid = str(product_id)
        product = get_object_or_404(Product, id=product_id)

        if pid in cart:
            current_qty = cart[pid]['quantity']

            if action == 'increase':
                if current_qty < product.stock:
                    cart[pid]['quantity'] += 1
                else:
                    messages.warning(request, f'Нельзя добавить больше {product.stock} шт.')
            elif action == 'decrease':
                if current_qty > 1:
                    cart[pid]['quantity'] -= 1
                else:
                    del cart[pid]
            elif action == 'remove':
                del cart[pid]

            request.session['cart'] = cart

    return redirect('cart')

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
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'cabinet.html', {
        'profile': profile,
        'orders': orders
    })

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

    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Обновляем данные профиля
        profile.phone = request.POST.get('phone', profile.phone)
        profile.address = request.POST.get('address', profile.address)
        profile.save()

        # Проверяем и обновляем остатки
        cart_items = []
        total = 0
        errors = []

        # Собираем данные и проверяем остатки
        for product_id, item in cart.items():
            product = get_object_or_404(Product, id=product_id)
            qty = item.get('quantity', 1)
            _, discounted_price = product.get_discount_info()
            item_total = discounted_price * qty

            if qty > product.stock:
                errors.append(f'Товар "{product.name}": недостаточно на складе (в наличии {product.stock}, запрошено {qty})')
            else:
                cart_items.append({
                    'product': product,
                    'quantity': qty,
                    'total': item_total
                })
                total += item_total

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'checkout.html', {
                'profile': profile,
                'cart_items': cart_items,
                'total': round(total, 2)
            })

        # Всё ок — уменьшаем остатки и оформляем заказ
        with transaction.atomic():
            order_items = []
            for item in cart_items:
                product = item['product']
                qty = item['quantity']
                # Уменьшаем остаток
                product.stock -= qty
                product.save()
                # Сохраняем данные товара (на случай, если его удалят позже)
                order_items.append({
                    'product_id': product.id,
                    'name': product.name,
                    'price': float(product.price),
                    'discounted_price': item['total'] / qty,
                    'quantity': qty,
                    'total': item['total']
                })

                order = Order.objects.create(
                    user=request.user,
                    total=total,
                    items=order_items
                )


        # Очищаем корзину
        request.session['cart'] = {}
        messages.success(request, f'Заказ #{order.id} успешно оформлен! Спасибо за покупку!')
        return redirect('cabinet')
    # GET-запрос — показываем страницу
    cart_items = []
    total = 0
    for product_id, item in cart.items():
        product = get_object_or_404(Product, id=product_id)
        qty = item.get('quantity', 1)
        _, discounted_price = product.get_discount_info()
        item_total = discounted_price * qty
        total += item_total
        cart_items.append({
            'product': product,
            'quantity': qty,
            'total': item_total
        })

    return render(request, 'checkout.html', {
        'profile': profile,
        'cart_items': cart_items,
        'total': round(total, 2)
    })

def password_reset_code_request(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')  # логин или email
        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                messages.error(request, 'Пользователь с таким логином или email не найден.')
                return render(request, 'password_reset_request.html')

        # Генерируем код
        code = get_random_string(6, '0123456789')
        request.session['password_reset_code'] = code
        request.session['password_reset_user_id'] = user.id

        # Отправляем код на email
        try:
            send_mail(
                'Код для смены пароля — NEXUS SPORT',
                f'Ваш код подтверждения: {code}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'Код подтверждения отправлен на ваш email.')
            return redirect('password_reset_code_verify')
        except Exception:
            messages.error(request, 'Не удалось отправить письмо. Попробуйте позже.')
            return render(request, 'password_reset_request.html')

    return render(request, 'password_reset_request.html')

def password_reset_code_verify(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, 'Пароли не совпадают.')
            return render(request, 'password_reset_verify.html')

        if code == request.session.get('password_reset_code'):
            user_id = request.session.get('password_reset_user_id')
            user = User.objects.get(id=user_id)
            user.set_password(password)
            user.save()
            messages.success(request, 'Пароль успешно изменён. Войдите с новым паролем.')
            # Очищаем сессию
            del request.session['password_reset_code']
            del request.session['password_reset_user_id']
            return redirect('login')
        else:
            messages.error(request, 'Неверный код подтверждения.')

    return render(request, 'password_reset_verify.html')

def black_friday_page(request):
    # Получаем товары со скидками (остаток <= 5 и > 0)
    discounted_products = Product.objects.filter(stock__gt=0, stock__lte=5)
    
    # Пример: Чёрная пятница длится 3 дня с 29 ноября
    now = timezone.now()
    bf_start = datetime(2025, 11, 29, 0, 0, tzinfo=timezone.utc)
    bf_end = bf_start + timedelta(days=3)
    is_active = bf_start <= now <= bf_end

    return render(request, 'black_friday.html', {
        'products': discounted_products,
        'is_active': is_active,
        'bf_end': bf_end,
    })