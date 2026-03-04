from django.contrib import admin
from .models import Table, Item, Order, TableSession, QuickFireItem, ActionLog
from unfold.admin import ModelAdmin
from unfold.decorators import display
from django.utils.translation import gettext_lazy as _

@admin.register(Table)
class TableAdmin(ModelAdmin):
    list_display = ('number', 'capacity', 'status_badge', 'current_people')
    list_filter = ('is_occupied',)
    search_fields = ('number',)
    list_editable = ('capacity',)
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        (_("Configuration"), {
            "fields": ("number", "capacity"),
        }),
        (_("Live State"), {
            "fields": ("is_occupied", "current_people", "opened_at", "pending_reset"),
        }),
    )

    @display(description=_("Status"), label={
        True: "danger",
        False: "success",
    })
    def status_badge(self, obj):
        return _("Occupied") if obj.is_occupied else _("Available")

@admin.register(Item)
class ItemAdmin(ModelAdmin):
    list_display = ('name', 'price', 'category_badge', 'drink_badge')
    list_filter = ('category', 'is_drink')
    search_fields = ('name',)
    list_editable = ('price',)
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        (_("Basic Information"), {
            "fields": ("name", "price", "category", "is_drink"),
        }),
        (_("Media"), {
            "fields": ("image",),
        }),
    )

    @display(description=_("Category"), label=True)
    def category_badge(self, obj):
        return obj.category or _("Uncategorized"), "info"

    @display(description=_("Type"), label={
        True: "info",
        False: "warning",
    })
    def drink_badge(self, obj):
        return _("Drink") if obj.is_drink else _("Other")

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('item_display', 'table', 'price_display', 'paid_status', 'timestamp_display', 'source_badge')
    list_filter = ('is_paid', 'order_source', 'shift', 'timestamp')
    search_fields = ('description', 'table__number', 'item__name')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'paid_at')
    autocomplete_fields = ('table', 'item')
    compressed_fields = True
    warn_unsaved_form = True

    fieldsets = (
        (_("Selection"), {
            "fields": ("table", "item"),
        }),
        (_("Transaction Details"), {
            "fields": ("transaction_price", "is_paid", "paid_at"),
        }),
        (_("Context"), {
            "fields": ("description", "order_source", "shift", "timestamp", "is_served"),
        }),
    )
    
    @display(description=_("Item"))
    def item_display(self, obj):
        return obj.item_name_display

    @display(description=_("Price"), header=True)
    def price_display(self, obj):
        p = obj.transaction_price if obj.transaction_price is not None else (obj.item.price if obj.item else 0)
        return f"{p:.2f} EGP"

    @display(description=_("Paid"), label={
        True: "success",
        False: "danger",
    })
    def paid_status(self, obj):
        return _("Paid") if obj.is_paid else _("Unpaid")

    @display(description=_("Source"), label=True)
    def source_badge(self, obj):
        return obj.get_order_source_display(), "info"

    @display(description=_("Time"))
    def timestamp_display(self, obj):
        return obj.timestamp.strftime("%H:%M")

@admin.register(TableSession)
class TableSessionAdmin(ModelAdmin):
    list_display = ('table_number', 'checkout_time_display', 'total_amount_display', 'user', 'people_count', 'shift_badge')
    list_filter = ('checkout_time', 'user', 'shift', 'table_number')
    search_fields = ('items_summary', 'table_number')
    date_hierarchy = 'checkout_time'
    readonly_fields = ('checkout_time', 'session_start_time')
    compressed_fields = True

    fieldsets = (
        (_("Session Overview"), {
            "fields": ("table_number", "people_count", "total_amount", "shift", "user"),
        }),
        (_("Timestamps"), {
            "fields": ("session_start_time", "checkout_time"),
        }),
        (_("Order Summary"), {
            "classes": ["collapse"],
            "fields": ("items_summary",),
        }),
    )

    @display(description=_("Checkout"), header=True)
    def checkout_time_display(self, obj):
        return obj.checkout_time.strftime("%d/%m/%Y %H:%M") if obj.checkout_time else "-"

    @display(description=_("Total"), header=True)
    def total_amount_display(self, obj):
        return f"{obj.total_amount:.2f} EGP"

    @display(description=_("Shift"), label=True)
    def shift_badge(self, obj):
        return obj.get_shift_display(), "info"

@admin.register(QuickFireItem)
class QuickFireItemAdmin(ModelAdmin):
    list_display = ('item', 'order')
    list_editable = ('order',)
    list_display_links = ('item',)
    ordering = ('order',)

@admin.register(ActionLog)
class ActionLogAdmin(ModelAdmin):
    list_display = ('user', 'action_type_badge', 'table', 'timestamp_display')
    list_filter = ('action_type', 'user', 'timestamp')
    search_fields = ('details', 'user__username', 'table__number')
    readonly_fields = ('timestamp',)
    compressed_fields = True

    fieldsets = (
        (_("Identity"), {
            "fields": ("user", "table"),
        }),
        (_("Action"), {
            "fields": ("action_type", "details"),
        }),
        (_("Timestamp"), {
            "fields": ("timestamp",),
        }),
    )

    @display(description=_("Action"), label=True)
    def action_type_badge(self, obj):
        return obj.action_type, "info"

    @display(description=_("Time"))
    def timestamp_display(self, obj):
        last_local = obj.timestamp
        return last_local.strftime("%d/%m/%Y %H:%M")