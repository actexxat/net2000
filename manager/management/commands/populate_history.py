from django.core.management.base import BaseCommand
from manager.models import Table, Item, Order, TableSession
from django.utils import timezone
import random
import datetime
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populates the database with synthetic history data for the last 60 days'

    def handle(self, *args, **kwargs):
        self.stdout.write("Generating synthetic data...")
        
        # Ensure we have tables
        tables = list(Table.objects.all())
        if not tables:
            self.stdout.write("Creating default tables...")
            for i in range(1, 11):
                tables.append(Table.objects.create(number=i, capacity=4))

        # Ensure we have basic items
        items = list(Item.objects.all())
        if not items:
            self.stdout.write("Creating default items...")
            items = [
                Item.objects.create(name="Coffee", price=25, category="Hot Drinks"),
                Item.objects.create(name="Tea", price=15, category="Hot Drinks"),
                Item.objects.create(name="Cola", price=20, category="Cold Drinks"),
                Item.objects.create(name="Sandwich", price=45, category="Food"),
            ]

        # Ensure Printing Service item
        print_item, _ = Item.objects.get_or_create(name="Printing Service", defaults={'price': 0, 'category': 'Services'})

        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=60)

        total_sessions = 0

        # Loop through each day
        current_date = start_date
        while current_date <= end_date:
            # Random volume: 15 to 40 sessions
            daily_volume = random.randint(15, 40)
            
            for _ in range(daily_volume):
                # Pick a random hour with Rush Hour bias (14:00 and 18:00)
                # Weights for hours 9-22
                hours = list(range(9, 23))
                weights = []
                for h in hours:
                    if h in [13, 14, 15]: # Rush 1
                        weights.append(3)
                    elif h in [17, 18, 19]: # Rush 2
                        weights.append(3)
                    else:
                        weights.append(1)
                
                start_hour = random.choices(hours, weights=weights, k=1)[0]
                start_minute = random.randint(0, 59)
                
                check_in = timezone.make_aware(datetime.datetime.combine(current_date, datetime.time(start_hour, start_minute)))
                # Duration 30m to 3h
                duration_minutes = random.randint(30, 180)
                check_out = check_in + datetime.timedelta(minutes=duration_minutes)
                
                table = random.choice(tables)
                
                # Create session (timestamps will be auto-set to now initially)
                session = TableSession.objects.create(
                    table_number=table.number,
                    people_count=random.randint(1, 4),
                    total_amount=Decimal('0.00')
                )
                
                # Force update timestamps to historical values
                TableSession.objects.filter(pk=session.pk).update(
                    check_in_time=check_in,
                    check_out_time=check_out
                )
                
                # Re-fetch to have correct data if needed (though we use session.pk mostly)
                session.refresh_from_db()

                # Create Orders & Build Summary
                # 1-4 random regular items
                num_items = random.randint(1, 4)
                session_total = Decimal('0.00')
                session_orders_desc = []
                
                for _ in range(num_items):
                    it = random.choice(items)
                    if it.name == "Printing Service":
                        continue
                    
                    order_time = check_in + datetime.timedelta(minutes=random.randint(5, duration_minutes-5))
                    o = Order.objects.create(
                        item=it,
                        table=table,
                        is_paid=True
                    )
                    # Fix timestamp and is_paid (create sets is_paid=True, but timestamp needs update)
                    Order.objects.filter(pk=o.pk).update(timestamp=order_time)
                    
                    session_total += it.price
                    session_orders_desc.append(it.name)

                # Printing Chance (20%)
                if random.random() < 0.2:
                    is_color = random.choice([True, False])
                    pages = random.randint(1, 20)
                    
                    if is_color:
                        desc = f"Printing Color ({pages} pages)"
                        price = Decimal(pages * 5)
                    else:
                        desc = f"Printing B/W ({pages} pages)"
                        price = Decimal(pages * 1)
                    
                    print_order_time = check_in + datetime.timedelta(minutes=random.randint(5, duration_minutes-5))
                    po = Order.objects.create(
                        item=print_item,
                        table=table,
                        is_paid=True,
                        description=desc,
                        transaction_price=price
                    )
                    Order.objects.filter(pk=po.pk).update(timestamp=print_order_time)
                    
                    session_total += price
                    # For summary, usually we aggregate, but here detailed list is fine or simple summary
                    session_orders_desc.append(desc)

                # Summarize items for TableSession.items_summary
                # e.g. "Coffee, Sandwich, ..."
                # Ideally, we group: "2x Coffee, 1x Sandwich"
                from collections import Counter
                counts = Counter(session_orders_desc)
                summary_parts = [f"{v}x {k}" for k, v in counts.items()]
                items_summary_str = ", ".join(summary_parts)

                # Update session total and summary
                TableSession.objects.filter(pk=session.pk).update(
                    total_amount=session_total,
                    items_summary=items_summary_str
                )
                
                total_sessions += 1

            current_date += datetime.timedelta(days=1)
            self.stdout.write(f"Generated {daily_volume} sessions for {current_date}")

        self.stdout.write(self.style.SUCCESS(f'Successfully populated {total_sessions} sessions across 60 days.'))
