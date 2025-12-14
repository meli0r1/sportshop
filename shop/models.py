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

    def save(self, *args, **kwargs):
        # Проверяем, изменился ли stock с 0 на >0
        old_instance = None
        if self.pk:  # если объект уже существует
            old_instance = Product.objects.get(pk=self.pk)
        
        super().save(*args, **kwargs)

        # Если остаток стал >0, а раньше был 0 — отправляем уведомления
        if old_instance and old_instance.stock == 0 and self.stock > 0:
            emails = StockNotification.objects.filter(product=self).values_list('email', flat=True)
            for email in emails:
                self.notify_of_stock(email)
            # Удаляем уведомления, чтобы не слать снова
            StockNotification.objects.filter(product=self).delete()


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
    
    def notify_of_stock(self, user_email):
        """Отправить уведомление о поступлении"""
        from django.core.mail import send_mail
        from django.conf import settings
        send_mail(
            'Товар снова в наличии!',
            f'Здравствуйте! Товар "{self.name}" снова в наличии на складе. Заходите за покупками!',
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=True,
        )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'


class StockNotification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    email = models.EmailField("Email пользователя", max_length=254)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Когда подписался")

    def __str__(self):
        return f"{self.email} → {self.product.name}"

    class Meta:
        verbose_name = "Уведомление о поступлении"
        verbose_name_plural = "Уведомления о поступлении"
        unique_together = ('product', 'email')

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    address = models.TextField("Адрес доставки", blank=True)
    telegram_id = models.CharField("Telegram ID", max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Профиль {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('shipped', 'В пути'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    total = models.DecimalField("Итого", max_digits=10, decimal_places=2)
    items = models.JSONField("Товары", default=list)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')
    tracking_number = models.CharField("Трек-номер", max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Заказ #{self.id} ({self.get_status_display()})"

    def get_tracking_url(self):
        """Возвращает URL для отслеживания на 1track.ru"""
        if self.tracking_number:
            return f"https://1track.ru/tracking/{self.tracking_number}"
        return None

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']