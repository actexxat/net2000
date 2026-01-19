import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from manager.models import Order, TableSession, Table

print("Clearing application data for production...")

# 1. Delete all Orders
count_orders = Order.objects.count()
Order.objects.all().delete()
print(f"Deleted {count_orders} orders.")

# 2. Delete all TableSessions (History)
count_sessions = TableSession.objects.count()
TableSession.objects.all().delete()
print(f"Deleted {count_sessions} history sessions.")

# 3. Reset all Tables
tables = Table.objects.all()
for t in tables:
    t.is_occupied = False
    t.current_people = 0
    t.opened_at = None
    t.save()
print(f"Reset {tables.count()} tables to available status.")

print("=========================================")
print("Application data cleared successfully!")
print("Ready for production usage.")
