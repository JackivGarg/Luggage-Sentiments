"""
generate_sample_data.py
-----------------------
Generates realistic sample luggage review data for 6 brands.
Run once to populate data/raw_data.csv, then delete this file.
"""

import csv
import random
import os

random.seed(42)

BRANDS = ["Safari", "Skybags", "American Tourister", "VIP", "Aristocrat", "Nasher Miles"]

PRODUCTS = {
    "Safari": [
        "Safari Poly-carbonate 55cm Trolley Bag",
        "Safari Pentagon 4W 77 Hardside Suitcase",
        "Safari Thorium Sharp 66cm Luggage",
        "Safari Harbour Fixed Cabin Trolley",
        "Safari Regloss Antiscratch 76cm Bag",
    ],
    "Skybags": [
        "Skybags Neo 55cm Cabin Luggage",
        "Skybags Rubik 68cm Medium Trolley",
        "Skybags Tribe 4W Strolly 79cm",
        "Skybags Oscar Polycarbonate 55cm Bag",
        "Skybags Intern Cabin 55cm Trolley",
    ],
    "American Tourister": [
        "American Tourister Ivy 68cm Spinner",
        "American Tourister Luggage Bag 55cm",
        "American Tourister Fornax 55cm Hard Case",
        "American Tourister Barcelona 79cm",
        "American Tourister Splash 77cm Trolley",
    ],
    "VIP": [
        "VIP Xion Polycarbonate 55cm Cabin Bag",
        "VIP Trace 67cm Medium Trolley",
        "VIP Voyager 79cm Large Luggage",
        "VIP Zane 4W 55cm Spinner Suitcase",
        "VIP Elanza 68cm Hard Body Trolley",
    ],
    "Aristocrat": [
        "Aristocrat Judo 55cm Cabin Trolley",
        "Aristocrat A-Line 67cm Medium Bag",
        "Aristocrat Dual 4W 79cm Large Luggage",
        "Aristocrat Photon Strolly 55cm",
        "Aristocrat Aston 68cm Spinner",
    ],
    "Nasher Miles": [
        "Nasher Miles Rome 55cm Cabin Trolley",
        "Nasher Miles Istanbul 65cm Luggage",
        "Nasher Miles Tokyo 75cm Hard Suitcase",
        "Nasher Miles Milan 55cm Polycarbonate",
        "Nasher Miles Paris 67cm Dual Tone",
    ],
}

REVIEWER_NAMES = [
    "Rahul S.", "Priya K.", "Amit M.", "Sneha R.", "Vikram J.",
    "Anjali P.", "Rohan D.", "Meera T.", "Suresh N.", "Kavita L.",
    "Deepak V.", "Pooja G.", "Arun B.", "Neha C.", "Rajesh W.",
    "Swati F.", "Manish H.", "Ritu A.", "Karan E.", "Divya U.",
    "Sanjay O.", "Anita I.", "Varun Y.", "Lakshmi Q.", "Nitin X.",
    "Geeta Z.", "Prakash M.", "Sunita D.", "Ashok R.", "Rekha S.",
]

POSITIVE_REVIEWS = [
    "Excellent quality material. The handle is sturdy and wheels are smooth. Love the build quality!",
    "Great value for money at this price. The zipper works perfectly and material feels premium.",
    "Superb durability and weight is very light. Perfect size for cabin luggage. Highly recommend!",
    "Amazing lock mechanism. The wheels glide effortlessly on any surface. Top quality product.",
    "The material is scratch resistant and the handle extends smoothly. Great quality overall.",
    "Perfect size and weight for travel. The zipper is heavy duty. Very satisfied with the price.",
    "Wheels are exceptionally smooth. The lock is TSA approved. Material quality is outstanding.",
    "Wonderful product! The handle is ergonomic-and the build quality is fantastic. Worth the price.",
    "The durability of this bag is impressive. Survived rough handling with no damage. Quality material!",
    "Light weight yet incredibly durable. The wheels rotate 360 degrees smoothly. Great quality.",
    "Best in this price range. The zipper never gets stuck. Material is water resistant. Highly durable.",
    "The quality of construction is remarkable. Handle is solid, zipper runs smooth. Great purchase!",
    "Perfect cabin size. Wheels turn freely in all directions. The material feels very premium.",
    "Love the weight distribution. Handle telescopes easily. The lock is secure and quality is top notch.",
    "Sturdy build with great quality material. The price is very reasonable for this level of durability.",
    "The zipper quality is excellent. Material is thick and durable. Wheels are butter smooth!",
    "Impressed by the weight, its so light! The handle mechanism is solid. Great quality for the price.",
    "Outstanding product. The lock works perfectly every time. Wheels have great durability.",
    "The size is perfect for a week long trip. Material quality exceeded expectations. Amazing price point.",
    "Very happy with this purchase. The handle is comfortable, wheels are quiet. Excellent quality.",
    "Premium quality at an affordable price. The durability is unmatched. Zipper is super smooth.",
    "The weight is surprisingly light for its size. Material is hard and scratch proof. Quality product!",
    "Perfect luggage! Wheels handle rough roads well. The zipper and lock are very durable.",
    "Great quality product. The material resists scratches. Handle is very solid and comfortable.",
    "Smooth wheels, sturdy handle, premium material. Everything about this bag screams quality!",
]

