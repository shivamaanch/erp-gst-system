"""
Test script to verify add milk route is working correctly
"""

import requests
import json

def test_add_milk_entry():
    """Test adding a milk entry with the correct Milk Chief data"""
    
    # Flask app URL
    base_url = "http://127.0.0.1:5000"
    
    # Test data (same as our Milk Chief test)
    test_data = {
        "txn_date": "2026-04-02",
        "shift": "Morning",
        "txn_type": "Purchase",
        "party_id": "1",  # Assuming party ID 1 exists
        "qty_liters": "897",
        "fat": "43",  # Will be converted to 4.3
        "clr": "295",  # Will be converted to 29.5
        "rate_per_liter": "4850",  # Rate per 100kg
        "create_invoice": "1",
        "manual_bill_no": "",
        "gst_rate": "",
        "narration": "Test Milk Chief calculation"
    }
    
    print("🧪 Testing Add Milk Entry Route")
    print("=" * 50)
    print(f"📝 Test Data:")
    print(f"   Quantity: {test_data['qty_liters']} L")
    print(f"   Fat: {test_data['fat']}% (will convert to 4.3%)")
    print(f"   CLR: {test_data['clr']} (will convert to 29.5)")
    print(f"   Rate: ₹{test_data['rate_per_liter']}/100kg")
    print()
    
    try:
        # First, let's try to access the add milk entry page to get session cookies
        print("🌐 Accessing Add Milk Entry page...")
        session = requests.Session()
        response = session.get(f"{base_url}/milk/entry")
        
        if response.status_code == 200:
            print("✅ Successfully accessed add milk entry page")
        else:
            print(f"❌ Failed to access page: {response.status_code}")
            return
        
        # Now try to submit the form
        print("📤 Submitting milk entry...")
        response = session.post(f"{base_url}/milk/entry", data=test_data)
        
        if response.status_code == 302:
            print("✅ Milk entry submitted successfully (redirect)")
            print("🎯 Check the Milk Statement to verify the calculation")
        else:
            print(f"❌ Submission failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("📝 Make sure the Flask app is running at http://127.0.0.1:5000")

if __name__ == "__main__":
    test_add_milk_entry()
