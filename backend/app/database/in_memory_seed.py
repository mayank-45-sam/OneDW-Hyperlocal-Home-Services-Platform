"""
Auto-seed demo workers into the in-memory database when the backend
starts without a real MongoDB connection. This ensures the
WorkerRecommendations page always shows results during development.
"""
from datetime import datetime, timezone
from bson import ObjectId


# Demo workers — each has a user entry + a worker-profile entry.
# Coordinates are spread across the Chennai / Tamil Nadu region.
DEMO_WORKERS = [
    {
        "user": {
            "name": "Ravi Kumar",
            "email": "ravi.electrician@demo.com",
            "phone": "9876501001",
            "role": "worker",
            "password_hash": "demo",
        },
        "profile": {
            "skills": ["Electrician", "Electrical Wiring", "AC Repair", "Fan Installation"],
            "experience_years": 8,
            "hourly_rate": 350.0,
            "bio": "Expert electrician with 8 years in residential & commercial wiring, switchboard repairs, and AC installation.",
            "is_available": True,
            "average_rating": 4.8,
            "total_jobs": 245,
            "latitude": 12.9141,
            "longitude": 80.2270,   # Thoraipakkam, Chennai
        },
    },
    {
        "user": {
            "name": "Suresh Plumber",
            "email": "suresh.plumber@demo.com",
            "phone": "9876501002",
            "role": "worker",
            "password_hash": "demo",
        },
        "profile": {
            "skills": ["Plumber", "Plumbing", "Pipe Repair", "Bathroom Fitting", "Water Heater"],
            "experience_years": 10,
            "hourly_rate": 300.0,
            "bio": "Certified plumber specialising in pipeline repair, bathroom fittings, and geyser installation.",
            "is_available": True,
            "average_rating": 4.6,
            "total_jobs": 312,
            "latitude": 12.8406,
            "longitude": 80.1534,   # Tambaram
        },
    },
    {
        "user": {
            "name": "Anand Carpenter",
            "email": "anand.carpenter@demo.com",
            "phone": "9876501003",
            "role": "worker",
            "password_hash": "demo",
        },
        "profile": {
            "skills": ["Carpenter", "Carpentry", "Furniture Assembly", "Door Repair", "Wardrobe"],
            "experience_years": 12,
            "hourly_rate": 400.0,
            "bio": "Master carpenter for custom furniture, modular kitchens, wardrobes, and door/window repair.",
            "is_available": True,
            "average_rating": 4.9,
            "total_jobs": 178,
            "latitude": 12.9716,
            "longitude": 80.2209,   # Sholinganallur
        },
    },
    {
        "user": {
            "name": "Meena Cleaner",
            "email": "meena.cleaning@demo.com",
            "phone": "9876501004",
            "role": "worker",
            "password_hash": "demo",
        },
        "profile": {
            "skills": ["Cleaning", "Home Cleaning", "Deep Cleaning", "Sofa Cleaning", "Kitchen Cleaning"],
            "experience_years": 5,
            "hourly_rate": 250.0,
            "bio": "Professional home cleaning specialist — deep cleaning, sofa/carpet cleaning, and kitchen scrubbing.",
            "is_available": True,
            "average_rating": 4.7,
            "total_jobs": 421,
            "latitude": 12.9010,
            "longitude": 80.2278,   # Perungudi
        },
    },
    {
        "user": {
            "name": "Karthik AC Tech",
            "email": "karthik.ac@demo.com",
            "phone": "9876501005",
            "role": "worker",
            "password_hash": "demo",
        },
        "profile": {
            "skills": ["AC Repair", "AC Service", "AC Installation", "Electrician", "Appliance Repair"],
            "experience_years": 7,
            "hourly_rate": 500.0,
            "bio": "Certified AC technician — installation, gas refilling, servicing, and cooling-problem diagnosis for all brands.",
            "is_available": True,
            "average_rating": 4.5,
            "total_jobs": 189,
            "latitude": 12.8956,
            "longitude": 80.1400,   # Chrompet
        },
    },
    {
        "user": {
            "name": "Priya Painter",
            "email": "priya.painter@demo.com",
            "phone": "9876501006",
            "role": "worker",
            "password_hash": "demo",
        },
        "profile": {
            "skills": ["Painter", "Painting", "Interior Painting", "Exterior Painting", "Waterproofing"],
            "experience_years": 9,
            "hourly_rate": 380.0,
            "bio": "Skilled painter for interior/exterior walls, waterproofing, texture finishes, and wood polishing.",
            "is_available": True,
            "average_rating": 4.7,
            "total_jobs": 203,
            "latitude": 12.9580,
            "longitude": 80.1975,   # Velachery
        },
    },
    {
        "user": {
            "name": "Vijay Mechanic",
            "email": "vijay.mechanic@demo.com",
            "phone": "9876501007",
            "role": "worker",
            "password_hash": "demo",
        },
        "profile": {
            "skills": ["Mechanic", "Appliance Repair", "Washing Machine Repair", "Refrigerator Repair", "Microwave Repair"],
            "experience_years": 6,
            "hourly_rate": 320.0,
            "bio": "Home appliance repair expert — washing machines, refrigerators, microwaves, and geysers.",
            "is_available": True,
            "average_rating": 4.4,
            "total_jobs": 156,
            "latitude": 13.0067,
            "longitude": 80.2206,   # Anna Nagar
        },
    },
    {
        "user": {
            "name": "Siva Plumber Pro",
            "email": "siva.plumber@demo.com",
            "phone": "9876501008",
            "role": "worker",
            "password_hash": "demo",
        },
        "profile": {
            "skills": ["Plumber", "Plumbing", "Drainage Cleaning", "Tap Repair", "Water Tank Cleaning"],
            "experience_years": 4,
            "hourly_rate": 280.0,
            "bio": "Quick-response plumber for tap leaks, drainage clogs, bathroom fittings, and water tank maintenance.",
            "is_available": True,
            "average_rating": 4.3,
            "total_jobs": 98,
            "latitude": 12.9236,
            "longitude": 80.1258,   # Default center (Chengalpattu area)
        },
    },
]


async def seed_demo_workers(db) -> None:
    """Insert demo workers into the in-memory database at startup."""
    now = datetime.now(timezone.utc)

    for entry in DEMO_WORKERS:
        user_data = entry["user"]
        profile_data = entry["profile"]

        # Create user document
        user_doc = {
            "_id": ObjectId(),
            "name": user_data["name"],
            "email": user_data["email"],
            "phone": user_data["phone"],
            "role": "worker",
            "password_hash": user_data.get("password_hash", "demo"),
            "is_active": True,
            "created_at": now,
        }
        user_result = await db.users.insert_one(user_doc)
        user_id = str(user_result.inserted_id)

        # Create worker profile document
        worker_doc = {
            "_id": ObjectId(),
            "user_id": user_id,
            "skills": profile_data["skills"],
            "experience_years": profile_data["experience_years"],
            "hourly_rate": profile_data["hourly_rate"],
            "bio": profile_data["bio"],
            "is_available": profile_data["is_available"],
            "average_rating": profile_data["average_rating"],
            "total_jobs": profile_data["total_jobs"],
            "latitude": profile_data["latitude"],
            "longitude": profile_data["longitude"],
            "created_at": now,
            "updated_at": now,
        }
        await db.workers.insert_one(worker_doc)
