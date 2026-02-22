from django.db import models
from django.utils.translation import gettext_lazy as _

class Table(models.Model):
    number = models.IntegerField(unique=True, verbose_name=_("Number"))
    capacity = models.IntegerField(default=50, verbose_name=_("Capacity"))
    is_occupied = models.BooleanField(default=False, verbose_name=_("Is Occupied"))
    current_people = models.IntegerField(default=1, verbose_name=_("Current People")) 
    opened_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Opened At")) # Track when the table was opened
    pending_reset = models.BooleanField(default=False, verbose_name=_("Pending Reset"))

    class Meta:
        verbose_name = _("Table")
        verbose_name_plural = _("Tables")

    def __str__(self):
        return _("Table %s") % self.number

    def get_bill_summary(self, settings=None):
        """
        Calculates totals, shortfall, and active orders for the table.
        Minimum Charge Policy: Only items marked as 'is_drink' count towards the minimum charge coverage.
        Non-drink items (food, services, etc.) are added on top of the minimum charge/drink total.
        """
        from decimal import Decimal
        from infrastructure.models import GlobalSettings
        
        if not settings:
            settings, _ = GlobalSettings.objects.get_or_create(id=1)
        
        # Get active orders
        if hasattr(self, 'active_orders'):
            unpaid_orders = self.active_orders
        else:
            unpaid_orders = list(self.order_set.filter(is_paid=False).select_related('item').order_by('timestamp'))
        
        
        order_total = Decimal('0.00')

        for order in unpaid_orders:
            # Calculate effective price
            price = order.transaction_price if order.transaction_price is not None else (order.item.price if order.item else Decimal('0.00'))
            price = price or Decimal('0.00')
            order_total += price
            
        # Calculate totals and shortfall per person
        min_charge = Decimal(str(settings.min_charge_per_person))
        
        shortfall = Decimal('0.00')
        progress = 100  # Default

        if self.number != 0 and min_charge > Decimal('0.00'):
            total_target = Decimal(self.current_people) * min_charge
            
            # New Logic: No-Pooling - Each drink contributes at most min_charge to total coverage.
            # However, the total covered amount should NOT be capped at total_target,
            # as excess from one person's drinks can't cover another's shortfall (as per user clarification).
            
            covered_amount = Decimal('0.00')
            for order in unpaid_orders:
                if order.item and order.item.is_drink:
                    price = order.transaction_price if order.transaction_price is not None else order.item.price
                    price = Decimal(str(price or '0.00'))
                    # Each drink contributes at most min_charge towards meeting the overall minimum
                    contribution = min(price, min_charge)
                    covered_amount += contribution
            
            # Shortfall is the difference between the total target and the covered amount, cannot be negative.
            shortfall = max(Decimal('0.00'), total_target - covered_amount)
            
            if total_target > 0:
                # Progress is based on how much is covered vs. the target, capped at 100%.
                # Use covered_amount as is, it's already summed up contributions (capped per drink).
                progress = int((min(covered_amount, total_target) / total_target) * 100)
            else:
                progress = 100        
        
        return {
            'orders': unpaid_orders,
            'order_total': order_total,
            'shortfall': shortfall,
            'final_total': order_total + shortfall,
            'progress': progress
        }

class Item(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name=_("Price"))
    category = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Category"))
    image = models.ImageField(upload_to='items/', null=True, blank=True, verbose_name=_("Image"))
    is_drink = models.BooleanField(default=False, verbose_name=_("Is Drink"))

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")

    def __str__(self):
        try:
            price_str = format(self.price, '.2f')
        except Exception:
            price_str = str(self.price)
        return _("%s (EGP %s)") % (self.name, price_str)

