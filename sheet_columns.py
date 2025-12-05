import ujson
import logging
import os
from clients import get_sheets_client

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SheetColumnExtractor:
    def __init__(self, delegated_email: str = "automation@futuretilt.com"):
        """
        Initialize the Sheet Column Extractor.

        Args:
            delegated_email: Email to delegate authentication to
        """
        self.delegated_email = delegated_email

    def get_sheets_service(self):
        """Create and return authorized Google Sheets API service."""
        try:
            return get_sheets_client(self.delegated_email)
        except Exception as e:
            logger.error(f"Failed to get sheets service: {str(e)}")
            raise

    def get_sheet_columns(self, sheet_id: str, sheet_name: str = None) -> list:
        """
        Extract column headers from a Google Sheet.

        Args:
            sheet_id: Google Sheets document ID
            sheet_name: Name of the sheet (optional, uses first sheet if None)

        Returns:
            List of column header names
        """
        try:
            sheets_service = self.get_sheets_service()

            # If no sheet name provided, get the first sheet
            if not sheet_name:
                spreadsheet = sheets_service.spreadsheets().get(
                    spreadsheetId=sheet_id
                ).execute()
                sheet_name = spreadsheet['sheets'][0]['properties']['title']
                logger.info(f"Using first sheet: {sheet_name}")

            # Get only the first row (headers)
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{sheet_name}!1:1",  # Only first row
                valueRenderOption='UNFORMATTED_VALUE'
            ).execute()

            values = result.get('values', [])

            if not values or not values[0]:
                logger.warning(f"No header row found in sheet '{sheet_name}'")
                return []

            headers = values[0]
            logger.info(f"Found {len(headers)} columns in sheet '{sheet_name}'")
            return headers

        except Exception as e:
            logger.error(f"Failed to get sheet columns: {str(e)}")
            raise


def lambda_handler(event, context):
    """
    AWS Lambda handler for extracting sheet columns.

    Expected event body:
    {
        "sheet_id": "Google Sheets ID",
        "sheet_name": "Sheet name (optional)",
        "delegated_email": "email@domain.com (optional)"
    }
    """
    try:
        # Parse request body
        body_str = event.get("body")
        if not body_str:
            raise ValueError("Request body is missing")

        data = ujson.loads(body_str)

        # Extract required parameters
        sheet_id = data.get("sheet_id")
        sheet_name = data.get("sheet_name")
        delegated_email = data.get("delegated_email", "automation@futuretilt.com")

        if not sheet_id:
            raise ValueError("Missing sheet_id")

        # Extract columns
        extractor = SheetColumnExtractor(delegated_email)
        columns = extractor.get_sheet_columns(sheet_id, sheet_name)

        return {
            "statusCode": 200,
            "body": ujson.dumps({
                "success": True,
                "sheet_id": sheet_id,
                "sheet_name": sheet_name,
                "columns": columns,
                "column_count": len(columns)
            })
        }

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            "statusCode": 500,
            "body": ujson.dumps({
                "success": False,
                "error": str(e),
                "error_type": "internal_error"
            })
        }


# For local testing
def main():
    """Local testing function."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sheet_columns.py <sheet_id> [sheet_name] [delegated_email]")
        return

    sheet_id = sys.argv[1]
    sheet_name = sys.argv[2] if len(sys.argv) > 2 else None
    delegated_email = sys.argv[3] if len(sys.argv) > 3 else "automation@futuretilt.com"

    try:
        # Extract columns
        extractor = SheetColumnExtractor(delegated_email)
        columns = extractor.get_sheet_columns(sheet_id, sheet_name)

        print(f"Sheet columns ({len(columns)}):")
        for i, col in enumerate(columns, 1):
            print(f"{i:2d}. {col}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()