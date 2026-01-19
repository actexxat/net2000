from django.db import models

class Table(models.Model):
    number = models.IntegerField(unique=True)
    capacity = models.IntegerField(default=50)
    is_occupied = models.BooleanField(default=False)
    current_people = models.IntegerField(default=1) 
    opened_at = models.DateTimeField(null=True, blank=True) # Track when the table was opened

    def __str__(self):
        return f"Table {self.number}"

class Item(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='items/', null=True, blank=True)
    is_drink = models.BooleanField(default=False)

    def __str__(self):
        try:
            price_str = format(self.price, '.2f')
        except Exception:
            price_str = str(self.price)
        return f"{self.name} (EGP {price_str})"

class Order(models.Model):
    ORDER_SOURCES = [
        ('DIRECT', 'Direct'),
        ('QR', 'QR Menu'),
    ]
    table = models.ForeignKey(Table, on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    transaction_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.CharField(max_length=200, null=True, blank=True)
    order_source = models.CharField(max_length=10, choices=ORDER_SOURCES, default='DIRECT')
    is_served = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['is_paid']),
            models.Index(fields=['order_source']),
        ]

    def __str__(self):
        name = self.display_name
        price = self.transaction_price if self.transaction_price is not None else (self.item.price if self.item else 0)
        table_num = self.table.number if self.table else "Unknown"
        return f"{name} ({price} EGP) for Table {table_num}"

    @property
    def item_name_display(self):
        """The core name of the ordered item. Never the note."""
        if self.item:
            return str(self.item.name)
        return str(self.description or "Quick Order")

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
    table_number = models.IntegerField()
    people_count = models.IntegerField()
    items_summary = models.TextField(default="")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    check_in_time = models.DateTimeField(auto_now_add=True)
    check_out_time = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['check_out_time']),
        ]

    def __str__(self):
        # ADD 'self.' before table_number
        return f"Table {self.table_number} - {self.check_out_time.strftime('%Y-%m-%d')}"
    

class GlobalSettings(models.Model):
    min_charge_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=25.00)

    def __str__(self):
        return "Global Space Settings"

    class Meta:
        verbose_name_plural = "Global Settings"