class Order(models.Model):
    ORDER_SOURCES = [
        ('DIRECT', _('Direct')),
        ('QR', _('QR Menu')),
    ]
    table = models.ForeignKey(Table, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Table"))
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Item"))
    is_paid = models.BooleanField(default=False, verbose_name=_("Is Paid"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Timestamp"))
    transaction_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Transaction Price"))
    description = models.CharField(max_length=200, null=True, blank=True, verbose_name=_("Description"))
    order_source = models.CharField(max_length=10, choices=ORDER_SOURCES, default='DIRECT', verbose_name=_("Order Source"))
    is_served = models.BooleanField(default=False, verbose_name=_("Is Served"))
    shift = models.CharField(max_length=10, choices=[(_('MORNING'), _('Morning')), (_('NIGHT'), _('Night'))], default='MORNING', verbose_name=_("Shift"))
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Paid At"))

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['is_paid']),
            models.Index(fields=['order_source']),
        ]
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self):
        name = self.item_name_display
        price = self.transaction_price if self.transaction_price is not None else (self.item.price if self.item else 0)
        table_num = self.table.number if self.table else _("Unknown")
        return _("%(name)s (%(price)s EGP) for Table %(table_num)s") % {'name': name, 'price': price, 'table_num': table_num}

    @property
    def item_name_display(self):
        """The core name of the ordered item. Never the note."""
        if self.item:
            return str(self.item.name)
        return str(self.description or _("Quick Order"))

    @property
    def item_category_display(self):
        """The category of the item."""
        if self.item and self.item.category:
            return str(self.item.category)
        return ""

    @property
    def customer_note_display(self):
        """The customer's instructions for this order."""
        if self.order_source == 'QR' and self.description:
            return str(self.description)
        # For DIRECT orders, if an item is linked, the description contains details (e.g., 'B/W 5 pages').
        # If no item is linked, the description is the main name (handled by item_name_display).
        if self.order_source == 'DIRECT' and self.item and self.description:
            return str(self.description)
        return ""

class TableSession(models.Model):
    SHIFT_CHOICES = [(_('MORNING'), _('Morning')), (_('NIGHT'), _('Night'))]
    table_number = models.IntegerField(verbose_name=_("Table Number"))
    people_count = models.IntegerField(verbose_name=_("People Count"))
    items_summary = models.TextField(default="", verbose_name=_("Items Summary"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Total Amount"))
    session_start_time = models.DateTimeField(auto_now_add=True, verbose_name=_("Session Start Time"))
    checkout_time = models.DateTimeField(null=True, blank=True, verbose_name=_("Checkout Time"))
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, default='MORNING', verbose_name=_("Shift"))
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("User"))

    class Meta:
        indexes = [
            models.Index(fields=['checkout_time']),
        ]
        verbose_name = _("Table Session")
        verbose_name_plural = _("Table Sessions")

    def __str__(self):
        # ADD 'self.' before table_number
        return _("Table %s - %s") % (self.table_number, self.checkout_time.strftime('%d/%m/%Y')) if self.checkout_time else _("Table %s - Open") % self.table_number

    


class StickyNote(models.Model):
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name=_("Author"))
    content = models.TextField(blank=True, verbose_name=_("Content"))
    color = models.CharField(max_length=50, default='bg-soft-yellow', verbose_name=_("Color")) # CSS class or hex
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Sticky Note")
        verbose_name_plural = _("Sticky Notes")

    def __str__(self):
        return _("Note by %s") % self.author.username

class QuickFireItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='quickfire_items', verbose_name=_("Item"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    class Meta:
        ordering = ['order']
        verbose_name = _("Quick Fire Item")
        verbose_name_plural = _("Quick Fire Items")

    def __str__(self):
        return _("%s (Order %s)") % (self.item.name, self.order)

class ActionLog(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("User"))
    action_type = models.CharField(max_length=50, verbose_name=_("Action Type")) # 'ORDER', 'PRINT', 'COPY', 'CHECKIN', 'CHECKOUT', etc.
    details = models.TextField(verbose_name=_("Details"))
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Table"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Timestamp"))

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _("Action Log")
        verbose_name_plural = _("Action Logs")

    def __str__(self):
        return _("%(user)s - %(action_type)s - %(timestamp)s") % {'user': self.user, 'action_type': self.action_type, 'timestamp': self.timestamp}