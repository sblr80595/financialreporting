#!/usr/bin/env python3
"""
Quick SAP Connectivity Diagnostic Tool
======================================
Check specific entity connectivity and diagnose issues
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.sap_connect.connectivity_manager import ConnectivityManager

def diagnose_cpm():
    """Diagnose CPM connectivity"""
    print("=" * 70)
    print("CPM SAP CONNECTIVITY DIAGNOSTIC")
    print("=" * 70)
    
    conn_mgr = ConnectivityManager()
    
    # Get CPM entity
    entity = conn_mgr.get_entity_by_id("CPM_CHEMOPHARM")
    
    if not entity:
        print("\n❌ ERROR: CPM_CHEMOPHARM entity not found in configuration")
        return
    
    print(f"\n✓ Entity Configuration Found")
    print(f"  ID: {entity['id']}")
    print(f"  Name: {entity['name']}")
    print(f"  Type: {entity['connection_type']}")
    print(f"  Server: {entity['sql_server']}")
    print(f"  Database: {entity['database']}")
    print(f"  Username: {entity['username']}")
    print(f"  Password: {'*' * len(entity['password'])}")
    
    # Check ODBC drivers
    print(f"\n✓ Checking ODBC Drivers...")
    drivers = conn_mgr.get_available_odbc_drivers()
    print(f"  Available drivers: {len(drivers)}")
    for driver in drivers:
        print(f"    - {driver}")
    
    best_driver = conn_mgr._get_best_sql_driver()
    if best_driver:
        print(f"\n  ✓ Selected driver: {best_driver}")
    else:
        print(f"\n  ❌ No suitable SQL Server driver found!")
        return
    
    # Test connection
    print(f"\n✓ Testing SQL Server Connection...")
    print(f"  Server: {entity['sql_server']}")
    print(f"  Database: {entity['database']}")
    print(f"  Attempting connection...\n")
    
    success, message, response_time = conn_mgr.test_sql_connection(entity)
    
    if success:
        print(f"  ✅ CONNECTION SUCCESSFUL!")
        print(f"  Response time: {response_time:.2f}s")
        print(f"  Message: {message}")
    else:
        print(f"  ❌ CONNECTION FAILED")
        print(f"  Error: {message}")
        
        print(f"\n📋 Troubleshooting Steps:")
        print(f"  1. Verify you are on the same network/VPN as {entity['sql_server']}")
        print(f"  2. Check if SQL Server is running and accessible")
        print(f"  3. Verify firewall allows connections to port 1433")
        print(f"  4. Test network connectivity: ping {entity['sql_server']}")
        print(f"  5. Verify credentials are correct")
        print(f"  6. Check if database '{entity['database']}' exists")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    diagnose_cpm()
