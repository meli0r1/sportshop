from django.contrib import admin

from .models import Product, UserProfile, Order

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']
    list_editable = ['price']

# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'name', 'email', 'phone']
    search_fields = ['name', 'email', 'phone']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'profile', 'total', 'created_at']
    readonly_fields = ['items_data']