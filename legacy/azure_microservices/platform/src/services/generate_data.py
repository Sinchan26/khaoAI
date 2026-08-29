import json
import random
import os

random.seed(42)

LOCATIONS = [
    "Salt Lake, Sector V",
    "Salt Lake, Sector I",
    "Park Street",
    "New Town, Action Area 1",
    "Ballygunge",
    "Indiranagar, Bangalore",
    "Koramangala, Bangalore",
    "HSR Layout, Bangalore",
    "Bandra West, Mumbai",
    "Connaught Place, Delhi"
]

CUISINES = [
    "North Indian", "Bengali", "South Indian", "Chinese", "Mughlai",
    "Biryani", "Fast Food", "Street Food", "Bakery & Desserts", "Healthy Bowls",
    "Italian & Pizza", "Continental", "Rolls & Wraps", "Chai & Snacks", "Cafe"
]

MEAL_TYPES = ["breakfast", "lunch", "snacks", "dinner", "late_night"]

TOMATO_RESTAURANT_NAMES = [
    "Arsalan Royal Biryani", "Aminia Heritage Mughlai", "Mocambo Continental",
    "Peter Cat Grill", "Flurys Heritage Tearoom", "Balaram Mullick Sweets",
    "Kusum Rolls Corner", "6 Ballygunge Place", "Bhojohori Manna",
    "Chowman Chinese Kitchen", "Mainland China", "Kewpie's Bengali Kitchen",
    "Tung Fong Express", "Barbeque Nation", "Oudh 1590",
    "Shiraz Golden Restaurant", "Dada Boudi Biryani", "Wow! Momo Kitchen",
    "Haldiram's Pure Delights", "Bikkgane Biryani Hub", "Bikanervala Sweets",
    "Sagar Ratna South Delights", "Saravana Bhavan South Express", "Udupi Grand",
    "Madras Tiffin Room", "The Daily Cafe", "Blue Tokai Coffee & Bakes",
    "Roastery Coffee House", "8th Day Cafe & Bakery", "Subway Fresh Subs",
    "Domino's Pizza Point", "La Pino'z Pizza Hub", "Burger King Junction",
    "KFC Crispy Corner", "McDonald's Express", "Nando's Flame Grill",
    "Chai Point Station", "Chaayos Chai & Bites", "Tibbs Frankie House",
    "Faasos Flavour Wraps", "Behrouz Royal Biryani", "Sweet Truth Confections",
    "The Good Bowl", "LunchBox Daily Homely Meals", "Firangi Bake",
    "Biryani By Kilo", "Gourmet Cloud Kitchen", "Punjab Grill Express",
    "Barista Lavazza Cafe", "Costa Coffee Brews"
]

TWIGGY_RESTAURANT_NAMES = [
    "Arsalan Express", "Royal Aminia Cloud", "Mocambo Classic Diner",
    "Peter Cat Sizzlers & Grill", "Flurys Patisserie & Cafe", "Mithai Mandir & Sweets",
    "Hot Kathi Roll Factory", "Kolkata Biryani House", "Oh! Calcutta Fine Dining",
    "Hao Chi Dimsum & Bowls", "Golden Dragon Oriental", "Saptapadi Bengali Thali",
    "Wok Express Asian Street", "Barbeque Delight Express", "Oudh Nawabi Flavours",
    "Royal Shiraz Heritage", "Barrackpore Special Dada Boudi", "Momo King & More",
    "Bikaji Express & Snacks", "Biryani Central", "Gupta Brothers Mithai & Tiffin",
    "Murugan Idli Express", "Swamy's South Kitchen", "Karnataka Dosa Corner",
    "Dakshin Tiffin House", "Arts Cafe & Bistro", "Third Wave Coffee Roasters",
    "Craft Coffee Express", "Bakers Studio & Bakery", "Green Salad & Subs",
    "Pizza Express Craft Kitchen", "Ovenstory Gourmet Pizza", "Biggies Burger Junction",
    "Fried Chicken Factory", "Smash Burgers & Shakes", "Chili's Grill & Bites",
    "Keventers Shakes & Bites", "Chai Days & Pakoras", "Rolls Mania Express",
    "Wrap-It-Up Kathi Rolls", "Royal Dastarkhwan Biryani", "The Belgian Waffle Co",
    "Fit Food Bowl Co", "Ghar Ka Khana Homestyle", "Pasta La Vista",
    "Charcoal Eats Biryani", "Cloud Feast Kitchen", "Dhaba by Punjab Grill",
    "Brew & Bite Cafe", "Starbucks Quick Delivery"
]

