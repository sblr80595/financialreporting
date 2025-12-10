"""
Schedule III Formatter for Companies Act, 2013
Formats financial statements as per Ind AS-compliant Schedule III requirements
"""

import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime
from backend.sap_connect.account_mapping_manager import AccountTypeMappingManager


class Schedule3BalanceSheet:
    """Format Balance Sheet as per Schedule III to Companies Act, 2013"""
    
    def __init__(self, trial_balance_df: pd.DataFrame, entity_name: str, 
                 as_at_date: str, entity_id: str = None):
        """
        Initialize Schedule III Balance Sheet formatter
        
        Args:
            trial_balance_df: Trial Balance DataFrame with columns [Account Code, Account Name, Debit, Credit, Balance]
            entity_name: Name of the company
            as_at_date: Balance Sheet date (YYYY-MM-DD)
            entity_id: Entity ID for custom mapping (optional)
        """
        self.tb_df = trial_balance_df
        self.entity_name = entity_name
        self.as_at_date = as_at_date
        self.entity_id = entity_id
        self.mapping_manager = AccountTypeMappingManager() if entity_id else None
        
    def _classify_account(self, account_code: str, account_name: str, balance: float, account_type: int = None) -> str:
        """Classify account into Schedule III categories"""
        
        # Use mapping manager if available
        if self.mapping_manager and self.entity_id:
            return self.mapping_manager.get_schedule3_category(
                self.entity_id, account_code, account_name, account_type or 0, balance
            )
        
        # Fallback to built-in logic
        account_code_str = str(account_code)
        account_name_upper = account_name.upper()
        
        # Use SAP B1 Account Type if available
        # Type 1 = Assets, Type 2 = Liabilities, Type 3 = Equity
        # Type 4 = Revenue, Type 5 = COGS, Type 6 = Expenses, Type 7 = Other Income, Type 8 = Tax
        
        if account_type == 1:  # Assets
            # Fixed Assets (11xxx-19xxx)
            if account_code_str.startswith('11') or account_code_str.startswith('12'):
                if 'GOODWILL' in account_name_upper:
                    return 'Goodwill'
                elif any(keyword in account_name_upper for keyword in ['TRADEMARK', 'SOFTWARE', 'LICENSE', 'PATENT', 'COPYRIGHT']):
                    return 'Other Intangible Assets'
                else:
                    return 'Property, Plant and Equipment'
            # Current Assets (13xxx-19xxx)
            elif account_code_str.startswith('13'):
                if any(keyword in account_name_upper for keyword in ['DEBTOR', 'RECEIVABLE']):
                    return 'Trade Receivables'
                else:
                    return 'Other Current Assets'
            elif account_code_str.startswith('14'):
                return 'Inventories'
            elif account_code_str.startswith('15'):
                if any(keyword in account_name_upper for keyword in ['CASH', 'BANK']):
                    return 'Cash and Cash Equivalents'
                else:
                    return 'Short-term Loans and Advances'
            elif account_code_str.startswith('16'):
                return 'Current Investments'
            elif account_code_str.startswith('17'):
                return 'Deferred Tax Assets (Net)'
            else:
                return 'Other Non-current Assets'
        
        elif account_type == 2:  # Liabilities
            # Non-current Liabilities (22xxx-24xxx)
            if account_code_str.startswith('22'):
                return 'Long-term Borrowings'
            elif account_code_str.startswith('23'):
                return 'Deferred Tax Liabilities (Net)'
            elif account_code_str.startswith('24'):
                return 'Other Non-current Liabilities'
            # Current Liabilities (21xxx, 25xxx-29xxx)
            elif account_code_str.startswith('21'):
                if any(keyword in account_name_upper for keyword in ['CREDITOR', 'PAYABLE']):
                    return 'Trade Payables'
                else:
                    return 'Other Current Liabilities'
            elif account_code_str.startswith('25'):
                return 'Short-term Borrowings'
            elif account_code_str.startswith('26'):
                return 'Short-term Provisions'
            elif account_code_str.startswith('27'):
                return 'Provisions - Current Tax'
            else:
                return 'Other Current Liabilities'
        
        elif account_type == 3:  # Equity
            if any(keyword in account_name_upper for keyword in ['SHARE CAPITAL', 'PAID UP CAPITAL']):
                return 'Equity Share Capital'
            else:
                return 'Reserves and Surplus'
        
        # Fallback to balance-based classification (old logic)
        elif balance > 0:  # Debit balance = Asset
            if any(keyword in account_name_upper for keyword in ['LAND', 'BUILDING', 'PLANT', 'MACHINERY', 'EQUIPMENT', 'FURNITURE', 'VEHICLE', 'COMPUTER']):
                return 'Property, Plant and Equipment'
            elif 'GOODWILL' in account_name_upper:
                return 'Goodwill'
            elif any(keyword in account_name_upper for keyword in ['SOFTWARE', 'LICENSE', 'PATENT', 'TRADEMARK', 'COPYRIGHT']):
                return 'Other Intangible Assets'
            elif any(keyword in account_name_upper for keyword in ['STOCK', 'INVENTORY', 'RAW MATERIAL', 'FINISHED GOODS', 'WIP']):
                return 'Inventories'
            elif any(keyword in account_name_upper for keyword in ['DEBTOR', 'RECEIVABLE']):
                return 'Trade Receivables'
            elif any(keyword in account_name_upper for keyword in ['CASH', 'BANK']):
                return 'Cash and Cash Equivalents'
            else:
                return 'Other Current Assets'
        else:  # Credit balance = Liability or Equity
            if any(keyword in account_name_upper for keyword in ['SHARE CAPITAL', 'EQUITY']):
                return 'Equity Share Capital'
            elif any(keyword in account_name_upper for keyword in ['RESERVE', 'SURPLUS', 'RETAINED EARNING']):
                return 'Reserves and Surplus'
            elif any(keyword in account_name_upper for keyword in ['CREDITOR', 'PAYABLE']):
                return 'Trade Payables'
            else:
                return 'Other Current Liabilities'
    
    def generate_balance_sheet(self) -> pd.DataFrame:
        """Generate Schedule III formatted Balance Sheet"""
        
        # Classify all accounts
        classified_data = []
        
        for _, row in self.tb_df.iterrows():
            category = self._classify_account(
                row.get('AccountCode', row.get('Code', '')),
                row.get('AccountName', row.get('Name', '')),
                row.get('Balance', 0),
                row.get('AccountType', None)
            )
            
            classified_data.append({
                'Category': category,
                'Account Code': row.get('AccountCode', row.get('Code', '')),
                'Account Name': row.get('AccountName', row.get('Name', '')),
                'Amount': abs(row.get('Balance', 0))
            })
        
        df = pd.DataFrame(classified_data)
        
        # Group by category
        summary = df.groupby('Category')['Amount'].sum().reset_index()
        summary.columns = ['Particulars', f'As at {self.as_at_date}']
        
        # Create Schedule III formatted Balance Sheet
        bs_data = []
        
        # I. EQUITY AND LIABILITIES
        bs_data.append({'Particulars': 'I. EQUITY AND LIABILITIES', f'As at {self.as_at_date}': '', 'Note': ''})
        bs_data.append({'Particulars': '', f'As at {self.as_at_date}': '', 'Note': ''})
        
        # (1) Equity
        bs_data.append({'Particulars': '(1) Equity', f'As at {self.as_at_date}': '', 'Note': ''})
        equity_items = ['Equity Share Capital', 'Reserves and Surplus']
        equity_total = 0
        for item in equity_items:
            amount = summary[summary['Particulars'] == item][f'As at {self.as_at_date}'].sum()
            if amount > 0:
                bs_data.append({'Particulars': f'     (a) {item}', f'As at {self.as_at_date}': amount, 'Note': ''})
                equity_total += amount
        bs_data.append({'Particulars': 'Total Equity', f'As at {self.as_at_date}': equity_total, 'Note': ''})
        bs_data.append({'Particulars': '', f'As at {self.as_at_date}': '', 'Note': ''})
        
        # (2) Non-current Liabilities
        bs_data.append({'Particulars': '(2) Non-current Liabilities', f'As at {self.as_at_date}': '', 'Note': ''})
        ncl_items = ['Long-term Borrowings', 'Deferred Tax Liabilities (Net)', 'Other Non-current Liabilities']
        ncl_total = 0
        for item in ncl_items:
            amount = summary[summary['Particulars'] == item][f'As at {self.as_at_date}'].sum()
            if amount > 0:
                bs_data.append({'Particulars': f'     (a) {item}', f'As at {self.as_at_date}': amount, 'Note': ''})
                ncl_total += amount
        bs_data.append({'Particulars': 'Total Non-current Liabilities', f'As at {self.as_at_date}': ncl_total, 'Note': ''})
        bs_data.append({'Particulars': '', f'As at {self.as_at_date}': '', 'Note': ''})
        
        # (3) Current Liabilities
        bs_data.append({'Particulars': '(3) Current Liabilities', f'As at {self.as_at_date}': '', 'Note': ''})
        cl_items = ['Short-term Borrowings', 'Trade Payables', 'Other Current Liabilities', 'Short-term Provisions', 'Provisions - Current Tax']
        cl_total = 0
        for item in cl_items:
            amount = summary[summary['Particulars'] == item][f'As at {self.as_at_date}'].sum()
            if amount > 0:
                bs_data.append({'Particulars': f'     (a) {item}', f'As at {self.as_at_date}': amount, 'Note': ''})
                cl_total += amount
        bs_data.append({'Particulars': 'Total Current Liabilities', f'As at {self.as_at_date}': cl_total, 'Note': ''})
        bs_data.append({'Particulars': '', f'As at {self.as_at_date}': '', 'Note': ''})
        
        total_equity_liabilities = equity_total + ncl_total + cl_total
        bs_data.append({'Particulars': 'TOTAL EQUITY AND LIABILITIES', f'As at {self.as_at_date}': total_equity_liabilities, 'Note': ''})
        bs_data.append({'Particulars': '', f'As at {self.as_at_date}': '', 'Note': ''})
        bs_data.append({'Particulars': '', f'As at {self.as_at_date}': '', 'Note': ''})
        
        # II. ASSETS
        bs_data.append({'Particulars': 'II. ASSETS', f'As at {self.as_at_date}': '', 'Note': ''})
        bs_data.append({'Particulars': '', f'As at {self.as_at_date}': '', 'Note': ''})
        
        # (1) Non-current Assets
        bs_data.append({'Particulars': '(1) Non-current Assets', f'As at {self.as_at_date}': '', 'Note': ''})
        nca_items = ['Property, Plant and Equipment', 'Goodwill', 'Other Intangible Assets', 
                     'Non-current Investments', 'Long-term Loans and Advances', 'Deferred Tax Assets (Net)', 'Other Non-current Assets']
        nca_total = 0
        for item in nca_items:
            amount = summary[summary['Particulars'] == item][f'As at {self.as_at_date}'].sum()
            if amount > 0:
                bs_data.append({'Particulars': f'     (a) {item}', f'As at {self.as_at_date}': amount, 'Note': ''})
                nca_total += amount
        bs_data.append({'Particulars': 'Total Non-current Assets', f'As at {self.as_at_date}': nca_total, 'Note': ''})
        bs_data.append({'Particulars': '', f'As at {self.as_at_date}': '', 'Note': ''})
        
        # (2) Current Assets
        bs_data.append({'Particulars': '(2) Current Assets', f'As at {self.as_at_date}': '', 'Note': ''})
        ca_items = ['Inventories', 'Current Investments', 'Trade Receivables', 'Cash and Cash Equivalents', 
                    'Short-term Loans and Advances', 'Other Current Assets']
        ca_total = 0
        for item in ca_items:
            amount = summary[summary['Particulars'] == item][f'As at {self.as_at_date}'].sum()
            if amount > 0:
                bs_data.append({'Particulars': f'     (a) {item}', f'As at {self.as_at_date}': amount, 'Note': ''})
                ca_total += amount
        bs_data.append({'Particulars': 'Total Current Assets', f'As at {self.as_at_date}': ca_total, 'Note': ''})
        bs_data.append({'Particulars': '', f'As at {self.as_at_date}': '', 'Note': ''})
        
        total_assets = nca_total + ca_total
        bs_data.append({'Particulars': 'TOTAL ASSETS', f'As at {self.as_at_date}': total_assets, 'Note': ''})
        
        return pd.DataFrame(bs_data)


