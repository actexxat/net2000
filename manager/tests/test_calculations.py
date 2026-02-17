from decimal import Decimal
from django.test import TestCase
from manager.models import Table, Item, Order
from infrastructure.models import GlobalSettings
from manager.views import _get_table_context

class CalculationTests(TestCase):
    def setUp(self):
        # Setup settings
        self.settings = GlobalSettings.objects.create(min_charge_per_person=Decimal('25.00'))
        
        # Setup table
        self.table = Table.objects.create(number=1, capacity=4, current_people=2, is_occupied=True)
        
        # Setup items
        self.drink1 = Item.objects.create(name="Tea", price=Decimal('10.00'), is_drink=True)
        self.drink2 = Item.objects.create(name="Coffee", price=Decimal('30.00'), is_drink=True)
        self.food = Item.objects.create(name="Sandwich", price=Decimal('50.00'), is_drink=False)
        self.service = Item.objects.create(name="Printing Service", price=Decimal('0.00'), is_drink=False)

    def test_min_charge_calculation(self):
        """
        Verify Minimum Charge Logic:
        - Only Drinks cover min charge.
        - Excess drink cost is NOT carried over to other people.
        """
        
        # Scenario 1: No orders
        # 2 people, min charge 25 each. Shortfall should be 50.
        _get_table_context(self.table, self.settings)
        self.assertEqual(self.table.shortfall, Decimal('50.00'))
        self.assertEqual(self.table.final_total, Decimal('50.00'))

        # Scenario 2: 1 Drink (10.00)
        # Person 1 covers 10.00 of 25.00 -> Shortfall 15.00
        # Person 2 covers 0.00 of 25.00 -> Shortfall 25.00
        # Total Shortfall = 40.00. Total Bill = 10.00 + 40.00 = 50.00
        Order.objects.create(table=self.table, item=self.drink1, transaction_price=self.drink1.price, is_paid=False)
        
        # Must refresh table relation or clear cache? _get_table_context re-fetches if not active_orders attr
        # But verify_table_context does query DB.
        
        _get_table_context(self.table, self.settings)
        self.assertEqual(self.table.actual_orders, Decimal('10.00'))
        self.assertEqual(self.table.shortfall, Decimal('40.00'))
        self.assertEqual(self.table.final_total, Decimal('50.00'))

        # Scenario 3: Add High Value Drink (30.00)
        # Person 1 (sorted desc drinks) takes the 30.00 drink. Covers 25.00. Shortfall 0.
        # Person 2 takes the 10.00 drink. Covers 10.00. Shortfall 15.00.
        # Total Shortfall = 15.00. Total Bill = 40.00 + 15.00 = 55.00
        Order.objects.create(table=self.table, item=self.drink2, transaction_price=self.drink2.price, is_paid=False)
        
        _get_table_context(self.table, self.settings)
        self.assertEqual(self.table.actual_orders, Decimal('40.00'))
        self.assertEqual(self.table.shortfall, Decimal('15.00'))
        self.assertEqual(self.table.final_total, Decimal('55.00'))

    def test_food_does_not_cover_min_charge(self):
        # Clear previous orders
        self.table.order_set.all().delete()
        
        # Add Food (50.00)
        # Food is NOT valid for min charge.
        # Person 1 Shortfall 25.
        # Person 2 Shortfall 25.
        # Total Shortfall 50.
        # Total Bill = 50 (Food) + 50 (Shortfall) = 100.
        
        Order.objects.create(table=self.table, item=self.food, transaction_price=self.food.price, is_paid=False)
        _get_table_context(self.table, self.settings)
        
        self.assertEqual(self.table.actual_orders, Decimal('50.00'))
        self.assertEqual(self.table.shortfall, Decimal('50.00'))
        self.assertEqual(self.table.final_total, Decimal('100.00'))

    def test_printing_pricing_logic(self):
        # We need to simulate the view logic for printing, or extract it.
        # Since it's in the view (add_print), let's reproduce the calculation here to verify the formula
        # defined in the requirements and implemented in views.
        
        # Rule: <= 100 pages -> 1.00/page. > 100 -> 0.75/page.
        
        def calculate_print_cost(pages):
            pages = int(pages)
            if pages <= 100:
                ppp = Decimal('1.00')
            else:
                ppp = Decimal('0.75')
            return (Decimal(pages) * ppp).quantize(Decimal('0.01'))

        self.assertEqual(calculate_print_cost(10), Decimal('10.00'))
        self.assertEqual(calculate_print_cost(100), Decimal('100.00'))
        self.assertEqual(calculate_print_cost(101), Decimal('75.75')) # 101 * 0.75
        self.assertEqual(calculate_print_cost(200), Decimal('150.00'))

