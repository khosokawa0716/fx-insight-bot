"""
Initialize Firestore with initial configuration data
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.utils.firestore_client import get_db
from src.models.firestore import SystemConfig


def init_system_config():
    """Create initial system configuration"""
    db = get_db()

    # Signal rules configuration
    signal_rules_config = {
        "config_id": "signal_rules",
        "version": "v1.0",
        "active": True,
        "config_data": {
            "buy_conditions": {
                "sentiment_min": 1,
                "impact_usdjpy_min": 5,
                "topics": ["金融政策", "経済指標"],
            },
            "sell_conditions": {
                "sentiment_max": -1,
                "impact_usdjpy_min": 5,
            },
            "risk_off_conditions": {
                "sentiment_max": -2,
                "topics": ["地政学"],
            },
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    # Save to Firestore
    doc_ref = db.collection("system_config").document("signal_rules")
    doc_ref.set(signal_rules_config)

    print(f"✅ Created system_config/signal_rules")
    print(f"   Version: {signal_rules_config['version']}")
    print(f"   Active: {signal_rules_config['active']}")

    return signal_rules_config


def verify_firestore_connection():
    """Verify Firestore connection"""
    try:
        db = get_db()
        collections = list(db.collections())
        print(f"✅ Connected to Firestore")
        print(f"   Collections: {[c.id for c in collections]}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Firestore: {e}")
        return False


def main():
    """Main initialization function"""
    print("=" * 60)
    print("Firestore Initialization Script")
    print("=" * 60)
    print()

    # Step 1: Verify connection
    print("Step 1: Verifying Firestore connection...")
    if not verify_firestore_connection():
        print("\n❌ Initialization failed: Cannot connect to Firestore")
        return

    print()

    # Step 2: Create initial system config
    print("Step 2: Creating initial system configuration...")
    try:
        init_system_config()
    except Exception as e:
        print(f"❌ Failed to create system config: {e}")
        return

    print()
    print("=" * 60)
    print("✅ Firestore initialization completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