SAMPLE_DISHES = {
    "breakfast": [
        ("Masala Dosa with Sambar & Chutneys", 120, True, "South Indian"),
        ("Idli Vada Combo (2 Idli + 1 Vada)", 90, True, "South Indian"),
        ("Club Kachori with Aloo Sabzi (4 pcs)", 70, True, "Street Food"),
        ("Poha with Sev & Peanuts", 60, True, "Healthy Bowls"),
        ("Aloo Paratha with Curd & Butter", 110, True, "North Indian"),
        ("Paneer Paratha with Pickle", 140, True, "North Indian"),
        ("Egg & Cheese Toast Sandwich", 120, False, "Fast Food"),
        ("English Breakfast Platter", 280, False, "Continental"),
        ("Masala Omelette with Brown Bread", 95, False, "Cafe"),
        ("Luchi with Chholar Dal (4 pcs)", 110, True, "Bengali"),
        ("Radhabhallavi with Dum Aloo", 130, True, "Bengali"),
        ("Overnight Oats & Fresh Fruits Bowl", 180, True, "Healthy Bowls"),
        ("Pancakes with Maple Syrup & Butter", 190, True, "Bakery & Desserts"),
        ("Filter Coffee & Medu Vada Combo", 85, True, "South Indian"),
        ("Chole Bhature (2 Bhature + Chole)", 150, True, "North Indian")
    ],
    "lunch": [
        ("Special Kolkata Mutton Biryani with Aloo & Egg", 340, False, "Biryani"),
        ("Chicken Dum Biryani (Hyderabadi Style)", 280, False, "Biryani"),
        ("Veg Dum Biryani with Salan & Raita", 210, True, "Biryani"),
        ("Chicken Butter Masala with 2 Butter Naan", 290, False, "North Indian"),
        ("Paneer Butter Masala with 2 Tandoori Roti", 240, True, "North Indian"),
        ("Dal Makhani & Jeera Rice Meal Bowl", 190, True, "North Indian"),
        ("Fish Kalia (Katla) with Steamed Rice", 260, False, "Bengali"),
        ("Kosha Mangsho (Mutton) with 3 Parathas", 380, False, "Bengali"),
        ("Grand Bengali Veg Thali", 220, True, "Bengali"),
        ("Schezwan Chicken Fried Rice & Chilli Chicken Combo", 260, False, "Chinese"),
        ("Veg Hakka Noodles & Manchurian Gravy", 210, True, "Chinese"),
        ("Grilled Chicken Salad with Vinaigrette", 250, False, "Healthy Bowls"),
        ("Paneer Tikka Rice Bowl", 210, True, "Healthy Bowls"),
        ("Tandoori Chicken Full (4 pcs)", 420, False, "Mughlai"),
        ("Shahi Paneer Thali with Rice & Paratha", 230, True, "North Indian")
    ],
    "snacks": [
        ("Double Chicken Double Egg Roll", 140, False, "Rolls & Wraps"),
        ("Single Egg Paneer Kathi Roll", 110, False, "Rolls & Wraps"),
        ("Special Vegetable Kathi Roll", 85, True, "Rolls & Wraps"),
        ("Steamed Chicken Momos (6 pcs) with Spicy Chutney", 130, False, "Street Food"),
        ("Crispy Pan Fried Veg Momos (6 pcs)", 110, True, "Street Food"),
        ("Samosa & Masala Chai Combo (2 pcs)", 65, True, "Chai & Snacks"),
        ("Pani Puri / Puchka Platter (8 pcs)", 60, True, "Street Food"),
        ("Pav Bhaji with Extra Butter Pav (2 pcs)", 130, True, "Street Food"),
        ("Crispy French Fries Large with Peri Peri", 110, True, "Fast Food"),
        ("Chicken Popcorn Box with Garlic Mayo", 160, False, "Fast Food"),
        ("Veg Grilled Cheese Sandwich", 120, True, "Cafe"),
        ("Chicken Club Sandwich 3-Tier", 190, False, "Cafe"),
        ("Nutella Waffle with Chocolate Ice Cream", 160, True, "Bakery & Desserts"),
        ("Hot Gulab Jamun (2 pcs) with Rabdi", 90, True, "Bakery & Desserts"),
        ("Cold Coffee with Vanilla Scoop", 120, True, "Cafe")
    ],
    "dinner": [
        ("Awadhi Mutton Biryani (Full Handi)", 390, False, "Biryani"),
        ("Chicken Tikka Biryani with Burani Raita", 310, False, "Biryani"),
        ("Murgh Musallam Half with 2 Roomali Roti", 360, False, "Mughlai"),
        ("Kadhai Paneer with 2 Garlic Naan", 260, True, "North Indian"),
        ("Chicken Bharta with 3 Roomali Rotis", 280, False, "North Indian"),
        ("Yellow Dal Tadka with Kashmiri Pulao", 180, True, "North Indian"),
        ("Prawn Malai Curry with Basmati Rice", 390, False, "Bengali"),
        ("Bhetki Paturi (2 pcs) with Steamed Rice", 350, False, "Bengali"),
        ("Kung Pao Chicken with Egg Fried Rice", 290, False, "Chinese"),
        ("Veg Singapore Noodles with Chilli Paneer", 240, True, "Chinese"),
        ("Farmhouse Gourmet Pizza (10 inch)", 350, True, "Italian & Pizza"),
        ("Smoky BBQ Chicken Pizza (10 inch)", 420, False, "Italian & Pizza"),
        ("Chelo Kebab Platter with Buttered Rice", 430, False, "Continental"),
        ("Creamy White Sauce Pasta (Penne Alfredo)", 250, True, "Italian & Pizza"),
        ("Mutton Rogan Josh with 2 Laccha Paratha", 390, False, "North Indian")
    ],
    "late_night": [
        ("Midnight Chicken Biryani Bowl", 240, False, "Biryani"),
        ("Crispy Chicken Burger & Fries Combo", 190, False, "Fast Food"),
        ("Veg Double Patty Cheese Burger", 150, True, "Fast Food"),
        ("Spicy Maggi with Cheese & Veggies", 85, True, "Chai & Snacks"),
        ("Egg Chicken Maggi Bowl", 110, False, "Chai & Snacks"),
        ("Chicken Shawarma Roll", 130, False, "Rolls & Wraps"),
        ("Loaded Cheesy Nachos with Salsa", 160, True, "Fast Food"),
        ("Chocolate Lava Cake with Vanilla Dip", 110, True, "Bakery & Desserts"),
        ("Red Velvet Pastry Slice", 95, True, "Bakery & Desserts"),
        ("Classic Pepperoni Pizza (8 inch)", 290, False, "Italian & Pizza"),
        ("Margherita Cheese Pizza (8 inch)", 210, True, "Italian & Pizza"),
        ("Chicken Wings in Hot Buffalo Sauce (6 pcs)", 220, False, "Fast Food"),
        ("Midnight Cold Brew & Brownie Box", 170, True, "Cafe"),
        ("Crispy Aloo Tikki Wrap", 90, True, "Rolls & Wraps"),
        ("Butter Chicken Naan Roll", 160, False, "Rolls & Wraps")
    ]
}

