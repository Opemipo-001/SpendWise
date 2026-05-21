from django.contrib import admin
from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type')
    search_fields = ('name',)
    list_filter = ('category_type',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'transaction_type', 'amount', 'date')
    search_fields = ('user__username', 'description')
    list_filter = ('transaction_type', 'category', 'date')