import pytest
from shop.models import Product

@pytest.mark.django_db
def test_product_creation():
    """Тест создания товара"""
    product = Product.objects.create(
        name='Футболка Nike',
        price=2000,
        stock=10
    )
    assert product.name == 'Футболка Nike'
    assert product.price == 2000
    assert product.stock == 10

@pytest.mark.django_db
def test_discount_calculation_20_percent():
    """Тест расчета скидки 20% при остатке 1 шт."""
    product = Product.objects.create(
        name='Шорты',
        price=1000,
        stock=1
    )
    discount, new_price = product.get_discount_info()
    assert discount == 20
    assert new_price == 800.0

@pytest.mark.django_db
def test_discount_calculation_10_percent():
    """Тест расчета скидки 10% при остатке 3 шт."""
    product = Product.objects.create(
        name='Кроссовки',
        price=5000,
        stock=3
    )
    discount, new_price = product.get_discount_info()
    assert discount == 10
    assert new_price == 4500.0

@pytest.mark.django_db
def test_no_discount_for_high_stock():
    """Тест отсутствия скидки при остатке > 5"""
    product = Product.objects.create(
        name='Толстовка',
        price=3000,
        stock=10
    )
    discount, new_price = product.get_discount_info()
    assert discount == 0
    assert new_price == 3000.0

import pytest
from django.contrib.auth.models import User
from shop.models import Product, Profile

@pytest.mark.django_db
def test_user_registration(client):
    """Тест регистрации пользователя"""
    response = client.post('/accounts/register/', {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'securepass123',
        'password2': 'securepass123',
    })
    assert response.status_code == 302  # редирект
    assert User.objects.filter(username='testuser').exists()

@pytest.mark.django_db
def test_catalog_page_loads(client):
    """Тест загрузки страницы каталога"""
    Product.objects.create(name='Товар 1', price=1000, stock=5)
    Product.objects.create(name='Товар 2', price=2000, stock=10)
    response = client.get('/каталог товаров/')
    assert response.status_code == 200
    assert 'Товар 1' in response.content.decode()
    assert 'Товар 2' in response.content.decode()

@pytest.mark.django_db
def test_add_to_cart_authorized(client, django_user_model):
    """Тест добавления товара в корзину авторизованным пользователем"""
    user = django_user_model.objects.create(username='buyer')
    client.force_login(user)
    product = Product.objects.create(name='Футболка', price=2000, stock=10)
    
    response = client.post(f'/cart/add/{product.id}/', {'quantity': 2})
    assert response.status_code == 302
    
    # Проверка сессии
    session = client.session
    cart = session.get('cart', {})
    assert str(product.id) in cart
    assert cart[str(product.id)]['quantity'] == 2

@pytest.mark.django_db
def test_checkout_updates_stock(client, django_user_model):
    """Тест обновления остатков при оформлении заказа"""
    # Создаём пользователя
    user = django_user_model.objects.create(
        username='buyer', 
        email='buyer@test.com'
    )
    
    # Получаем или создаём профиль (если сигнал уже создал — используем его)
    profile, created = Profile.objects.get_or_create(
        user=user,
        defaults={'phone': '+79991234567', 'address': 'Москва'}
    )
    
    # Логинимся
    client.force_login(user)
    
    # Создаём товар
    product = Product.objects.create(name='Шорты', price=3000, stock=10)
    
    # Добавляем в корзину
    client.post(f'/cart/add/{product.id}/', {'quantity': 3})
    
    # Оформляем заказ
    response = client.post('/checkout/', {
        'phone': '+79991234567',
        'address': 'Москва, ул. Пушкина, д. 1'
    })
    
    # Проверяем обновление остатка
    product.refresh_from_db()
    assert product.stock == 7  # было 10, купили 3