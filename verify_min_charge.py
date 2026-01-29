import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from manager.models import Table, Item, Order, GlobalSettings

def run_verification():
    print("--- Verifying Minimum Charge Logic ---")
    
    # 1. Setup Data
    # Ensure Global Settings min charge is 25
    settings, _ = GlobalSettings.objects.get_or_create(id=1)
    if settings.min_charge_per_person != 25.00:
        print(f"Updating Min Charge from {settings.min_charge_per_person} to 25.00")
        settings.min_charge_per_person = Decimal('25.00')
        settings.save()
        
    # Create/Get Items
    drink_item, _ = Item.objects.get_or_create(name="Test Drink", defaults={'price': 25.00, 'is_drink': True})
    drink_item.is_drink = True # Ensure it is true
    drink_item.price = Decimal('25.00')
    drink_item.save()
    
    non_drink_item, _ = Item.objects.get_or_create(name="Test Print", defaults={'price': 100.00, 'is_drink': False})
    non_drink_item.is_drink = False # Ensure it is false
    non_drink_item.price = Decimal('100.00')
    non_drink_item.save()
    
    # Create Table
    table, _ = Table.objects.get_or_create(number=999, defaults={'capacity': 4})
    table.is_occupied = True
    table.current_people = 2
    table.save()
    
    # Clear existing orders
    table.order_set.all().delete()
    
    print(f"Table {table.number} initialized with {table.current_people} people.")
    print(f"Target: {table.current_people} * 25 = 50.00")
    
    # SCENARIO 1: No Orders
    s1 = table.get_bill_summary(settings)
    print("\n--- Scenario 1: No Orders ---")
    print(f"Orders: {s1['order_total']}, Shortfall: {s1['shortfall']}, Final: {s1['final_total']}, Progress: {s1['progress']}%")
    # Expected: Shortfall 50, Final 50, Progress 0
    
    # SCENARIO 2: 1 Drink (25) + 1 Print (100)
    # Total Spend: 125. Eligible Spend: 25. Target: 50. Shortfall: 25.
    Order.objects.create(table=table, item=drink_item, transaction_price=25.00)
    Order.objects.create(table=table, item=non_drink_item, transaction_price=100.00)
    
    s2 = table.get_bill_summary(settings)
    print("\n--- Scenario 2: 1 Drink (25) + 1 Print (100) ---")
    print(f"Orders: {s2['order_total']}, Shortfall: {s2['shortfall']}, Final: {s2['final_total']}, Progress: {s2['progress']}%")
    # Expected: Orders 125, Shortfall 25, Final 150, Progress 50%
    
    # SCENARIO 3: 2 Drinks (25 each) + 1 Print (100)
    # Total Spend: 150. Eligible Spend: 50. Target: 50. Shortfall: 0.
    Order.objects.create(table=table, item=drink_item, transaction_price=25.00)
    
    s3 = table.get_bill_summary(settings)
    print("\n--- Scenario 3: 2 Drinks (50 total) + 1 Print (100) ---")
    print(f"Orders: {s3['order_total']}, Shortfall: {s3['shortfall']}, Final: {s3['final_total']}, Progress: {s3['progress']}%")
    # Expected: Orders 150, Shortfall 0, Final 150, Progress 100%

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    run_verification()
