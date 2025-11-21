# Sheet Column Extractor Microservice

A lightweight microservice that extracts column headers from Google Sheets. Designed to be invoked from Google Apps Script.

## Features

- Extract column headers from any Google Sheet
- Minimal dependencies (only Google API client libraries)
- Support for service account authentication with delegation
- Compatible with AWS Lambda
- Includes Google Apps Script integration example

## What This Service Does

This microservice does **only one thing**: reads the header row (first row) of a Google Sheet and returns the column names as a JSON array.

## What Was Removed

Compared to the original campaign creation microservice, this service removes:

- Campaign creation logic
- Klaviyo integration
- Trello integration
- Tag management
- Segment validation
- Complex data parsing and transformation
- Pandas data processing (except for basic operations)
- Business logic for audiences, send times, etc.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### As AWS Lambda Function

Deploy `sheet_columns.py` as a Lambda function and invoke with:

```json
{
  "body": "{
    \"sheet_id\": \"your-google-sheet-id\",
    \"sheet_name\": \"Sheet1\",
    \"service_account_key\": \"{...service account JSON...}\",
    \"delegated_email\": \"automation@futuretilt.com\"
  }"
}
```

### Local Testing

```bash
python sheet_columns.py <sheet_id> <service_account.json> [sheet_name] [delegated_email]
```

### From Google Apps Script

See `app_script_example.js` for a complete integration example.

## API Response

Success response:
```json
{
  "success": true,
  "sheet_id": "1abc123...",
  "sheet_name": "Sheet1",
  "columns": ["Campaign Title", "Subject Line", "Send Date", "Audiences"],
  "column_count": 4
}
```

Error response:
```json
{
  "success": false,
  "error": "Error message",
  "error_type": "internal_error"
}
```

## Authentication

Uses Google Service Account with domain-wide delegation. The service account must have:

1. Google Sheets API enabled
2. Domain-wide delegation configured
3. Appropriate scopes: `https://www.googleapis.com/auth/spreadsheets`

## Deployment

1. Package the code and dependencies
2. Deploy to AWS Lambda (or your preferred serverless platform)
3. Configure the endpoint URL in your Apps Script
4. Set up service account credentials in Apps Script properties