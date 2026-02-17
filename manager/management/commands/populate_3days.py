from django.core.management.base import BaseCommand
from manager.models import Table, Item, Order, TableSession
from django.utils import timezone
import random
import datetime
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populates the database with synthetic history data for the last 3 days with high volume'

    def handle(self, *args, **kwargs):
        self.stdout.write("Generating high-volume synthetic data for 3 days...")
        
        # Ensure we have tables
        tables = list(Table.objects.all())
        if not tables:
            self.stdout.write("Creating default tables...")
            for i in range(1, 11):
                tables.append(Table.objects.create(number=i, capacity=4))

        # Get service items
        print_item, _ = Item.objects.get_or_create(name="Printing Service", defaults={'price': 0, 'category': 'Services'})
        fax_item, _ = Item.objects.get_or_create(name="Fax Service", defaults={'price': 5, 'category': 'Services'})
        copy_item, _ = Item.objects.get_or_create(name="Copy Service", defaults={'price': 0, 'category': 'Services'})
        
        # Get regular items (drinks and food)
        regular_items = list(Item.objects.exclude(name__in=["Printing Service", "Fax Service", "Copy Service"]))

        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=2) # 3 days total

        total_sessions = 0
        total_orders = 0

        current_date = start_date
        while current_date <= end_date:
            # We want ~200 orders per day.
            # Average session has ~3 items. So ~60-70 sessions per day.
            daily_sessions_count = random.randint(60, 80)
            
            for _ in range(daily_sessions_count):
                # Pick a random hour with Rush Hour bias
                hours = list(range(10, 23)) # 10 AM to 11 PM
                weights = [3 if h in [13, 14, 15, 18, 19, 20] else 1 for h in hours]
                
                start_hour = random.choices(hours, weights=weights, k=1)[0]
                start_minute = random.randint(0, 59)
                
                check_in = timezone.make_aware(datetime.datetime.combine(current_date, datetime.time(start_hour, start_minute)))
                duration_minutes = random.randint(20, 150)
                check_out = check_in + datetime.timedelta(minutes=duration_minutes)
                
                table = random.choice(tables)
                
                # Create session
                session = TableSession.objects.create(
                    table_number=table.number,
                    people_count=random.randint(1, 4),
                    total_amount=Decimal('0.00'),
                    session_start_time=check_in
                )
                # Force update timestamps
                TableSession.objects.filter(pk=session.pk).update(checkout_time=check_out)
                
                session.refresh_from_db()

                session_total = Decimal('0.00')
                session_orders_desc = []
                
                # Each session has 1-5 random items
                num_items = random.randint(1, 5)
                for _ in range(num_items):
                    chance = random.random()
                    
                    if chance < 0.7: # 70% chance for a regular drink/item
                        it = random.choice(regular_items)
                        order_time = check_in + datetime.timedelta(minutes=random.randint(2, duration_minutes-2))
                        o = Order.objects.create(item=it, table=table, is_paid=True)
                        Order.objects.filter(pk=o.pk).update(timestamp=order_time)
                        session_total += it.price
                        session_orders_desc.append(it.name)
                        total_orders += 1
                        
                    elif chance < 0.8: # 10% chance for Printing
                        pages = random.randint(1, 50)
                        is_color = random.choice([True, False])
                        if is_color:
                            desc = f"Printing Color ({pages} pages)"
                            price = Decimal(pages * 10) # Higher price for color
                        else:
                            desc = f"Printing B/W ({pages} pages)"
                            price = Decimal(pages * 1)
                        
                        order_time = check_in + datetime.timedelta(minutes=random.randint(2, duration_minutes-2))
                        o = Order.objects.create(item=print_item, table=table, is_paid=True, description=desc, transaction_price=price)
                        Order.objects.filter(pk=o.pk).update(timestamp=order_time)
                        session_total += price
                        session_orders_desc.append(desc)
                        total_orders += 1

                    elif chance < 0.9: # 10% chance for Copy
                        pages = random.randint(1, 30)
                        is_color = random.choice([True, False])
                        if is_color:
                            desc = f"Copy Color ({pages} pages)"
                            price = Decimal(pages * 5)
                        else:
                            desc = f"Copy B/W ({pages} pages)"
                            price = Decimal(pages * 2)
                            
                        order_time = check_in + datetime.timedelta(minutes=random.randint(2, duration_minutes-2))
                        o = Order.objects.create(item=copy_item, table=table, is_paid=True, description=desc, transaction_price=price)
                        Order.objects.filter(pk=o.pk).update(timestamp=order_time)
                        session_total += price
                        session_orders_desc.append(desc)
                        total_orders += 1

                    else: # 10% chance for Fax
                        pages = random.randint(1, 5)
                        desc = f"Fax Service ({pages} pages)"
                        price = Decimal(pages * 5)
                        
                        order_time = check_in + datetime.timedelta(minutes=random.randint(2, duration_minutes-2))
                        o = Order.objects.create(item=fax_item, table=table, is_paid=True, description=desc, transaction_price=price)
                        Order.objects.filter(pk=o.pk).update(timestamp=order_time)
                        session_total += price
                        session_orders_desc.append(desc)
                        total_orders += 1

                # Update session summary
                from collections import Counter
                counts = Counter(session_orders_desc)
                summary_parts = [f"{v}x {k}" for k, v in counts.items()]
                items_summary_str = ", ".join(summary_parts)

                TableSession.objects.filter(pk=session.pk).update(
                    total_amount=session_total,
                    items_summary=items_summary_str
                )
                total_sessions += 1

            self.stdout.write(f"Generated sessions for {current_date}")
            current_date += datetime.timedelta(days=1)

        self.stdout.write(self.style.SUCCESS(f'Successfully populated {total_sessions} sessions with {total_orders} orders across 3 days.'))
