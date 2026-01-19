from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from .models import Table, Item, Order, GlobalSettings, TableSession

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'capacity', 'is_occupied', 'current_people')
    list_filter = ('is_occupied',)
    search_fields = ('number',)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'is_drink')
    list_filter = ('category', 'is_drink')
    search_fields = ('name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'item', 'is_paid', 'timestamp', 'transaction_price', 'order_source')
    list_filter = ('is_paid', 'order_source', 'timestamp')
    search_fields = ('description', 'table__number')
    date_hierarchy = 'timestamp'

@admin.register(TableSession)
class TableSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'table_number', 'check_out_time', 'total_amount', 'user', 'people_count')
    list_filter = ('check_out_time', 'user', 'table_number')
    search_fields = ('items_summary', 'table_number')
    date_hierarchy = 'check_out_time'
    
    # Custom tool to clear data
    change_list_template = "admin/manager/tablesession/change_list.html"

@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ('min_charge_per_person',)