"""
Category mapping service for GL code mapping
"""

import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from backend.services.path_service import PathService


class MappingService:
    """Service for mapping GL codes to categories"""

    def __init__(self):
        pass

    async def map_categories(self, entity: str) -> Dict[str, Any]:
        """Map GL codes to major/minor categories"""
        try:
            # Import the mapping module
            from backend.utils.tb_map_major_minor_categories import (
                get_mapping_summary,
                map_categories,
            )

            # Run mapping with entity parameter
            success, message, output_file = map_categories(entity)

            if success:
                # Get mapping summary
                summary = get_mapping_summary(output_file)

                return {
                    "success": True,
                    "message": "Category mapping completed successfully",
                    "total_records": summary.get('total_records', 0),
                    "mapped_records": summary.get('mapped_records', 0),
                    "unmapped_records": summary.get('unmapped_records', 0),
                    "output_path": output_file,
                    "summary": summary
                }

            return {
                "success": False,
                "message": message,
                "total_records": 0,
                "mapped_records": 0,
                "unmapped_records": 0,
                "output_path": None
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Mapping error: {str(e)}",
                "total_records": 0,
                "mapped_records": 0,
                "unmapped_records": 0,
                "output_path": None
            }

    async def get_mapping_reference(self, entity: str) -> Dict[str, Any]:
        """Get the mapping reference file information

        Args:
            entity: Entity name
        """
        try:
            path_service = PathService(entity)
            reference_path = path_service.get_mapping_file_path(entity)

            if not reference_path.exists():
                return {
                    "exists": False,
                    "message": "Reference mapping file not found"
                }

            # Read the reference file
            df = pd.read_excel(reference_path)

            # Get category breakdown
            category_breakdown = {}
            if 'BSPL' in df.columns:
                category_breakdown['bspl'] = df['BSPL'].value_counts().to_dict()
            if 'Ind AS Major' in df.columns:
                category_breakdown['major'] = df['Ind AS Major'].value_counts().to_dict()

            return {
                "exists": True,
                "total_mappings": len(df),
                "columns": list(df.columns),
                "category_breakdown": category_breakdown,
                "file_size": reference_path.stat().st_size,
                "file_path": str(reference_path)
            }

        except Exception as e:
            return {
                "exists": False,
                "error": str(e)
            }

    async def search_mappings(self, search_term: str, entity: str) -> Dict[str, Any]:
        """Search mappings by GL code or description

        Args:
            search_term: Term to search for in mappings
            entity: Entity name
        """
        try:
            path_service = PathService(entity)
            reference_path = path_service.get_mapping_file_path(entity)

            if not reference_path.exists():
                return {
                    "success": False,
                    "message": "Reference mapping file not found"
                }

            # Read the reference file
            df = pd.read_excel(reference_path)

            # Filter based on search term
            if search_term:
                filtered_df = df[
                    df.astype(str).apply(
                        lambda row: row.str.contains(search_term, case=False, na=False).any(),
                        axis=1
                    )
                ]
            else:
                filtered_df = df

            # Convert to records for JSON serialization
            records = filtered_df.to_dict('records')

            return {
                "success": True,
                "total_results": len(records),
                "search_term": search_term,
                "results": records[:100]  # Limit to first 100 results
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Search error: {str(e)}"
            }
