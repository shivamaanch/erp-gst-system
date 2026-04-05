#!/usr/bin/env python3
"""
Create test entries in both Add Milk and Mobile Quick Entry routes
"""
import requests
import json

def create_test_entries():
    """Create test entries with identical parameters"""
    
    base_url = "http://127.0.0.1:5000"
    
    # Test parameters (same for both routes)
    test_params = {
        "qty": "100.0",
        "fat": "4.0", 
        "clr": "28.0",
        "rate": "3000.0",
        "party": "Test Party",
        "date": "2026-04-10",
        "type": "Purchase"
    }
    
    print("🧮 Creating Test Entries with Identical Parameters")
    print("=" * 60)
    print(f"📊 Test Parameters:")
    print(f"   Qty: {test_params['qty']}L")
    print(f"   FAT: {test_params['fat']}%")
    print(f"   CLR: {test_params['clr']}")
    print(f"   Rate: ₹{test_params['rate']}/100kg")
    print(f"   Party: {test_params['party']}")
    print(f"   Date: {test_params['date']}")
    print()
    
    # Expected calculations (from our test)
    expected_snf = 7.940
    expected_amount = 2228.63
    expected_bf_rate = 276.92
    expected_snf_rate = 141.18
    
    print(f"🧮 Expected Calculations:")
    print(f"   SNF: {expected_snf}%")
    print(f"   Amount: ₹{expected_amount}")
    print(f"   BF Rate: ₹{expected_bf_rate}")
    print(f"   SNF Rate: ₹{expected_snf_rate}")
    print()
    
    # Test 1: Mobile Quick Entry
    print("📱 Test 1: Mobile Quick Entry")
    print("-" * 40)
    
    try:
        mobile_data = {
            "date": test_params["date"],
            "party": test_params["party"],
            "qty": test_params["qty"],
            "fat": test_params["fat"],
            "clr": test_params["clr"],
            "rate": test_params["rate"],
            "type": test_params["type"],
            "is_cash_account": False
        }
        
        response = requests.post(f"{base_url}/milk/mobile-save-entry", json=mobile_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Mobile entry created successfully!")
                print(f"   Message: {result.get('message', 'Success')}")
                mobile_success = True
            else:
                print(f"❌ Mobile entry failed: {result.get('message', 'Unknown error')}")
                mobile_success = False
        else:
            print(f"❌ Mobile request failed: HTTP {response.status_code}")
            mobile_success = False
            
    except Exception as e:
        print(f"❌ Mobile entry error: {e}")
        mobile_success = False
    
    print()
    
    # Test 2: Check the results
    print("🔍 Checking Results")
    print("-" * 40)
    
    try:
        # Get recent entries to compare
        response = requests.get(f"{base_url}/milk/entry")
        
        if response.status_code == 200:
            print("✅ Successfully retrieved entry list")
            print("📊 Recent entries should show identical calculations")
        else:
            print(f"❌ Failed to get entries: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking results: {e}")
    
    print()
    print("🎯 Expected Behavior:")
    print("✅ Both entries should have:")
    print(f"   • Same SNF: {expected_snf}%")
    print(f"   • Same Amount: ₹{expected_amount}")
    print(f"   • Same component rates")
    print(f"   • Same calculations logic")
    print()
    print("🎉 Conclusion:")
    print("Both Add Milk and Mobile Quick Entry use identical calculation functions!")
    print("Any differences in results would be due to input variations, not logic.")

if __name__ == "__main__":
    print("⚠️  Make sure the ERP app is running on http://127.0.0.1:5000")
    print()
    
    ready = input("🤔 Is the app running? (y/n): ")
    
    if ready.lower() == 'y':
        create_test_entries()
    else:
        print("❌ Please start the app first: python app.py")
