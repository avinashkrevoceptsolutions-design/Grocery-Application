import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from app.database.connection import get_database
from app.domain.Users.schemas import UserRole
from app.core.config import settings
from app.core.security import hash_password

logger = logging.getLogger(__name__)

# Predefined Seed Users
SEED_ADMIN: Dict[str, Any] = {
    "first_name": settings.ADMIN_FIRST_NAME,
    "last_name": settings.ADMIN_LAST_NAME,
    "email": settings.ADMIN_EMAIL,
    "username": settings.ADMIN_USERNAME,
    "phone_number": settings.ADMIN_PHONE,
    "raw_password": settings.ADMIN_PASSWORD,
    "role": UserRole.ADMIN.value,
}

SEED_CUSTOMERS: List[Dict[str, Any]] = [
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "customer1@grocery.com",
        "username": "john_doe",
        "phone_number": "+19876543211",
        "raw_password": "Customer@12345",
        "role": UserRole.CUSTOMER.value,
    },
    {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "customer2@grocery.com",
        "username": "jane_smith",
        "phone_number": "+19876543212",
        "raw_password": "Customer@12345",
        "role": UserRole.CUSTOMER.value,
    },
]


SEED_INVENTORY: List[Dict[str, Any]] = [
    {
        "name": "Fresh Organic Bananas",
        "price": 1.89,
        "quantity_available": 200,
        "image": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=600&q=80"
    },
    {
        "name": "Organic Honeycrisp Apples",
        "price": 4.99,
        "quantity_available": 150,
        "image": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?auto=format&fit=crop&w=600&q=80"
    },
    {
        "name": "Whole Organic Milk",
        "price": 5.49,
        "quantity_available": 80,
        "image": "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=600&q=80"
    },
    {
        "name": "Pasture-Raised Grade A Eggs",
        "price": 6.29,
        "quantity_available": 100,
        "image": "https://images.unsplash.com/photo-1506976785307-8732e854ad03?auto=format&fit=crop&w=600&q=80"
    },
    {
        "name": "Artisan Sourdough Bread",
        "price": 4.79,
        "quantity_available": 60,
        "image": "https://images.unsplash.com/photo-1589367920969-ab8e050bbb04?auto=format&fit=crop&w=600&q=80"
    },
    {
        "name": "Greek Plain Yogurt",
        "price": 5.99,
        "quantity_available": 75,
        "image": "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80"
    },
    {
        "name": "Extra Virgin Olive Oil",
        "price": 12.99,
        "quantity_available": 50,
        "image": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?auto=format&fit=crop&w=600&q=80"
    },
    {
        "name": "Raw Wildflower Honey",
        "price": 8.49,
        "quantity_available": 65,
        "image": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=600&q=80"
    },
    {
        "name": "Royal Basmati Rice",
        "price": 11.99,
        "quantity_available": 90,
        "image": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=600&q=80"
    },
    {
        "name": "Boneless Chicken Breast",
        "price": 9.49,
        "quantity_available": 40,
        "image": "https://images.unsplash.com/photo-1604503468506-a8da13d82791?auto=format&fit=crop&w=600&q=80"
    }
]


async def seed_startup_data():
    """
    Idempotently seeds:
    - 1 Admin
    - 2 Customers
    - 10 Inventory Items (name, price, quantity_available: int, image)
    """
    db = get_database()
    users_col = db["users"]
    inventory_col = db["inventory"]
    now = datetime.now(timezone.utc)

    # 1. Seed Admin
    existing_admin = await users_col.find_one({
        "$or": [
            {"email": SEED_ADMIN["email"].lower()},
            {"username": SEED_ADMIN["username"].lower()}
        ]
    })
    if not existing_admin:
        admin_doc = {
            "first_name": SEED_ADMIN["first_name"],
            "last_name": SEED_ADMIN["last_name"],
            "email": SEED_ADMIN["email"].lower(),
            "username": SEED_ADMIN["username"].lower(),
            "phone_number": SEED_ADMIN["phone_number"],
            "password_hash": hash_password(SEED_ADMIN["raw_password"]),
            "role": SEED_ADMIN["role"],
            "created_at": now,
            "updated_at": now,
        }
        await users_col.insert_one(admin_doc)
        logger.info(f"Seeded Admin user: {SEED_ADMIN['username']} ({SEED_ADMIN['email']})")
    else:
        logger.info(f"Admin user already exists: {SEED_ADMIN['username']}")


    for cust in SEED_CUSTOMERS:
        existing_cust = await users_col.find_one({
            "$or": [
                {"email": cust["email"].lower()},
                {"username": cust["username"].lower()},
                {"phone_number": cust["phone_number"]}
            ]
        })
        if not existing_cust:
            cust_doc = {
                "first_name": cust["first_name"],
                "last_name": cust["last_name"],
                "email": cust["email"].lower(),
                "username": cust["username"].lower(),
                "phone_number": cust["phone_number"],
                "password_hash": hash_password(cust["raw_password"]),
                "role": cust["role"],
                "created_at": now,
                "updated_at": now,
            }
            await users_col.insert_one(cust_doc)
            logger.info(f"Seeded Customer user: {cust['username']} ({cust['email']})")
        else:
            logger.info(f"Customer user already exists: {cust['username']}")

    # 3. Seed 10 Inventory Items (Idempotent)
    for item in SEED_INVENTORY:
        qty = int(item["quantity_available"])
        clean_item = {
            "name": str(item["name"]).strip(),
            "price": float(item["price"]),
            "quantity_available": qty,
            "image": str(item["image"]).strip(),
            "status": "OUT_OF_STOCK" if qty == 0 else "IN_STOCK",
            "created_at": now,
            "updated_at": now
        }
        # Update or insert item with exact fields
        await inventory_col.replace_one(
            {"name": clean_item["name"]},
            clean_item,
            upsert=True
        )
        logger.info(f"Seeded/Synced Inventory item: {clean_item['name']}")

    logger.info("Startup data seeding completed successfully.")
