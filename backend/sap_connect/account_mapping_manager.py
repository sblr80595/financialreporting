"""
Account Type Mapping Manager
Manages and auto-detects account type mappings for different SAP B1 entities
"""

import json
import os
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime


class AccountTypeMappingManager:
    """Manages account type mappings for Schedule III classification"""
    
    def __init__(self, config_path: str = 'config/sap_connect/account_type_mappings.json'):
        """
        Initialize the mapping manager
        
        Args:
            config_path: Path to the account type mappings configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            # Return default config if file doesn't exist
            return {
                "account_type_mappings": {"default": {}},
                "entity_mappings": {},
                "metadata": {}
            }
    
    def _save_config(self):
        """Save configuration to JSON file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_entity_mapping_profile(self, entity_id: str) -> str:
        """Get the mapping profile name for an entity"""
        entity_config = self.config.get('entity_mappings', {}).get(entity_id, {})
        return entity_config.get('mapping_profile', 'default')
    
    def get_schedule3_category(self, entity_id: str, account_code: str, 
                               account_name: str, account_type: int, 
                               balance: float) -> str:
        """
        Get Schedule III category for an account
        
        Args:
            entity_id: Entity ID
            account_code: Account code
            account_name: Account name
            account_type: SAP B1 account type (1-8)
            balance: Account balance
            
        Returns:
            Schedule III category name
        """
        # Get entity-specific custom rules first
        entity_config = self.config.get('entity_mappings', {}).get(entity_id, {})
        custom_rules = entity_config.get('custom_rules', {})
        
        # Check account-specific override
        account_specific = custom_rules.get('account_specific', {})
        if str(account_code) in account_specific:
            return account_specific[str(account_code)]
        
        # Check name-based overrides
        name_based = custom_rules.get('name_based_overrides', {})
        account_name_upper = account_name.upper()
        for keyword, category in name_based.items():
            if keyword in account_name_upper:
                return category
        
        # Get mapping profile
        profile_name = self.get_entity_mapping_profile(entity_id)
        profile = self.config.get('account_type_mappings', {}).get(profile_name, {})
        mappings = profile.get('mappings', {})
        
        # Get account type mapping
        type_mapping = mappings.get(str(account_type), {})
        schedule3_mapping = type_mapping.get('schedule3_mapping', {})
        
        # Find matching code range
        account_code_int = int(account_code) if account_code.isdigit() else 0
        
        for code_range, category in schedule3_mapping.items():
            if '-' in code_range:
                start, end = code_range.split('-')
                start_int = int(start)
                end_int = int(end)
                if start_int <= account_code_int <= end_int:
                    return category
        
        # Fallback to default classification
        return self._default_classification(account_code, account_name, account_type, balance)
    
    def _default_classification(self, account_code: str, account_name: str, 
                                account_type: int, balance: float) -> str:
        """Default classification logic when no mapping found"""
        account_name_upper = account_name.upper()
        
        if account_type == 1:  # Assets
            if 'GOODWILL' in account_name_upper:
                return 'Goodwill'
            elif any(kw in account_name_upper for kw in ['TRADEMARK', 'SOFTWARE', 'LICENSE', 'PATENT']):
                return 'Other Intangible Assets'
            elif any(kw in account_name_upper for kw in ['FURNITURE', 'EQUIPMENT', 'COMPUTER', 'VEHICLE']):
                return 'Property, Plant and Equipment'
            elif any(kw in account_name_upper for kw in ['DEBTOR', 'RECEIVABLE']):
                return 'Trade Receivables'
            elif any(kw in account_name_upper for kw in ['STOCK', 'INVENTORY']):
                return 'Inventories'
            elif any(kw in account_name_upper for kw in ['CASH', 'BANK']):
                return 'Cash and Cash Equivalents'
            else:
                return 'Other Current Assets'
        
        elif account_type == 2:  # Liabilities
            if any(kw in account_name_upper for kw in ['CREDITOR', 'PAYABLE']):
                return 'Trade Payables'
            elif 'BORROWING' in account_name_upper or 'LOAN' in account_name_upper:
                if 'LONG' in account_name_upper or 'TERM' in account_name_upper:
                    return 'Long-term Borrowings'
                else:
                    return 'Short-term Borrowings'
            else:
                return 'Other Current Liabilities'
        
        elif account_type == 3:  # Equity
            if 'CAPITAL' in account_name_upper:
                return 'Equity Share Capital'
            else:
                return 'Reserves and Surplus'
        
        else:
            return 'Other Current Assets'
    
    def auto_detect_and_save(self, entity_id: str, trial_balance_df: pd.DataFrame):
        """
        Auto-detect account type structure for an entity and save to config
        
        Args:
            entity_id: Entity ID
            trial_balance_df: Trial balance DataFrame with AccountCode, AccountName, AccountType, Balance
        """
        print(f"\n🔍 Auto-detecting account type structure for {entity_id}...")
        
        # Analyze account types
        type_analysis = {}
        
        for account_type in trial_balance_df['AccountType'].unique():
            type_df = trial_balance_df[trial_balance_df['AccountType'] == account_type]
            
            # Get code ranges
            codes = type_df['AccountCode'].astype(str).str.extract(r'(\d+)')[0].astype(float).dropna()
            if len(codes) > 0:
                min_code = int(codes.min())
                max_code = int(codes.max())
                
                # Sample account names
                sample_names = type_df['AccountName'].head(5).tolist()
                
                type_analysis[int(account_type)] = {
                    'count': len(type_df),
                    'code_range': f"{min_code}-{max_code}",
                    'sample_names': sample_names
                }
        
        # Display analysis
        print("\n📊 Account Type Analysis:")
        print("=" * 80)
        for acc_type, info in sorted(type_analysis.items()):
            print(f"\nType {acc_type}:")
            print(f"  Count: {info['count']} accounts")
            print(f"  Code Range: {info['code_range']}")
            print(f"  Sample Accounts:")
            for name in info['sample_names']:
                print(f"    - {name}")
        
        # Ask if user wants to save
        print("\n" + "=" * 80)
        print(f"💾 Updating configuration for {entity_id}...")
        
        # Update entity mapping
        if entity_id not in self.config.get('entity_mappings', {}):
            self.config['entity_mappings'][entity_id] = {
                'mapping_profile': 'india_standard',
                'verified_date': datetime.now().strftime('%Y-%m-%d'),
                'verified_by': 'auto_detect',
                'type_analysis': type_analysis
            }
        else:
            self.config['entity_mappings'][entity_id]['verified_date'] = datetime.now().strftime('%Y-%m-%d')
            self.config['entity_mappings'][entity_id]['verified_by'] = 'auto_detect'
            self.config['entity_mappings'][entity_id]['type_analysis'] = type_analysis
        
        # Save config
        self._save_config()
        print(f"✅ Configuration saved to {self.config_path}")
        
        return type_analysis
    
    def get_entity_info(self, entity_id: str) -> Dict:
        """Get mapping information for an entity"""
        return self.config.get('entity_mappings', {}).get(entity_id, {})
    
    def list_all_entities(self) -> list:
        """List all entities with mappings"""
        return list(self.config.get('entity_mappings', {}).keys())
    
    def verify_entity_mapping(self, entity_id: str, trial_balance_df: pd.DataFrame) -> Dict:
        """
        Verify if the current mapping works well for an entity
        
        Returns:
            Dictionary with verification results and recommendations
        """
        results = {
            'total_accounts': len(trial_balance_df),
            'classified': 0,
            'unclassified': 0,
            'categories': {},
            'recommendations': []
        }
        
        for _, row in trial_balance_df.iterrows():
            category = self.get_schedule3_category(
                entity_id,
                row.get('AccountCode', ''),
                row.get('AccountName', ''),
                row.get('AccountType', 0),
                row.get('Balance', 0)
            )
            
            if category:
                results['classified'] += 1
                results['categories'][category] = results['categories'].get(category, 0) + 1
            else:
                results['unclassified'] += 1
        
        # Generate recommendations
        if results['unclassified'] > 0:
            results['recommendations'].append(
                f"⚠️  {results['unclassified']} accounts could not be classified. "
                "Consider adding custom rules."
            )
        
        classification_rate = (results['classified'] / results['total_accounts']) * 100
        if classification_rate < 90:
            results['recommendations'].append(
                f"⚠️  Classification rate is {classification_rate:.1f}%. "
                "Recommended to review and add entity-specific rules."
            )
        else:
            results['recommendations'].append(
                f"✅ Classification rate is {classification_rate:.1f}%. Good coverage!"
            )
        
        return results
