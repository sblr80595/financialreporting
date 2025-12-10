"""
SAP Connect - Main Entry Point
================================
This script uses the modular sap_connect package
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.sap_connect.config_manager import Config
from src.sap_connect.connectivity_manager import ConnectivityManager
from src.sap_connect.data_extractor import DataExtractor
from src.sap_connect.sap_client import SAPClient

def main():
    """Main execution function"""
    print("="*60)
    print("SAP CONNECT - Data Extraction Tool")
    print("="*60)
    
    # Load configuration
    config = Config()
    print("\n✓ Configuration loaded from config/sap_connect/config.json")
    
    # Initialize connectivity manager
    conn_mgr = ConnectivityManager()
    print(f"✓ Loaded {len(conn_mgr.get_all_entities())} entities")
    
    # You can add your data extraction logic here
    print("\n✓ SAP Connect module is ready to use!")
    print("="*60)

if __name__ == "__main__":
    main()
