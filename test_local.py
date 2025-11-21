#!/usr/bin/env python3
"""
Test script for local development and testing of the sheet column extractor.
"""

import ujson
from sheet_columns import SheetColumnExtractor

def test_column_extraction():
    """Test the column extraction functionality."""

    # Mock service account info (replace with real values for actual testing)
    mock_service_account = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
        "client_email": "service-account@your-project.iam.gserviceaccount.com",
        "client_id": "client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
    }

    # Test parameters
    sheet_id = "1your-sheet-id-here"  # Replace with actual sheet ID
    sheet_name = "Sheet1"  # Replace with actual sheet name
    delegated_email = "automation@futuretilt.com"

    try:
        # Create extractor instance
        extractor = SheetColumnExtractor(mock_service_account, delegated_email)

        # Extract columns
        print(f"Extracting columns from sheet: {sheet_id}")
        print(f"Sheet name: {sheet_name}")
        print(f"Delegated email: {delegated_email}")
        print("-" * 50)

        columns = extractor.get_sheet_columns(sheet_id, sheet_name)

        print(f"Success! Found {len(columns)} columns:")
        for i, col in enumerate(columns, 1):
            print(f"{i:2d}. {col}")

    except Exception as e:
        print(f"Error during testing: {e}")
        print("Make sure to:")
        print("1. Replace mock_service_account with real credentials")
        print("2. Replace sheet_id with a real Google Sheet ID")
        print("3. Ensure your service account has proper permissions")

def test_lambda_handler():
    """Test the lambda handler function."""
    from sheet_columns import lambda_handler

    # Mock Lambda event
    event = {
        "body": ujson.dumps({
            "sheet_id": "1your-sheet-id-here",
            "sheet_name": "Sheet1",
            "service_account_key": ujson.dumps({
                "type": "service_account",
                "project_id": "your-project-id",
                # ... other service account fields
            }),
            "delegated_email": "automation@futuretilt.com"
        })
    }

    context = {}  # Mock context

    try:
        response = lambda_handler(event, context)
        print("Lambda handler response:")
        print(ujson.dumps(ujson.loads(response['body']), indent=2))

    except Exception as e:
        print(f"Lambda handler test failed: {e}")

if __name__ == "__main__":
    print("=== Sheet Column Extractor Test ===")
    print()

    print("1. Testing direct column extraction...")
    test_column_extraction()
    print()

    print("2. Testing Lambda handler...")
    test_lambda_handler()
    print()

    print("Note: These tests use mock data. Replace with real credentials for actual testing.")