from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from .models import Table, Item, Order, TableSession, QuickFireItem
from infrastructure.models import GlobalSettings
from unfold.admin import ModelAdmin

@admin.register(Table)
class TableAdmin(ModelAdmin):
    list_display = ('number', 'capacity', 'is_occupied', 'current_people')
    list_filter = ('is_occupied',)
    search_fields = ('number',)

@admin.register(Item)
class ItemAdmin(ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_drink')
    list_filter = ('category', 'is_drink')
    search_fields = ('name',)

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'table', 'item', 'is_paid', 'timestamp', 'transaction_price', 'order_source')
    list_filter = ('is_paid', 'order_source', 'timestamp')
    search_fields = ('description', 'table__number')
    date_hierarchy = 'timestamp'

@admin.register(TableSession)
class TableSessionAdmin(ModelAdmin):
    list_display = ('id', 'table_number', 'checkout_time', 'total_amount', 'user', 'people_count')
    list_filter = ('checkout_time', 'user', 'table_number')
    search_fields = ('items_summary', 'table_number')
    date_hierarchy = 'checkout_time'
    
@admin.register(GlobalSettings)
class GlobalSettingsAdmin(ModelAdmin):
    list_display = ('min_charge_per_person',)

@admin.register(QuickFireItem)
class QuickFireItemAdmin(ModelAdmin):
    list_display = ('item', 'order')
    list_editable = ('order',)
    list_display_links = ('item',)
    ordering = ('order',)