import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from manager.models import Item

cafe_menu = {
    "ESPRESSO": {
        "espresso": {"S": 40, "D": 50},
        "macchiato": {"S": 45, "D": 55},
        "americano": {"S": 45, "D": 60},
        "flat_white": {"S": 55, "D": 65},
        "latte": {"S": 55, "D": 65},
        "cappuccino": {"S": 55, "D": 65},
        "cortado": {"S": 60, "D": 70},
        "mocha": {"S": 60, "D": 70}
    },
    "HOT_DRINKS": {
        "cinnamon_milk": 35,
        "tea_anise": 20,
        "flavor_tea": 30,
        "tea_latte": 35,
        "nescafe_black": 30,
        "nescafe_milk": 40,
        "hot_cider": 45,
        "hot_chocolate": 50
    },
    "COFFEE": {
        "turkish_coffee": {"S": 30, "D": 40},
        "hazelnut_coffee": {"S": 40, "D": 50},
        "french_coffee": {"S": 40, "D": 50},
        "caramel_coffee": {"S": 45, "D": 55}
    },
    "ICED_COFFEE": {
        "iced_americano": 50,
        "iced_latte": 65,
        "iced_cappuccino": 60,
        "iced_caramel_macchiato": 75,
        "iced_mocha": 70,
        "cafe_frappe": 75,
        "frappuccino_caramel": 75,
        "ice_spanish_latte": 75
    },
    "MILK_SHAKES": {
        "chocolate": 60,
        "vanilla": 60,
        "caramel": 60,
        "mango": 65,
        "strawberry": 65,
        "oreo": 75,
        "nutella": 80,
        "lotus": 85
    },
    "FRESH_JUICE": {
        "strawberry": 60,
        "guava": 60,
        "kiwi": 70,
        "mango": 60,
        "lemon": 40,
        "lemon_mint": 45
    },
    "SMOOTHIES": {
        "pineapple": 70,
        "mango": 70,
        "strawberry": 70,
        "peach": 70,
        "blueberry": 70,
        "passion_fruit": 70,
        "kiwi": 70,
        "apple": 70,
        "cherry": 70,
        "mix_smoothies": 75
    },
    "FOOD": {
        "food/sweets": 0
    }
}

def clean_name(name):
    return " ".join(word.capitalize() for word in name.split("_"))

def populate():
    # Clear existing items except Services
    Item.objects.exclude(name__in=["Printing Service", "Fax Service", "Copy Service"]).delete()
    
    # Ensure Service items exist with correct properties
    Item.objects.get_or_create(name="Printing Service", defaults={"price": 0, "is_drink": False, "category": "Services"})
    Item.objects.get_or_create(name="Fax Service", defaults={"price": 5, "is_drink": False, "category": "Services"})
    Item.objects.get_or_create(name="Copy Service", defaults={"price": 0, "is_drink": False, "category": "Services"})
    
    count = 0
    for category_id, items in cafe_menu.items():
        category_name = clean_name(category_id)
        is_drink = category_id not in ["CROISSANT", "FOOD"]
        
        for item_key, item_val in items.items():
            base_name = clean_name(item_key)
            
            if isinstance(item_val, dict):
                # Handle Single/Double
                for size_key, price in item_val.items():
                    size_name = "Single" if size_key == "S" else "Double"
                    full_name = f"{base_name} ({size_name})"
                    Item.objects.get_or_create(
                        name=full_name,
                        defaults={
                            "price": price, 
                            "category": category_name,
                            "is_drink": is_drink
                        }
                    )
                    count += 1
            else:
                # Regular item
                Item.objects.get_or_create(
                    name=base_name,
                    defaults={
                        "price": item_val, 
                        "category": category_name,
                        "is_drink": is_drink
                    }
                )
                count += 1
                
    print(f"Successfully populated {count} items.")

if __name__ == "__main__":
    populate()
