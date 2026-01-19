from django.contrib import admin
from .models import Table, Item, Order, GlobalSettings, TableSession

admin.site.register(Table)
admin.site.register(Item)
admin.site.register(Order)
admin.site.register(GlobalSettings)
admin.site.register(TableSession)