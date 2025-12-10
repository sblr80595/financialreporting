"""
SAP B1 API Client
=================
Purpose: Unified API client for all SAP B1 Service Layer interactions
Author: SAP Connection Module
Date: November 2025
"""

import requests
import urllib3
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SAPClient:
    """
    Unified SAP B1 Service Layer API client.
    Handles authentication, requests, pagination, and error handling.
    """
    
    def __init__(self, service_layer_url: str, username: str, password: str, 
                 company_db: str, timeout: int = 120, max_retries: int = 3):
        """
        Initialize SAP API client.
        
        Args:
            service_layer_url: SAP Service Layer base URL
            username: SAP username
            password: SAP password
            company_db: Company database name
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.service_layer_url = service_layer_url
        self.username = username
        self.password = password
        self.company_db = company_db
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
        self.session_id = None
        
    def login(self) -> bool:
        """
        Login to SAP B1 Service Layer.
        
        Returns:
            True if login successful, False otherwise
        """
        print("\n[LOGIN] Authenticating to SAP B1 Service Layer...")
        self.session = requests.Session()
        login_payload = {
            "CompanyDB": self.company_db,
            "UserName": self.username,
            "Password": self.password
        }
        
        try:
            response = self.session.post(
                f"{self.service_layer_url}/Login",
                json=login_payload,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                self.session_id = response.json().get("SessionId")
                print(f"✓ Login successful! Session ID: {self.session_id}")
                return True
            else:
                print(f"✗ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"✗ Login error: {str(e)}")
            return False
    
    def logout(self):
        """Logout from SAP B1 Service Layer."""
        if self.session and self.session_id:
            try:
                headers = {"Cookie": f"B1SESSION={self.session_id}"}
                self.session.post(
                    f"{self.service_layer_url}/Logout",
                    headers=headers,
                    verify=False,
                    timeout=10
                )
                print("\n✓ Logged out successfully")
            except:
                pass
    
    def fetch_data(self, endpoint: str, filter_query: Optional[str] = None, 
                   select_fields: Optional[str] = None, 
                   top: int = 1000, verbose: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch data from any SAP endpoint with pagination support.
        
        Args:
            endpoint: API endpoint (e.g., 'JournalEntries')
            filter_query: OData filter query
            select_fields: Comma-separated fields to select
            top: Number of records per page
            verbose: Print progress messages
            
        Returns:
            List of records
        """
        url = f"{self.service_layer_url}/{endpoint}"
        params = {"$top": top}
        
        if filter_query:
            params["$filter"] = filter_query
        if select_fields:
            params["$select"] = select_fields
        
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"B1SESSION={self.session_id}"
        }
        
        all_results = []
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    headers=headers,
                    params=params,
                    verify=False,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("value", [])
                    all_results.extend(results)
                    
                    if verbose:
                        print(f"    Fetched {len(results)} records (total: {len(all_results)})")
                    
                    # Handle pagination
                    next_link = data.get("@odata.nextLink") or data.get("odata.nextLink")
                    page_count = 1
                    
                    while next_link:
                        response = self.session.get(
                            next_link,
                            headers=headers,
                            verify=False,
                            timeout=self.timeout
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            results = data.get("value", [])
                            all_results.extend(results)
                            page_count += 1
                            
                            if verbose:
                                print(f"    Page {page_count}: Fetched {len(results)} records (total: {len(all_results)})")
                            
                            next_link = data.get("@odata.nextLink") or data.get("odata.nextLink")
                        else:
                            if verbose:
                                print(f"    Pagination stopped at page {page_count}: Status {response.status_code}")
                            break
                    
                    return all_results
                    
                else:
                    if verbose:
                        print(f"  Attempt {attempt + 1}/{self.max_retries} failed: {response.status_code}")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(3)
                        
            except Exception as e:
                if verbose:
                    print(f"  Attempt {attempt + 1}/{self.max_retries} error: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(3)
        
        return []
    
    def build_date_filter(self, date_field: str, start_date: str, 
                         end_date: Optional[str] = None) -> str:
        """
        Build OData date filter.
        
        Args:
            date_field: Field name (e.g., 'TaxDate')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), optional
            
        Returns:
            OData filter string
        """
        if end_date:
            return f"{date_field} ge '{start_date}' and {date_field} le '{end_date}'"
        else:
            return f"{date_field} ge '{start_date}'"
    
    def __enter__(self):
        """Context manager entry."""
        self.login()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logout()
