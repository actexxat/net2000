
import os
import django
import random
import datetime
from decimal import Decimal
from django.utils import timezone

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth.models import User
from manager.models import Table, Item, Order, TableSession

def create_items():
    print("Creating items...")
    items_data = [
        {"name": "Coffee", "price": 45.00, "category": "Drinks", "is_drink": True},
        {"name": "Tea", "price": 30.00, "category": "Drinks", "is_drink": True},
        {"name": "Sandwich", "price": 85.00, "category": "Food", "is_drink": False},
        {"name": "Burger", "price": 120.00, "category": "Food", "is_drink": False},
        {"name": "Cola", "price": 25.00, "category": "Drinks", "is_drink": True},
        {"name": "Cheesecake", "price": 90.00, "category": "Dessert", "is_drink": False},
        {"name": "Latte", "price": 55.00, "category": "Drinks", "is_drink": True},
        {"name": "Fries", "price": 40.00, "category": "Appetizer", "is_drink": False},
    ]
    created_items = []
    for data in items_data:
        item, created = Item.objects.get_or_create(
            name=data["name"],
            defaults=data
        )
        created_items.append(item)
    return created_items

def create_tables():
    print("Creating tables...")
    for i in range(1, 11):
        Table.objects.get_or_create(number=i)

def create_dummy_history(items):
    print("Creating history data...")
    now = timezone.now()
    admin_user = User.objects.first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin_dummy', 'admin@example.com', 'password')

    
    # Generate data for past 7 days
    for days_ago in range(8): # Today (0) to 7 days ago
        date = now - datetime.timedelta(days=days_ago)
        print(f"Generating for {date.date()}...")
        
        # Create 10-20 sessions per day
        sessions_count = random.randint(10, 20)
        
        for _ in range(sessions_count):
            hour = random.randint(9, 23) # Open from 9 AM to 11 PM
            minute = random.randint(0, 59)
            
            session_end = date.replace(hour=hour, minute=minute)
            session_start = session_end - datetime.timedelta(hours=random.randint(1, 4))
            
            table_num = random.randint(1, 10)
            
            # Orders for this session
            session_items = []
            total_amount = Decimal('0.00')
            items_summary = []
            
            # 2-5 items per session
            for _ in range(random.randint(2, 5)):
                item = random.choice(items)
                session_items.append(item)
                price = Decimal(str(item.price))
                total_amount += price
                items_summary.append(item.name)
                
                # Create Paid Order linked to this "virtual" session (for top selling items stats)
                # Note: TableSession stores 'history', Order stores individual items. 
                # Analytics uses Order for 'top selling' and TableSession for 'revenue'.
                # So we must create Order objects with proper timestamps.
                
                Order.objects.create(
                    item=item,
                    is_paid=True,
                    transaction_price=price,
                    timestamp=session_end, # Assume paid at checkout
                    description=f"Auto generated",
                    is_served=True
                )
            
            TableSession.objects.create(
                table_number=table_num,
                people_count=random.randint(1, 4),
                items_summary=", ".join(items_summary),
                total_amount=total_amount,
                check_in_time=session_start,
                check_out_time=session_end,
                user=admin_user
            )

if __name__ == "__main__":
    create_tables()
    items = create_items()
    create_dummy_history(items)
    print("Done!")
