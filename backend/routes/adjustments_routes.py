"""
Adjustments Analysis Routes
Provides endpoints for analyzing manual adjustments with industry-standard classifications
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import pandas as pd

from backend.services.adjustment_impact_service import AdjustmentImpactService
from backend.services.final_tb_summary_service import FinalTrialBalanceSummaryService

router = APIRouter(prefix="/adjustments", tags=["Adjustments"])



class AdjustmentSummary(BaseModel):
    """Summary of adjustment classifications"""
    classification: str
    count: int
    total_debit: float
    total_credit: float
    net_impact: float


class AdjustmentDetail(BaseModel):
    """Detailed adjustment entry"""
    account: str
    debit: float
    credit: float
    description: str
    schedule_iii_head: str
    compliance_impact: str
    adjustment_classification: str
    compliance_standard: str
    file_source: str


class AdjustmentAnalysisResponse(BaseModel):
    """Response model for adjustment analysis"""
    entity: str
    total_adjustments: int
    total_files: int
    summary_by_classification: List[AdjustmentSummary]
    summary_by_schedule_iii: List[Dict]
    adjustments: List[AdjustmentDetail]


# Industry-standard adjustment classifications
ADJUSTMENT_CLASSIFICATIONS = {
    # Accrual-based adjustments
    "accrual": "Accruals and Deferrals",
    "prepaid": "Accruals and Deferrals",
    "deferred": "Accruals and Deferrals",
    "unearned": "Accruals and Deferrals",
    "accrue": "Accruals and Deferrals",
    
    # Reclassification adjustments
    "reclass": "Reclassification",
    "reclassify": "Reclassification",
    "transfer": "Reclassification",
    "misclassification": "Reclassification",
    
    # Depreciation and amortization
    "depreciation": "Depreciation and Amortization",
    "amortization": "Depreciation and Amortization",
    "depreciate": "Depreciation and Amortization",
    "amortize": "Depreciation and Amortization",
    
    # Provisions and impairments
    "provision": "Provisions and Impairments",
    "impairment": "Provisions and Impairments",
    "allowance": "Provisions and Impairments",
    "bad debt": "Provisions and Impairments",
    "doubtful": "Provisions and Impairments",
    "write-off": "Provisions and Impairments",
    "writeoff": "Provisions and Impairments",
    
    # Inventory adjustments
    "inventory": "Inventory Adjustments",
    "stock": "Inventory Adjustments",
    "obsolescence": "Inventory Adjustments",
    "shrinkage": "Inventory Adjustments",
    
    # Foreign currency adjustments
    "forex": "Foreign Exchange Adjustments",
    "foreign exchange": "Foreign Exchange Adjustments",
    "currency": "Foreign Exchange Adjustments",
    "translation": "Foreign Exchange Adjustments",
    "exchange rate": "Foreign Exchange Adjustments",
    
    # Intercompany eliminations
    "intercompany": "Intercompany Eliminations",
    "interco": "Intercompany Eliminations",
    "inter-company": "Intercompany Eliminations",
    "elimination": "Intercompany Eliminations",
    
    # Revenue recognition adjustments
    "revenue recognition": "Revenue Recognition Adjustments",
    "deferred revenue": "Revenue Recognition Adjustments",
    "unbilled": "Revenue Recognition Adjustments",
    
    # Tax adjustments
    "tax": "Tax Adjustments",
    "deferred tax": "Tax Adjustments",
    "income tax": "Tax Adjustments",
    "gst": "Tax Adjustments",
    "vat": "Tax Adjustments",
    
    # Prior period adjustments
    "prior period": "Prior Period Adjustments",
    "prior year": "Prior Period Adjustments",
    "correction": "Prior Period Adjustments",
    "error": "Prior Period Adjustments",
    
    # Period cutoff and timing adjustments
    "cutoff": "Period Cutoff Adjustments",
    "cut-off": "Period Cutoff Adjustments",
    "correct period": "Period Cutoff Adjustments",
    "wrong period": "Period Cutoff Adjustments",
    "period correction": "Period Cutoff Adjustments",
    "timing": "Period Cutoff Adjustments",
    "timing difference": "Period Cutoff Adjustments",
    "enc": "Period Cutoff Adjustments",
    "ensure correct": "Period Cutoff Adjustments",
    "period shift": "Period Cutoff Adjustments",
    "period adjustment": "Period Cutoff Adjustments",
    
    # Fair value and revaluation
    "fair value": "Fair Value and Revaluation",
    "revaluation": "Fair Value and Revaluation",
    "mark to market": "Fair Value and Revaluation",
    "mtm": "Fair Value and Revaluation",
    
    # Consolidation adjustments
    "consolidation": "Consolidation Adjustments",
    "goodwill": "Consolidation Adjustments",
    "minority interest": "Consolidation Adjustments",
    "nci": "Consolidation Adjustments",
    
    # Year-end closing adjustments
    "closing": "Year-End Closing Adjustments",
    "year end": "Year-End Closing Adjustments",
    "period end": "Year-End Closing Adjustments",
    
    # Audit adjustments
    "audit": "Audit Adjustments",
    "aje": "Audit Adjustments",
    "pje": "Audit Adjustments",
    "audit adjustment": "Audit Adjustments",
    "proposed": "Audit Adjustments"
}

SCHEDULE_III_MAPPING = {
    "Cash": "Cash and Cash Equivalents",
    "Bank": "Cash and Cash Equivalents",
    "Fixed Assets": "Property, Plant and Equipment",
    "Inventory": "Inventories",
    "Accounts Receivable": "Trade Receivables",
    "Accounts Payable": "Trade Payables",
    "Loan": "Borrowings",
    "Equity": "Equity Share Capital",
    "Sales": "Revenue from Operations",
    "Purchase": "Cost of Materials Consumed",
    "Depreciation": "Depreciation and Amortization Expense"
}

# Keyword-based Schedule III mapping (for GL descriptions)
SCHEDULE_III_KEYWORDS = {
    "Cash and Cash Equivalents": ["cash", "bank", "fca", "deposit", "f.deposit", "petty cash"],
    "Trade Receivables": ["receivable", "trade debtor", "debtor", "ar", "owing from", "amount owing from"],
    "Inventories": ["inventory", "stock", "wip", "work in progress"],
    "Property, Plant and Equipment": ["ppe", "fixed asset", "equipment", "machinery", "vehicle", "building", "furniture", "rou"],
    "Intangible Assets": ["intangible", "goodwill", "patent", "trademark", "software", "write off"],
    "Investments": ["investment", "equity", "bond", "shares"],
    "Other Current Assets": ["prepayment", "prepaid", "advance", "other current"],
    "Trade Payables": ["payable", "trade creditor", "creditor", "ap", "vendor", "owing to", "amount owing to"],
    "Borrowings": ["loan", "borrowing", "term loan", "overdraft", "credit facility"],
    "Lease Liabilities": ["lease", "hp", "hire purchase", "finance lease"],
    "Current Tax Liabilities": ["taxation", "tax payable", "prov.for taxation", "provision for tax", "tax (temp)"],
    "Deferred Tax Liabilities": ["deferred tax", "deferred taxation"],
    "Revenue from Operations": ["sales", "revenue", "income", "turnover"],
    "Cost of Materials Consumed": ["purchase", "cogs", "cost of sales", "material"],
    "Employee Benefits": ["salary", "wages", "epf", "socso", "payroll", "bonus"],
    "Depreciation and Amortization Expense": ["depreciation", "amortization", "amortisation", "accum.dep"],
    "Finance Costs": ["interest", "finance cost", "finance charge"],
    "Other Income": ["other income", "misc income", "sundry income", "exchange gain"],
    "Other Expenses": ["expense", "charges", "professional fees", "rental", "consultancy", "exchange loss", "unrealised exchange"]
}

def map_schedule_iii(account_text: str) -> str:
    """Map account to Schedule III head using keyword matching"""
    if not account_text or str(account_text).strip() == '':
        return "Unclassified"
    
    account_lower = str(account_text).lower()
    
    # First try exact mapping (for legacy support)
    for key, value in SCHEDULE_III_MAPPING.items():
        if key.lower() in account_lower:
            return value
    
    # Then try keyword-based mapping
    for schedule_head, keywords in SCHEDULE_III_KEYWORDS.items():
        for keyword in keywords:
            if keyword in account_lower:
                return schedule_head
    
    return "Unclassified"

IND_AS_IMPACT = {
    "Revenue": "Ind AS 115 - Revenue Recognition",
    "Depreciation": "Ind AS 16 - Property, Plant & Equipment",
    "Loan": "Ind AS 109 - Financial Instruments",
    "Inventory": "Ind AS 2 - Valuation of Inventories"
}

IFRS_IMPACT = {
    "Revenue": "IFRS 15 - Revenue from Contracts with Customers",
    "Loan": "IFRS 9 - Financial Instruments",
    "Inventory": "IAS 2 - Inventories"
}


def categorize_adjustment(desc: str) -> str:
    """Categorize adjustment based on description"""
    desc_lower = str(desc).lower()
    for keyword, category in ADJUSTMENT_CLASSIFICATIONS.items():
        if keyword in desc_lower:
            return category
    return "Other Adjustments"


@router.get("/analyze/{entity}", response_model=AdjustmentAnalysisResponse)
async def analyze_adjustments(
    entity: str,
    period: Optional[str] = Query(None, description="Period filter (optional)")
):
    """
    Analyze manual adjustments for an entity with industry-standard classifications
    """
    try:
        # Construct path to manual adjustments folder
        base_dir = Path(__file__).parent.parent.parent
        folder_path = base_dir / "data" / entity / "input" / "manual-adjustments"
        
        # If folder doesn't exist or no files, return empty response
        if not folder_path.exists():
            return AdjustmentAnalysisResponse(
                entity=entity,
                total_adjustments=0,
                total_files=0,
                summary_by_classification=[],
                summary_by_schedule_iii=[],
                adjustments=[]
            )
        
        # Get all Excel files
        adjustment_files = list(folder_path.glob("*.xlsx"))
        
        if not adjustment_files:
            return AdjustmentAnalysisResponse(
                entity=entity,
                total_adjustments=0,
                total_files=0,
                summary_by_classification=[],
                summary_by_schedule_iii=[],
                adjustments=[]
            )
        
        all_adjustments = []
        
        for file_path in adjustment_files:
            try:
                df = pd.read_excel(file_path, engine="openpyxl")
                
                # Handle different file formats
                # Format 1: GL Code, GL Description, adjustment columns
                if 'GL Code' in df.columns and 'GL Description' in df.columns:
                    # Get all adjustment columns (containing 'Adj', 'Reclass', etc.)
                    adjustment_cols = [col for col in df.columns 
                                     if any(keyword in str(col) for keyword in 
                                           ['Adj', 'adj', 'Reclass', 'reclass', 'Audit', 'audit', 'adjusted', 'value'])]
                    
                    if not adjustment_cols:
                        print(f"No adjustment columns found in {file_path.name}")
                        continue
                    
                    # Transform to standard format
                    records = []
                    for _, row in df.iterrows():
                        account = str(row.get('GL Code', ''))
                        description = str(row.get('GL Description', '') or row.get('GL Code Description', ''))
                        
                        for adj_col in adjustment_cols:
                            value = row.get(adj_col, 0)
                            if pd.notna(value) and value != 0:
                                records.append({
                                    'Account': account,
                                    'Description': f"{description} - {adj_col}",
                                    'Debit': float(value) if value > 0 else 0,
                                    'Credit': abs(float(value)) if value < 0 else 0
                                })
                    
                    if records:
                        df = pd.DataFrame(records)
                    else:
                        continue
                
                # Format 1b: GL Code, GL Code Description, total_adjusted_value (Analisa format)
                elif 'GL Code' in df.columns and 'GL Code Description' in df.columns and 'total_adjusted_value' in df.columns:
                    records = []
                    for _, row in df.iterrows():
                        account = str(row.get('GL Code', ''))
                        description = str(row.get('GL Code Description', ''))
                        value = row.get('total_adjusted_value', 0)
                        
                        if pd.notna(value) and value != 0:
                            records.append({
                                'Account': account,
                                'Description': description,
                                'Debit': float(value) if value > 0 else 0,
                                'Credit': abs(float(value)) if value < 0 else 0
                            })
                    
                    if records:
                        df = pd.DataFrame(records)
                    else:
                        continue
                        
                # Format 2: Standard Account, Debit, Credit, Description
                else:
                    # Ensure required columns exist
                    for col in ["Account", "Debit", "Credit", "Description"]:
                        if col not in df.columns:
                            df[col] = ""
                
                # Convert numeric columns
                df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0)
                df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0)
                
                # Detect compliance standard
                compliance_standard = "Ind AS / Schedule III"
                if "USD" in file_path.name or "IFRS" in file_path.name or "USGAAP" in file_path.name:
                    compliance_standard = "IFRS / US GAAP"
                
                # Convert numeric columns
                df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0)
                df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0)
                
                # Detect compliance standard
                compliance_standard = "Ind AS / Schedule III"
                if "USD" in file_path.name or "IFRS" in file_path.name or "USGAAP" in file_path.name:
                    compliance_standard = "IFRS / US GAAP"
                
                # Map Schedule III Head using both Account and Description
                df["ScheduleIIIHead"] = df.apply(
                    lambda row: map_schedule_iii(f"{row.get('Account', '')} {row.get('Description', '')}"),
                    axis=1
                )
                
                # Map compliance impact
                if compliance_standard.startswith("IFRS"):
                    df["ComplianceImpact"] = df["Account"].apply(
                        lambda x: IFRS_IMPACT.get(str(x), "General IFRS Compliance")
                    )
                else:
                    df["ComplianceImpact"] = df["Account"].apply(
                        lambda x: IND_AS_IMPACT.get(str(x), "General Ind AS Compliance")
                    )
                
                # Classify adjustments - use both Description and file name
                df["AdjustmentClassification"] = df.apply(
                    lambda row: categorize_adjustment(f"{row['Description']} {file_path.name}"),
                    axis=1
                )
                df["ComplianceStandard"] = compliance_standard
                df["FileSource"] = file_path.name
                
                # Convert numeric columns
                df["Debit"] = pd.to_numeric(df["Debit"], errors='coerce').fillna(0)
                df["Credit"] = pd.to_numeric(df["Credit"], errors='coerce').fillna(0)
                
                all_adjustments.append(df)
                
            except Exception as e:
                print(f"Error processing {file_path.name}: {str(e)}")
                continue
        
        if not all_adjustments:
            raise HTTPException(
                status_code=500,
                detail="Failed to process any adjustment files"
            )
        
        # Combine all adjustments
        adjustments_df = pd.concat(all_adjustments, ignore_index=True)
        
        # Generate summary by classification
        classification_summary = []
        for classification in adjustments_df["AdjustmentClassification"].unique():
            subset = adjustments_df[adjustments_df["AdjustmentClassification"] == classification]
            total_debit = float(subset["Debit"].sum())
            total_credit = float(subset["Credit"].sum())
            
            classification_summary.append(AdjustmentSummary(
                classification=classification,
                count=len(subset),
                total_debit=total_debit,
                total_credit=total_credit,
                net_impact=total_debit - total_credit
            ))
        
        # Sort by count descending
        classification_summary.sort(key=lambda x: x.count, reverse=True)
        
        # Generate summary by Schedule III
        schedule_iii_summary = []
        for schedule_head in adjustments_df["ScheduleIIIHead"].unique():
            subset = adjustments_df[adjustments_df["ScheduleIIIHead"] == schedule_head]
            schedule_iii_summary.append({
                "schedule_iii_head": schedule_head,
                "count": len(subset),
                "total_debit": float(subset["Debit"].sum()),
                "total_credit": float(subset["Credit"].sum())
            })
        
        # Convert to list of AdjustmentDetail
        adjustments_list = []
        for _, row in adjustments_df.iterrows():
            adjustments_list.append(AdjustmentDetail(
                account=str(row["Account"]),
                debit=float(row["Debit"]),
                credit=float(row["Credit"]),
                description=str(row["Description"]),
                schedule_iii_head=str(row["ScheduleIIIHead"]),
                compliance_impact=str(row["ComplianceImpact"]),
                adjustment_classification=str(row["AdjustmentClassification"]),
                compliance_standard=str(row["ComplianceStandard"]),
                file_source=str(row["FileSource"])
            ))
        
        return AdjustmentAnalysisResponse(
            entity=entity,
            total_adjustments=len(adjustments_df),
            total_files=len(adjustment_files),
            summary_by_classification=classification_summary,
            summary_by_schedule_iii=schedule_iii_summary,
            adjustments=adjustments_list
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing adjustments: {str(e)}"
        )


@router.get("/impact-summary/{entity}")
async def get_adjustment_impact_summary(entity: str):
    """
    Get before/after adjustment impact summary
    
    Compares unaudited trial balance with adjusted trial balance to show:
    - Impact by financial statement category (Assets, Liabilities, Equity, Revenue, Expenses)
    - GL-level changes
    - Material changes requiring attention
    - Impact by adjustment type
    """
    try:
        impact_service = AdjustmentImpactService(entity)
        result = impact_service.analyze_impact()
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing adjustment impact: {str(e)}"
        )


@router.get("/final-tb-summary/{entity}")
async def get_final_tb_summary(entity: str):
    """
    Get summary analysis of final trial balance by BSPL and Ind AS Major categories
    
    This endpoint analyzes the final trial balance file and provides:
    - Overall summary (total unaudited vs adjusted)
    - BSPL category breakdown (BS vs PL)
    - Ind AS Major category breakdown (dynamic based on data)
    
    Args:
        entity: Entity code (e.g., 'cpm', 'lifeline_diagnostics')
    
    Returns:
        Summary statistics by BSPL and Ind AS Major categories
    """
    try:
        summary_service = FinalTrialBalanceSummaryService(entity)
        result = summary_service.analyze_final_tb()
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing final trial balance: {str(e)}"
        )
