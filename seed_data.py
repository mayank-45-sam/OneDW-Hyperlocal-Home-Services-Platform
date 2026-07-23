"""
Seed script: inserts sample workers and service requests into MongoDB for testing.
Run from the backend/ directory:
    python seed_data.py

This creates:
  - 6 worker users with profiles, locations, skills, and ratings
  - 5 sample service requests in 'pending' state
  - 3 sample completed bookings
  - 3 sample ratings
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import random

# Ensure app package is importable
sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.utils.security import hash_password

WORKERS = [
    {
        "name": "Ravi Kumar",
        "email": "ravi.electrician@test.com",
        "phone": "9876543210",
        "role": "worker",
        "skills": ["Electrician"],
        "experience_years": 8,
        "hourly_rate": 350.0,
        "bio": "Certified electrician with 8 years experience in residential & commercial wiring.",
        "is_available": True,
        "average_rating": 4.8,
        "total_jobs": 124,
        "latitude": 12.9236,
        "longitude": 80.1258,  # Tambaram area
    },
    {
        "name": "Suresh Babu",
        "email": "suresh.plumber@test.com",
        "phone": "9876543211",
        "role": "worker",
        "skills": ["Plumber", "Water Tank Cleaning"],
        "experience_years": 5,
        "hourly_rate": 300.0,
        "bio": "Experienced plumber specialising in bathroom fittings and pipe repairs.",
        "is_available": True,
        "average_rating": 4.5,
        "total_jobs": 87,
        "latitude": 12.9400,
        "longitude": 80.1350,
    },
    {
        "name": "Kannan Selvam",
        "email": "kannan.carpenter@test.com",
        "phone": "9876543212",
        "role": "worker",
        "skills": ["Carpenter"],
        "experience_years": 12,
        "hourly_rate": 400.0,
        "bio": "Master carpenter with expertise in custom furniture and door installations.",
        "is_available": True,
        "average_rating": 4.9,
        "total_jobs": 210,
        "latitude": 11.9416,
        "longitude": 79.8083,  # Puducherry
    },
    {
        "name": "Priya Lakshmi",
        "email": "priya.cleaning@test.com",
        "phone": "9876543213",
        "role": "worker",
        "skills": ["Cleaning"],
        "experience_years": 3,
        "hourly_rate": 250.0,
        "bio": "Professional deep cleaning service for homes and offices.",
        "is_available": True,
        "average_rating": 4.6,
        "total_jobs": 56,
        "latitude": 12.9500,
        "longitude": 80.1400,
    },
    {
        "name": "Murugan AC",
        "email": "murugan.ac@test.com",
        "phone": "9876543214",
        "role": "worker",
        "skills": ["AC Repair", "Appliance Repair"],
        "experience_years": 7,
        "hourly_rate": 500.0,
        "bio": "Authorised AC technician for all major brands. Fast and reliable service.",
        "is_available": True,
        "average_rating": 4.7,
        "total_jobs": 98,
        "latitude": 12.9250,
        "longitude": 80.1300,
    },
    {
        "name": "Deepak Painter",
        "email": "deepak.painter@test.com",
        "phone": "9876543215",
        "role": "worker",
        "skills": ["Painter"],
        "experience_years": 6,
        "hourly_rate": 320.0,
        "bio": "Interior and exterior painting specialist with premium finishes.",
        "is_available": False,  # Offline worker for testing filter
        "average_rating": 4.3,
        "total_jobs": 72,
        "latitude": 12.9600,
        "longitude": 80.1500,
    },
]

SAMPLE_REQUESTS = [
    {
        "service_type": "Electrician",
        "location": "Tambaram, Chennai",
        "latitude": 12.9236,
        "longitude": 80.1258,
        "description": "Fan stopped working and main circuit breaker trips frequently.",
        "preferred_date": "2026-07-25",
        "preferred_time": "10:00",
        "status": "pending",
    },
    {
        "service_type": "Plumber",
        "location": "Velachery, Chennai",
        "latitude": 12.9800,
        "longitude": 80.2185,
        "description": "Kitchen sink is clogged and bathroom tap leaking.",
        "preferred_date": "2026-07-24",
        "preferred_time": "09:00",
        "status": "pending",
    },
    {
        "service_type": "Cleaning",
        "location": "Anna Nagar, Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "description": "Need thorough house cleaning for 3BHK apartment before shifting in.",
        "preferred_date": "2026-07-26",
        "preferred_time": "08:00",
        "status": "pending",
    },
    {
        "service_type": "AC Repair",
        "location": "Puducherry",
        "latitude": 11.9416,
        "longitude": 79.8083,
        "description": "1.5 ton split AC not cooling, showing E2 error code.",
        "preferred_date": "2026-07-24",
        "preferred_time": "11:00",
        "status": "pending",
    },
    {
        "service_type": "Carpenter",
        "location": "Tambaram, Chennai",
        "latitude": 12.9236,
        "longitude": 80.1258,
        "description": "Main door hinge broken, need replacement and aligning.",
        "preferred_date": "2026-07-25",
        "preferred_time": "14:00",
        "status": "pending",
    },
]


async def seed():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]

    print(f"🔗 Connected to MongoDB: {settings.mongodb_db_name}")

    # Create a dummy customer for seeding requests
    existing_customer = await db.users.find_one({"email": "test.customer@test.com"})
    if not existing_customer:
        customer_doc = {
            "name": "Test Customer",
            "email": "test.customer@test.com",
            "phone": "9000000001",
            "password": hash_password("password123"),
            "role": "customer",
            "is_verified": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = await db.users.insert_one(customer_doc)
        customer_id = str(result.inserted_id)
        print(f"✅ Created test customer: test.customer@test.com / password123 (id={customer_id})")
    else:
        customer_id = str(existing_customer["_id"])
        print(f"ℹ️  Test customer already exists (id={customer_id})")

    # Seed workers
    worker_ids = []
    for w in WORKERS:
        existing = await db.users.find_one({"email": w["email"]})
        if existing:
            worker_ids.append(str(existing["_id"]))
            print(f"ℹ️  Worker already exists: {w['email']}")
            continue

        user_doc = {
            "name": w["name"],
            "email": w["email"],
            "phone": w["phone"],
            "password": hash_password("password123"),
            "role": "worker",
            "is_verified": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        user_result = await db.users.insert_one(user_doc)
        user_id = str(user_result.inserted_id)
        worker_ids.append(user_id)

        profile_doc = {
            "user_id": user_id,
            "skills": w["skills"],
            "experience_years": w["experience_years"],
            "hourly_rate": w["hourly_rate"],
            "bio": w["bio"],
            "is_available": w["is_available"],
            "average_rating": w["average_rating"],
            "total_jobs": w["total_jobs"],
            "latitude": w["latitude"],
            "longitude": w["longitude"],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await db.workers.insert_one(profile_doc)
        print(f"✅ Created worker: {w['name']} ({', '.join(w['skills'])})")

    # Seed requests
    req_ids = []
    for req in SAMPLE_REQUESTS:
        doc = {**req, "customer_id": customer_id, "created_at": datetime.now(timezone.utc)}
        result = await db.requests.insert_one(doc)
        req_ids.append(str(result.inserted_id))
        print(f"✅ Created request: {req['service_type']} @ {req['location']}")

    print("\n🎉 Seed complete!")
    print(f"   Workers: {len(worker_ids)} | Requests: {len(req_ids)}")
    print(f"\n📝 Test Login Credentials:")
    print(f"   Customer: test.customer@test.com / password123")
    for w in WORKERS:
        print(f"   Worker ({w['name']}): {w['email']} / password123")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