def generate_platform_data(platform_name: str, names: list[str], price_modifier: float = 1.0, delivery_offset: int = 0):
    restaurants = []
    menu_items = []
    item_id_counter = 1

    for idx, r_name in enumerate(names, start=1):
        loc = random.choice(LOCATIONS)
        base_rating = round(random.uniform(3.6, 4.9), 1)
        base_delivery = random.choice([20, 25, 30, 35, 40, 45]) + delivery_offset
        cuisine_type = random.choice(CUISINES)

        rest_id = f"{platform_name[:3].lower()}_rest_{idx:03d}"
        restaurants.append({
            "id": rest_id,
            "name": r_name,
            "platform": platform_name,
            "location": loc,
            "cuisine": cuisine_type,
            "rating": base_rating,
            "ratings_count": random.randint(150, 4800),
            "avg_delivery_time_mins": max(15, base_delivery),
            "price_for_two": random.randint(300, 1100),
            "is_pure_veg": random.random() < 0.25,
            "is_open": True
        })

        # Generate ~15 items per restaurant across meal times
        for meal_t in MEAL_TYPES:
            candidates = SAMPLE_DISHES[meal_t]
            # Pick 3 items per meal type = 15 items total
            picked = random.sample(candidates, 3)
            for dish_name, base_price, is_veg, dish_cuisine in picked:
                # Add slight variation per restaurant & platform
                adjusted_price = int(round(base_price * price_modifier * random.uniform(0.9, 1.15) / 5.0) * 5)
                dish_rating = round(min(5.0, max(3.2, base_rating + random.uniform(-0.3, 0.3))), 1)
                item_delivery = max(15, base_delivery + random.randint(-5, 5))

                menu_items.append({
                    "id": f"{platform_name[:3].lower()}_item_{item_id_counter:04d}",
                    "restaurant_id": rest_id,
                    "restaurant_name": r_name,
                    "platform": platform_name,
                    "location": loc,
                    "name": dish_name,
                    "price": adjusted_price,
                    "meal_type": meal_t,
                    "cuisine": dish_cuisine,
                    "is_veg": is_veg,
                    "rating": dish_rating,
                    "ratings_count": random.randint(30, 1200),
                    "delivery_time_mins": item_delivery,
                    "description": f"Delicious fresh {dish_name.lower()} prepared with authentic ingredients.",
                    "image_url": f"https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&auto=format&fit=crop&q=60"
                })
                item_id_counter += 1

    return restaurants, menu_items

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Generate Tomato data (slightly different pricing & delivery)
    tomato_rests, tomato_items = generate_platform_data("Tomato", TOMATO_RESTAURANT_NAMES, price_modifier=0.98, delivery_offset=0)
    tomato_dir = os.path.join(base_dir, "tomato_simulator", "data")
    os.makedirs(tomato_dir, exist_ok=True)
    with open(os.path.join(tomato_dir, "restaurants.json"), "w", encoding="utf-8") as f:
        json.dump(tomato_rests, f, indent=2, ensure_ascii=False)
    with open(os.path.join(tomato_dir, "menu_items.json"), "w", encoding="utf-8") as f:
        json.dump(tomato_items, f, indent=2, ensure_ascii=False)
    print(f"Generated Tomato data: {len(tomato_rests)} restaurants, {len(tomato_items)} items")

    # Generate Twiggy data
    twiggy_rests, twiggy_items = generate_platform_data("Twiggy", TWIGGY_RESTAURANT_NAMES, price_modifier=1.02, delivery_offset=-3)
    twiggy_dir = os.path.join(base_dir, "twiggy_simulator", "data")
    os.makedirs(twiggy_dir, exist_ok=True)
    with open(os.path.join(twiggy_dir, "restaurants.json"), "w", encoding="utf-8") as f:
        json.dump(twiggy_rests, f, indent=2, ensure_ascii=False)
    with open(os.path.join(twiggy_dir, "menu_items.json"), "w", encoding="utf-8") as f:
        json.dump(twiggy_items, f, indent=2, ensure_ascii=False)
    print(f"Generated Twiggy data: {len(twiggy_rests)} restaurants, {len(twiggy_items)} items")

if __name__ == "__main__":
    main()
