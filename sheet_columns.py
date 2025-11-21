from google.oauth2 import service_account
from googleapiclient.discovery import build
import ujson
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SheetColumnExtractor:
    def __init__(self, service_account_info: dict, delegated_email: str):
        """
        Initialize the Sheet Column Extractor.

        Args:
            service_account_info: Service account credentials dict
            delegated_email: Email to delegate authentication to
        """
        self.service_account_info = service_account_info
        self.delegated_email = delegated_email

    def get_sheets_service(self):
        """Create and return authorized Google Sheets API service."""
        try:
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

            credentials = service_account.Credentials.from_service_account_info(
                self.service_account_info,
                scopes=SCOPES
            )

            # Create delegated credentials
            delegated_credentials = credentials.with_subject(self.delegated_email)

            return build('sheets', 'v4', credentials=delegated_credentials)

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
        "service_account_key": "Service account JSON string",
        "delegated_email": "email@domain.com"
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
        service_account_key = data.get("service_account_key")
        delegated_email = data.get("delegated_email")

        if not sheet_id:
            raise ValueError("Missing sheet_id")
        if not service_account_key:
            raise ValueError("Missing service_account_key")
        if not delegated_email:
            raise ValueError("Missing delegated_email")

        # Parse service account info
        if isinstance(service_account_key, str):
            service_account_info = ujson.loads(service_account_key)
        else:
            service_account_info = service_account_key

        # Extract columns
        extractor = SheetColumnExtractor(service_account_info, delegated_email)
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

    if len(sys.argv) < 3:
        print("Usage: python sheet_columns.py <sheet_id> <service_account_json_file> [sheet_name] [delegated_email]")
        return

    sheet_id = sys.argv[1]
    service_account_file = sys.argv[2]
    sheet_name = sys.argv[3] if len(sys.argv) > 3 else None
    delegated_email = sys.argv[4] if len(sys.argv) > 4 else "automation@futuretilt.com"

    try:
        # Load service account info
        with open(service_account_file, 'r') as f:
            service_account_info = ujson.load(f)

        # Extract columns
        extractor = SheetColumnExtractor(service_account_info, delegated_email)
        columns = extractor.get_sheet_columns(sheet_id, sheet_name)

        print(f"Sheet columns ({len(columns)}):")
        for i, col in enumerate(columns, 1):
            print(f"{i:2d}. {col}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()