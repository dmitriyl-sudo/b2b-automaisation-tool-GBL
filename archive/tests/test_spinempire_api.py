#!/usr/bin/env python3
"""
SpinEmpire API Test Script
Tests authentication and payment systems endpoint
"""

import requests
import json
import sys
from datetime import datetime

class SpinEmpireAPI:
    def __init__(self):
        self.base_url = "https://spinempire.com/api/v1/en"
        self.session = requests.Session()
        self.token = None
        
        # Set headers similar to the browser request
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
            'Referer': 'https://spinempire.com/en',
            'Origin': 'https://spinempire.com'
        })

    def login(self, login="4depaffilfieurmobi1", password="123123123"):
        """Authenticate with SpinEmpire API"""
        print(f"🔐 Attempting login with user: {login}")
        
        login_url = f"{self.base_url}/account/login"
        login_data = {
            "login": login,
            "password": password,
            "google_token": "",
            "facebook_token": ""
        }
        
        try:
            response = self.session.post(login_url, json=login_data)
            print(f"📡 Login request status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ Login successful!")
                
                # Extract token from cookies or response
                cookies = response.cookies
                if '__token' in cookies:
                    self.token = cookies['__token']
                    print(f"🎟️  Token extracted from cookies")
                
                # Print response data (truncated)
                print(f"📄 Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
                
                return True
            else:
                print(f"❌ Login failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"💥 Login error: {str(e)}")
            return False

    def get_payment_systems(self):
        """Get payment systems with the specified fields"""
        print(f"\n💳 Fetching payment systems...")
        
        # URL with exact fields from the request
        url = f"{self.base_url}/model/paysystem/deposit"
        params = {
            'fields': 'images,name,title,display_type,show_amount,parent_paysystem,run_iframe,version',
            'limit': 100
        }
        
        try:
            response = self.session.get(url, params=params)
            print(f"📡 Payment systems request status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Payment systems fetched successfully!")
                
                # Analyze the response
                if isinstance(data, dict):
                    print(f"📊 Response structure:")
                    for key, value in data.items():
                        if isinstance(value, list):
                            print(f"  - {key}: list with {len(value)} items")
                        else:
                            print(f"  - {key}: {type(value).__name__}")
                    
                    # If there's a data field with payment methods
                    if 'data' in data and isinstance(data['data'], list):
                        methods = data['data']
                        print(f"\n🎯 Found {len(methods)} payment methods:")
                        
                        for i, method in enumerate(methods[:5]):  # Show first 5
                            title = method.get('title', 'N/A')
                            name = method.get('name', 'N/A')
                            display_type = method.get('display_type', 'N/A')
                            print(f"  {i+1}. {title} ({name}) - {display_type}")
                        
                        if len(methods) > 5:
                            print(f"  ... and {len(methods) - 5} more")
                
                return data
            else:
                print(f"❌ Failed to fetch payment systems: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"💥 Payment systems error: {str(e)}")
            return None

    def save_response(self, data, filename):
        """Save response data to JSON file"""
        if data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"{filename}_{timestamp}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Response saved to: {filepath}")
            return filepath
        return None

def main():
    print("🚀 SpinEmpire API Test Script")
    print("=" * 50)
    
    api = SpinEmpireAPI()
    
    # Step 1: Login
    if api.login():
        print(f"🔗 Session cookies: {len(api.session.cookies)} cookies set")
        
        # Step 2: Get payment systems
        payment_data = api.get_payment_systems()
        
        if payment_data:
            # Save the response
            saved_file = api.save_response(payment_data, "spinempire_payment_systems")
            print(f"\n✨ Test completed successfully!")
            if saved_file:
                print(f"📁 Data saved to: {saved_file}")
        else:
            print(f"\n❌ Failed to fetch payment systems")
            sys.exit(1)
    else:
        print(f"\n❌ Authentication failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
