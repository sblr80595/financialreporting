"""
Financial Statements Generator
===============================
Purpose: Generate Trial Balance, Balance Sheet, P&L, and Cash Flow statements
Author: SAP Connection Module
Date: November 2025
"""

import pandas as pd
import os
from datetime import datetime
from typing import Optional
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.sap_connect.sap_client import SAPClient
from backend.sap_connect.config_manager import Config
from backend.sap_connect.utils import ExcelFormatter, Logger


class FinancialStatementsGenerator:
    """Generate financial statements from SAP B1 data."""
    
    def __init__(self, sap_client: SAPClient, config: Config = None, logger: Optional[Logger] = None):
        """
        Initialize financial statements generator.
        
        Args:
            sap_client: Authenticated SAP client
            config: Configuration instance
            logger: Optional logger instance
        """
        self.client = sap_client
        self.config = config or Config()
        self.logger = logger or Logger("FinancialStatements")
    
    def get_trial_balance(self, start_date: str, end_date: str, 
                         use_cache: bool = True) -> pd.DataFrame:
        """
        Generate Trial Balance.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Use cached CSV if available
            
        Returns:
            DataFrame with trial balance
        """
        self.logger.info("Generating Trial Balance...")
        
        # Check for cached data
        cached_file = self.self.config.get_output_path('journal_entries', 'JournalEntries_Flattened.csv')
        
        if use_cache and os.path.exists(cached_file):
            self.logger.info(f"Using cached data from {cached_file}")
            try:
                df_lines = pd.read_csv(cached_file)
                df_lines['TaxDate'] = pd.to_datetime(df_lines['TaxDate'])
                df_lines = df_lines[
                    (df_lines['TaxDate'] >= start_date) & 
                    (df_lines['TaxDate'] <= end_date)
                ]
                self.logger.info(f"Loaded {len(df_lines)} lines from cache")
                lines = df_lines.to_dict('records')
            except Exception as e:
                self.logger.warning(f"Error reading cache: {e}, fetching from API...")
                lines = self._fetch_journal_lines(start_date, end_date)
        else:
            lines = self._fetch_journal_lines(start_date, end_date)
        
        if not lines:
            self.logger.warning("No journal entry lines found")
            return pd.DataFrame()
        
        # Create DataFrame
        df_lines = pd.DataFrame(lines)
        
        # Determine account name column
        account_name_col = 'ShortName' if 'ShortName' in df_lines.columns else 'AccountName'
        group_cols = ['AccountCode', account_name_col] if account_name_col in df_lines.columns else ['AccountCode']
        
        # Aggregate by account
        trial_balance = df_lines.groupby(group_cols).agg({
            'Debit': 'sum',
            'Credit': 'sum',
        }).reset_index()
        
        # Calculate balance
        trial_balance['Balance'] = trial_balance['Debit'] - trial_balance['Credit']
        
        # Add system currency if available
        if 'DebitSys' in df_lines.columns and 'CreditSys' in df_lines.columns:
            sys_balance = df_lines.groupby(['AccountCode']).agg({
                'DebitSys': 'sum',
                'CreditSys': 'sum'
            }).reset_index()
            trial_balance = trial_balance.merge(sys_balance, on='AccountCode', how='left')
            trial_balance['BalanceSys'] = trial_balance['DebitSys'] - trial_balance['CreditSys']
        
        # Rename for consistency
        if account_name_col == 'ShortName':
            trial_balance.rename(columns={'ShortName': 'AccountName'}, inplace=True)
        
        # Sort by account code
        trial_balance.sort_values('AccountCode', inplace=True)
        
        self.logger.success(f"Trial Balance generated: {len(trial_balance)} accounts")
        self.logger.info(f"  Total Debits: {trial_balance['Debit'].sum():,.2f}")
        self.logger.info(f"  Total Credits: {trial_balance['Credit'].sum():,.2f}")
        self.logger.info(f"  Net Balance: {trial_balance['Balance'].sum():,.2f}")
        
        return trial_balance
    
    def _fetch_journal_lines(self, start_date: str, end_date: str) -> list:
        """Fetch journal entry lines from API."""
        date_filter = self.client.build_date_filter('TaxDate', start_date, end_date)
        journal_entries = self.client.fetch_data("JournalEntries", filter_query=date_filter, timeout=180)
        
        self.logger.info(f"Retrieved {len(journal_entries)} journal entries")
        
        lines = []
        for entry in journal_entries:
            if 'JournalEntryLines' in entry and isinstance(entry['JournalEntryLines'], list):
                for line in entry['JournalEntryLines']:
                    line['TaxDate'] = entry.get('TaxDate')
                    line['JdtNum'] = entry.get('JdtNum')
                    lines.append(line)
        
        return lines
    
    def get_balance_sheet(self, as_of_date: str) -> pd.DataFrame:
        """
        Generate Balance Sheet.
        
        Args:
            as_of_date: Balance sheet date (YYYY-MM-DD)
            
        Returns:
            DataFrame with balance sheet
        """
        self.logger.info(f"Generating Balance Sheet as of {as_of_date}...")
        
        # Fetch chart of accounts
        chart_accounts = self.client.fetch_data("ChartOfAccounts")
        self.logger.info(f"Retrieved {len(chart_accounts)} accounts")
        
        # Fetch journal entries up to date
        date_filter = self.client.build_date_filter('TaxDate', '1900-01-01', as_of_date)
        journal_entries = self.client.fetch_data("JournalEntries", filter_query=date_filter)
        self.logger.info(f"Retrieved {len(journal_entries)} journal entries")
        
        # Extract lines
        lines = []
        for entry in journal_entries:
            if 'JournalEntryLines' in entry and isinstance(entry['JournalEntryLines'], list):
                lines.extend(entry['JournalEntryLines'])
        
        if not lines:
            self.logger.warning("No data available for Balance Sheet")
            return pd.DataFrame()
        
        df_lines = pd.DataFrame(lines)
        
        # Aggregate
        balances = df_lines.groupby(['AccountCode', 'ShortName']).agg({
            'Debit': 'sum',
            'Credit': 'sum'
        }).reset_index()
        
        balances['Balance'] = balances['Debit'] - balances['Credit']
        
        # Merge with chart
        df_chart = pd.DataFrame(chart_accounts)
        
        if 'Code' in df_chart.columns and 'AccountType' in df_chart.columns:
            balance_sheet = balances.merge(
                df_chart[['Code', 'Name', 'AccountType']],
                left_on='AccountCode',
                right_on='Code',
                how='left'
            )
            
            # Filter for BS accounts
            bs_types = ['atAssets', 'atLiabilities', 'atEquity', 'at_Assets', 'at_Liabilities', 'at_Equity']
            balance_sheet = balance_sheet[balance_sheet['AccountType'].isin(bs_types)]
            
            balance_sheet.rename(columns={'Name': 'AccountName'}, inplace=True)
            balance_sheet = balance_sheet[['AccountCode', 'AccountName', 'AccountType', 'Balance']]
            balance_sheet.sort_values(['AccountType', 'AccountCode'], inplace=True)
            
            self.logger.success(f"Balance Sheet generated: {len(balance_sheet)} accounts")
        else:
            balance_sheet = balances
            self.logger.warning("Balance Sheet created without account type classification")
        
        return balance_sheet
    
    def get_profit_loss(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Generate Profit & Loss Statement.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with P&L statement
        """
        self.logger.info(f"Generating P&L Statement for {start_date} to {end_date}...")
        
        # Fetch chart of accounts
        chart_accounts = self.client.fetch_data("ChartOfAccounts")
        
        # Fetch journal entries
        date_filter = self.client.build_date_filter('TaxDate', start_date, end_date)
        journal_entries = self.client.fetch_data("JournalEntries", filter_query=date_filter)
        self.logger.info(f"Retrieved {len(journal_entries)} journal entries")
        
        # Extract lines
        lines = []
        for entry in journal_entries:
            if 'JournalEntryLines' in entry and isinstance(entry['JournalEntryLines'], list):
                lines.extend(entry['JournalEntryLines'])
        
        if not lines:
            self.logger.warning("No data available for P&L")
            return pd.DataFrame()
        
        df_lines = pd.DataFrame(lines)
        
        # Aggregate
        pl_balances = df_lines.groupby(['AccountCode', 'ShortName']).agg({
            'Debit': 'sum',
            'Credit': 'sum'
        }).reset_index()
        
        pl_balances['Amount'] = pl_balances['Credit'] - pl_balances['Debit']
        
        # Merge with chart
        df_chart = pd.DataFrame(chart_accounts)
        
        if 'Code' in df_chart.columns and 'AccountType' in df_chart.columns:
            profit_loss = pl_balances.merge(
                df_chart[['Code', 'Name', 'AccountType']],
                left_on='AccountCode',
                right_on='Code',
                how='left'
            )
            
            # Filter for P&L accounts
            pl_types = ['atRevenues', 'atExpenses', 'atOtherIncome', 'atOtherExpenses',
                       'at_Revenues', 'at_Expenses', 'at_OtherIncome', 'at_OtherExpenses']
            profit_loss = profit_loss[profit_loss['AccountType'].isin(pl_types)]
            
            profit_loss.rename(columns={'Name': 'AccountName'}, inplace=True)
            profit_loss = profit_loss[['AccountCode', 'AccountName', 'AccountType', 'Debit', 'Credit', 'Amount']]
            profit_loss.sort_values(['AccountType', 'AccountCode'], inplace=True)
            
            self.logger.success(f"P&L Statement generated: {len(profit_loss)} accounts")
            
            # Calculate totals
            revenue = profit_loss[profit_loss['AccountType'].str.contains('Revenue|Income', case=False, na=False)]['Amount'].sum()
            expenses = profit_loss[profit_loss['AccountType'].str.contains('Expense', case=False, na=False)]['Amount'].sum()
            net_income = revenue - expenses
            
            self.logger.info(f"  Total Revenue: {revenue:,.2f}")
            self.logger.info(f"  Total Expenses: {expenses:,.2f}")
            self.logger.info(f"  Net Income: {net_income:,.2f}")
        else:
            profit_loss = pl_balances
            self.logger.warning("P&L created without account type classification")
        
        return profit_loss
    
    def save_all_statements(self, trial_balance: pd.DataFrame, 
                           balance_sheet: pd.DataFrame,
                           profit_loss: pd.DataFrame, 
                           cashflow: pd.DataFrame,
                           base_filename: Optional[str] = None):
        """
        Save all financial statements.
        
        Args:
            trial_balance: Trial balance DataFrame
            balance_sheet: Balance sheet DataFrame
            profit_loss: P&L DataFrame
            cashflow: Cash flow DataFrame
            base_filename: Base filename (without extension)
        """
        if base_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"Financial_Statements_{timestamp}"
        
        # Save to Excel
        excel_file = self.config.get_output_path('financial_statements', f"{base_filename}.xlsx")
        
        formatter = ExcelFormatter()
        formatter.save_multiple_sheets(
            excel_file,
            {
                'Trial Balance': trial_balance,
                'Balance Sheet': balance_sheet,
                'Profit & Loss': profit_loss,
                'Cash Flow': cashflow
            }
        )
        
        self.logger.success(f"Excel file saved: {excel_file}")
        
        # Save individual CSV files
        if not trial_balance.empty:
            csv_file = self.config.get_output_path('financial_statements', 'Trial_Balance.csv')
            trial_balance.to_csv(csv_file, index=False)
            self.logger.success(f"Trial Balance CSV: {csv_file}")
        
        if not balance_sheet.empty:
            csv_file = self.config.get_output_path('financial_statements', 'Balance_Sheet.csv')
            balance_sheet.to_csv(csv_file, index=False)
            self.logger.success(f"Balance Sheet CSV: {csv_file}")
        
        if not profit_loss.empty:
            csv_file = self.config.get_output_path('financial_statements', 'Profit_Loss.csv')
            profit_loss.to_csv(csv_file, index=False)
            self.logger.success(f"Profit & Loss CSV: {csv_file}")
        
        if not cashflow.empty:
            csv_file = self.config.get_output_path('financial_statements', 'Cash_Flow.csv')
            cashflow.to_csv(csv_file, index=False)
            self.logger.success(f"Cash Flow CSV: {csv_file}")