class Schedule3ProfitLoss:
    """Format Profit & Loss Statement as per Schedule III to Companies Act, 2013"""
    
    def __init__(self, pl_df: pd.DataFrame, entity_name: str, period_start: str, 
                 period_end: str, entity_id: str = None):
        """
        Initialize Schedule III P&L formatter
        
        Args:
            pl_df: Profit & Loss DataFrame
            entity_name: Name of the company
            period_start: Period start date (YYYY-MM-DD)
            period_end: Period end date (YYYY-MM-DD)
            entity_id: Entity ID for custom mapping (optional)
        """
        self.pl_df = pl_df
        self.entity_name = entity_name
        self.period_start = period_start
        self.period_end = period_end
        self.entity_id = entity_id
        self.mapping_manager = AccountTypeMappingManager() if entity_id else None
        
    def _classify_pl_account(self, account_name: str, amount: float) -> Tuple[str, str]:
        """
        Classify P&L account into Schedule III categories
        
        Returns:
            Tuple of (category, type) where type is 'Income' or 'Expense'
        """
        account_name_upper = account_name.upper()
        
        # Income Classification
        if any(keyword in account_name_upper for keyword in ['SALES', 'REVENUE', 'TURNOVER', 'SERVICE INCOME']):
            return 'Revenue from Operations', 'Income'
        elif any(keyword in account_name_upper for keyword in ['INTEREST INCOME', 'DIVIDEND INCOME', 'OTHER INCOME']):
            return 'Other Income', 'Income'
        
        # Expense Classification
        elif any(keyword in account_name_upper for keyword in ['RAW MATERIAL', 'MATERIAL CONSUMED', 'CONSUMPTION']):
            return 'Cost of Materials Consumed', 'Expense'
        elif any(keyword in account_name_upper for keyword in ['PURCHASE', 'STOCK IN TRADE']):
            return 'Purchases of Stock-in-Trade', 'Expense'
        elif any(keyword in account_name_upper for keyword in ['SALARY', 'WAGES', 'EMPLOYEE', 'STAFF', 'PROVIDENT FUND', 'GRATUITY', 'BONUS']):
            return 'Employee Benefits Expense', 'Expense'
        elif any(keyword in account_name_upper for keyword in ['INTEREST', 'FINANCE COST', 'BANK CHARGES']) and 'INCOME' not in account_name_upper:
            return 'Finance Costs', 'Expense'
        elif any(keyword in account_name_upper for keyword in ['DEPRECIATION', 'AMORTIZATION']):
            return 'Depreciation and Amortization', 'Expense'
        else:
            return 'Other Expenses', 'Expense'
    
    def generate_profit_loss(self) -> pd.DataFrame:
        """Generate Schedule III formatted Profit & Loss Statement"""
        
        # Classify all accounts
        classified_data = []
        
        for _, row in self.pl_df.iterrows():
            category, type_ = self._classify_pl_account(
                row.get('Account Name', row.get('Name', '')),
                row.get('Amount', row.get('Balance', 0))
            )
            
            classified_data.append({
                'Category': category,
                'Type': type_,
                'Account Name': row.get('Account Name', row.get('Name', '')),
                'Amount': abs(row.get('Amount', row.get('Balance', 0)))
            })
        
        df = pd.DataFrame(classified_data)
        
        # Group by category
        income_df = df[df['Type'] == 'Income'].groupby('Category')['Amount'].sum().reset_index()
        expense_df = df[df['Type'] == 'Expense'].groupby('Category')['Amount'].sum().reset_index()
        
        # Create Schedule III formatted P&L
        pl_data = []
        period_label = f'For the period ended {self.period_end}'
        
        # I. INCOME
        pl_data.append({'Particulars': 'I. INCOME', period_label: '', 'Note': ''})
        pl_data.append({'Particulars': '', period_label: '', 'Note': ''})
        
        # Revenue from Operations
        revenue = income_df[income_df['Category'] == 'Revenue from Operations']['Amount'].sum()
        pl_data.append({'Particulars': 'Revenue from Operations', period_label: revenue, 'Note': ''})
        
        # Other Income
        other_income = income_df[income_df['Category'] == 'Other Income']['Amount'].sum()
        pl_data.append({'Particulars': 'Other Income', period_label: other_income, 'Note': ''})
        
        total_income = revenue + other_income
        pl_data.append({'Particulars': 'Total Income (I)', period_label: total_income, 'Note': ''})
        pl_data.append({'Particulars': '', period_label: '', 'Note': ''})
        
        # II. EXPENSES
        pl_data.append({'Particulars': 'II. EXPENSES', period_label: '', 'Note': ''})
        pl_data.append({'Particulars': '', period_label: '', 'Note': ''})
        
        expense_categories = [
            'Cost of Materials Consumed',
            'Purchases of Stock-in-Trade',
            'Employee Benefits Expense',
            'Finance Costs',
            'Depreciation and Amortization',
            'Other Expenses'
        ]
        
        total_expenses = 0
        for category in expense_categories:
            amount = expense_df[expense_df['Category'] == category]['Amount'].sum()
            if amount > 0:
                pl_data.append({'Particulars': category, period_label: amount, 'Note': ''})
                total_expenses += amount
        
        pl_data.append({'Particulars': 'Total Expenses (II)', period_label: total_expenses, 'Note': ''})
        pl_data.append({'Particulars': '', period_label: '', 'Note': ''})
        
        # III. PROFIT BEFORE TAX
        profit_before_tax = total_income - total_expenses
        pl_data.append({'Particulars': 'III. Profit/(Loss) before Tax (I - II)', period_label: profit_before_tax, 'Note': ''})
        pl_data.append({'Particulars': '', period_label: '', 'Note': ''})
        
        # IV. TAX EXPENSE (Placeholder - to be calculated separately)
        pl_data.append({'Particulars': 'IV. Tax Expense', period_label: '', 'Note': ''})
        pl_data.append({'Particulars': '     (1) Current Tax', period_label: 0, 'Note': ''})
        pl_data.append({'Particulars': '     (2) Deferred Tax', period_label: 0, 'Note': ''})
        total_tax = 0
        pl_data.append({'Particulars': 'Total Tax Expense (IV)', period_label: total_tax, 'Note': ''})
        pl_data.append({'Particulars': '', period_label: '', 'Note': ''})
        
        # V. PROFIT AFTER TAX
        profit_after_tax = profit_before_tax - total_tax
        pl_data.append({'Particulars': 'V. Profit/(Loss) for the period (III - IV)', period_label: profit_after_tax, 'Note': ''})
        
        return pd.DataFrame(pl_data)
