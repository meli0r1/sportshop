from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Product, Profile, Order

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'status', 'tracking_number', 'created_at']
    list_editable = ['status', 'tracking_number']  # можно менять прямо в списке
    list_filter = ['status', 'created_at', 'user']
    readonly_fields = ['items', 'created_at']
    search_fields = ['user__username', 'tracking_number']