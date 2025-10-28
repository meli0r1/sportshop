from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Product(models.Model):
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    image = models.ImageField('Изображение', upload_to='products/', blank=True, null=True)
    stock = models.PositiveIntegerField('Остаток на складе')

    def get_discount_info(self):
        """Скидка только на малые остатки"""
        stock = self.stock
        if stock == 0:
            discount = 0
        elif stock == 1:
            discount = 20
        elif 2 <= stock <= 3:
            discount = 10
        elif 4 <= stock <= 5:
            discount = 5
        else:
            discount = 0  # 6 и больше — без скидки
        new_price = float(self.price) * (1 - discount / 100)
        return discount, round(new_price, 2)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    address = models.TextField("Адрес доставки", blank=True)

    def __str__(self):
        return f"Профиль {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    total = models.DecimalField("Итого", max_digits=10, decimal_places=2)
    # Сохраняем состав заказа как JSON (название, цена, количество)
    items = models.JSONField("Товары", default=list)

    def __str__(self):
        return f"Заказ #{self.id} от {self.created_at.strftime('%d.%m.%Y %H:%M')}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']