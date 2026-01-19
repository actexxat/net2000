import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from manager.models import Table, Item, Order, GlobalSettings
from manager.views import _get_table_context

def test_user_scenario():
    print("--- Running User Scenario: 2 people, 1 Spanish Latte (75) ---")
    
    settings = GlobalSettings.objects.get(id=1)
    settings.min_charge_per_person = Decimal('25.00')
    settings.save()
    
    table, _ = Table.objects.get_or_create(number=88, defaults={'capacity': 4})
    table.is_occupied = True
    table.current_people = 2
    table.save()
    
    Order.objects.filter(table=table, is_paid=False).delete()
    
    latte, _ = Item.objects.get_or_create(name="Ice Spanish Latte", defaults={'price': 75, 'is_drink': True})
    Order.objects.create(table=table, item=latte)
    
    _get_table_context(table, settings)
    
    print(f"Table People: {table.current_people}")
    print(f"Min Charge: {settings.min_charge_per_person}")
    print(f"Item Price: {latte.price}")
    print(f"Actual Orders: {table.actual_orders}")
    print(f"Shortfall: {table.shortfall}")
    print(f"Final Total: {table.final_total}")
    
    # Expected: 75 + 25 = 100
    if table.final_total == Decimal('100.00'):
        print("\n[SUCCESS] Code logic matches EXPECTED result (100.00)")
    else:
        print(f"\n[FAILURE] Code logic resulted in {table.final_total}, NOT 100.00")

if __name__ == "__main__":
    test_user_scenario()
