"""
Period Discovery Service
Automatically discovers available periods from trial balance files across entities
"""
import re
from pathlib import Path
from typing import Dict, List, Set
import pandas as pd
from datetime import datetime


class PeriodDiscoveryService:
    """Service to discover periods from trial balance files"""
    
    # Pattern to match period columns like "Mar'25", "(Unaudited) Mar'25", "Total Mar'25", etc.
    PERIOD_PATTERN = re.compile(r"([A-Z][a-z]{2})'(\d{2})")
    
    # Month name to number mapping
    MONTH_MAP = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    @classmethod
    def discover_periods_for_entity(cls, entity: str, base_path: Path = None) -> Dict[str, str]:
        """
        Discover available periods for a specific entity by scanning trial balance files.
        
        Args:
            entity: Entity code (e.g., 'cpm', 'analisa_resource')
            base_path: Base directory path (defaults to project root)
            
        Returns:
            Dict mapping period keys to column names
            e.g., {"mar_2025": "(Unaudited) Mar'25", "jun_2025": "Total Jun'25"}
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent / "data"
        
        entity_path = base_path / entity / "input"
        periods = {}
        
        print(f"🔍 Discovering periods for entity: {entity}")
        print(f"   Looking in: {entity_path}")
        
        # Check unadjusted trial balance folder
        tb_folders = [
            entity_path / "unadjusted-trialbalance",
            entity_path / "pre-adjusted-trialbalance",
        ]
        
        for tb_folder in tb_folders:
            if not tb_folder.exists():
                print(f"   ⚠️  Folder does not exist: {tb_folder}")
                continue
            
            print(f"   ✓ Scanning folder: {tb_folder.name}")
                
            # Scan Excel and CSV files
            files = list(tb_folder.glob("*.xlsx")) + list(tb_folder.glob("*.csv"))
            print(f"   Found {len(files)} file(s): {[f.name for f in files]}")
            
            for file_path in files:
                try:
                    print(f"      Reading: {file_path.name}")
                    # Read first row to get column names
                    if file_path.suffix == '.xlsx':
                        df = pd.read_excel(file_path, nrows=0)
                    else:
                        df = pd.read_csv(file_path, nrows=0)
                    
                    print(f"      Columns: {list(df.columns)}")
                    
                    # Extract period columns
                    for col in df.columns:
                        col_str = str(col)
                        match = cls.PERIOD_PATTERN.search(col_str)
                        if match:
                            month_abbr = match.group(1)
                            year_short = match.group(2)
                            
                            # Convert to full year
                            year_full = f"20{year_short}"
                            
                            # Create period key (e.g., "mar_2025")
                            month_lower = month_abbr.lower()
                            period_key = f"{month_lower}_{year_full}"
                            
                            # Store the actual column name
                            periods[period_key] = col_str
                            print(f"      ✓ Found period: {period_key} -> {col_str}")
                            
                except Exception as e:
                    print(f"      ❌ Error reading {file_path.name}: {e}")
                    continue
        
        print(f"   📊 Total periods discovered: {len(periods)}")
        return periods
    
    @classmethod
    def discover_all_periods(cls, base_path: Path = None) -> Dict[str, Dict[str, str]]:
        """
        Discover available periods for all entities.
        
        Returns:
            Dict mapping entity codes to their available periods
            e.g., {
                "cpm": {"mar_2025": "(Unaudited) Mar'25"},
                "analisa_resource": {"jun_2025": "Total Jun'25"}
            }
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent / "data"
        
        all_periods = {}
        
        # Scan all entity folders
        for entity_path in base_path.iterdir():
            if entity_path.is_dir() and not entity_path.name.startswith('.'):
                entity = entity_path.name
                periods = cls.discover_periods_for_entity(entity, base_path)
                if periods:
                    all_periods[entity] = periods
        
        return all_periods
    
    @classmethod
    def get_period_display_name(cls, period_key: str) -> str:
        """
        Convert period key to display name in MMM-YYYY format.
        
        Args:
            period_key: Period key like "mar_2025"
            
        Returns:
            Display name like "Mar-2025"
        """
        parts = period_key.split('_')
        if len(parts) != 2:
            return period_key
        
        month_abbr = parts[0].capitalize()
        year = parts[1]
        
        return f"{month_abbr}-{year}"
    
    @classmethod
    def sort_periods(cls, periods: Dict[str, str]) -> Dict[str, str]:
        """
        Sort periods chronologically.
        
        Args:
            periods: Dict of period_key to column_name
            
        Returns:
            Sorted dict of periods
        """
        def period_to_date(period_key: str):
            """Convert period key to datetime for sorting"""
            try:
                parts = period_key.split('_')
                month_abbr = parts[0].capitalize()
                year = parts[1]
                month_num = cls.MONTH_MAP.get(month_abbr, '01')
                return datetime.strptime(f"{year}-{month_num}", "%Y-%m")
            except:
                return datetime.min
        
        sorted_keys = sorted(periods.keys(), key=period_to_date, reverse=True)
        return {k: periods[k] for k in sorted_keys}


# Singleton instance
period_discovery_service = PeriodDiscoveryService()