NEGATIVE_REVIEWS = [
    "The zipper broke after first use. Very poor quality material. Not worth the price at all.",
    "Handle snapped within a week. Wheels got stuck frequently. Terrible durability for the price.",
    "Extremely poor quality. The lock stopped working after one trip. Material is flimsy and cheap.",
    "Waste of money. The wheels fell off during airport handling. Zero durability. Horrible quality.",
    "The zipper keeps getting jammed. Material started peeling after first journey. Poor quality.",
    "Handle wobbles badly and feels unsafe. The weight is too heavy even when empty. Bad quality.",
    "Lock mechanism is faulty out of the box. The size is misleading. Quality is substandard.",
    "Material cracked on the first trip. The zipper teeth are misaligned. Terrible price to quality ratio.",
    "Worst luggage ever. The handle broke, wheels jammed, and zipper tore. No durability at all.",
    "The quality is far below what you would expect at this price. Handle and zipper both failed early.",
    "Flimsy material that dents easily. The wheels make horrible noise. Not durable at all.",
    "Regret this purchase. The lock is useless and can be opened easily. Material quality is terrible.",
    "Handle gets stuck and does not retract properly. The weight is too much. Zipper quality is poor.",
    "Do not buy. The wheels broke on the first trip. Material is thin and cheap. Wasted my money.",
    "The size seems smaller than advertised. Zipper is so stiff it hurts fingers. Horrible quality.",
    "Material scratched everywhere on first flight. Handle feels loose. Weight is misleadingly heavy.",
    "Terrible durability. The lock jammed permanently after two uses. Quality control is nonexistent.",
    "The wheels wobble and make loud noise. Zipper broke within a month. Not worth the price.",
    "Handle is uncomfortable and flimsy. The material tore at the seam. Zero quality assurance.",
    "Complete waste of money. The price does not justify this quality. Zipper and handle both failed.",
]

NEUTRAL_REVIEWS = [
    "Decent product for the price. Material is okay. The wheels work fine but nothing special.",
    "Average quality. The handle could be better. Size is standard. Weight is acceptable.",
    "Its an okay bag. The zipper works. Material is not premium but serves the purpose for the price.",
    "Nothing great, nothing terrible. The wheels are average. Quality is decent for a budget bag.",
    "Satisfactory purchase. The lock works. Material is standard quality. Size is as described.",
    "Average product overall. Handle is fine, weight is manageable. Not the best quality for the price.",
    "Gets the job done. The wheels are decent. Material quality is average. Zipper could be smoother.",
    "Standard luggage at a standard price. The durability seems okay so far. Handle is functional.",
    "Mixed feelings. The material looks good but zipper quality could improve. Wheels are average.",
    "Acceptable for the price point. The handle works fine. Quality is what you would expect.",
]


def generate_product_specs(brand):
    """Generate realistic price/mrp/rating specs per brand."""
    brand_profiles = {
        "Safari":             {"price_range": (1400, 3500), "disc_range": (25, 55), "rating_range": (3.5, 4.3)},
        "Skybags":            {"price_range": (1800, 4200), "disc_range": (20, 50), "rating_range": (3.6, 4.4)},
        "American Tourister": {"price_range": (2500, 6500), "disc_range": (15, 45), "rating_range": (3.8, 4.6)},
        "VIP":                {"price_range": (1600, 4000), "disc_range": (20, 50), "rating_range": (3.3, 4.1)},
        "Aristocrat":         {"price_range": (1300, 3200), "disc_range": (30, 60), "rating_range": (3.4, 4.2)},
        "Nasher Miles":       {"price_range": (2200, 5500), "disc_range": (10, 35), "rating_range": (3.7, 4.5)},
    }
    profile = brand_profiles[brand]
    price = round(random.uniform(*profile["price_range"]), 0)
    discount_pct = round(random.uniform(*profile["disc_range"]), 0)
    mrp = round(price / (1 - discount_pct / 100), 0)
    rating = round(random.uniform(*profile["rating_range"]), 1)
    return price, mrp, discount_pct, rating


def generate_reviews(brand, product, price, mrp, discount_pct, rating):
    """Generate between 8 and 20 reviews per product."""
    rows = []
    num_reviews = random.randint(8, 20)
    review_count = random.randint(50, 800)

    for _ in range(num_reviews):
        reviewer_name = random.choice(REVIEWER_NAMES)
        # Distribute sentiments: roughly 50% positive, 25% negative, 25% neutral
        roll = random.random()
        if roll < 0.50:
            review_text = random.choice(POSITIVE_REVIEWS)
            reviewer_rating = random.choice([4, 5])
        elif roll < 0.75:
            review_text = random.choice(NEGATIVE_REVIEWS)
            reviewer_rating = random.choice([1, 2])
        else:
            review_text = random.choice(NEUTRAL_REVIEWS)
            reviewer_rating = random.choice([3, 4])

        rows.append({
            "brand": brand,
            "product_title": product,
            "price": int(price),
            "mrp": int(mrp),
            "discount_pct": int(discount_pct),
            "rating": rating,
            "review_count": review_count,
            "reviewer_name": reviewer_name,
            "reviewer_rating": reviewer_rating,
            "review_text": review_text,
        })
    return rows


def main():
    os.makedirs("data", exist_ok=True)
    all_rows = []
    for brand in BRANDS:
        for product in PRODUCTS[brand]:
            price, mrp, discount_pct, rating = generate_product_specs(brand)
            reviews = generate_reviews(brand, product, price, mrp, discount_pct, rating)
            all_rows.extend(reviews)

    fieldnames = ["brand", "product_title", "price", "mrp", "discount_pct",
                  "rating", "review_count", "reviewer_name", "reviewer_rating", "review_text"]

    with open("data/raw_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Generated {len(all_rows)} review rows across {len(BRANDS)} brands.")
    print(f"Saved to data/raw_data.csv")


if __name__ == "__main__":
    main()
