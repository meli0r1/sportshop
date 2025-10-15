from django.db import models


class Product(models.Model):
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    image = models.ImageField('Изображение', upload_to='products/', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

class UserProfile(models.Model):
    session_key = models.CharField(max_length=100, unique=True, verbose_name="Ключ сессии")
    name = models.CharField("Имя", max_length=100, blank=True)
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    address = models.TextField("Адрес доставки", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Профиль ({self.session_key})"

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

class Order(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="Профиль")
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField("Сумма", max_digits=10, decimal_places=2)
    items_data = models.JSONField("Товары", help_text="Данные о товарах в формате JSON")

    def __str__(self):
        return f"Заказ #{self.id} от {self.created_at.strftime('%d.%m.%Y')}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
