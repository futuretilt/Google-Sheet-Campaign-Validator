/**
 * Google Apps Script function to call the sheet column extractor microservice
 *
 * This should be deployed as a Google Apps Script and can be triggered
 * from within a Google Sheet or as a web app.
 */

function getSheetColumns() {
  // Get the active spreadsheet and sheet
  const sheet = SpreadsheetApp.getActiveSheet();
  const spreadsheetId = SpreadsheetApp.getActiveSpreadsheet().getId();
  const sheetName = sheet.getName();

  // Configure your microservice endpoint
  const MICROSERVICE_URL = "https://your-lambda-url.amazonaws.com/prod/extract-columns";

  // Service account configuration (store these securely in Apps Script properties)
  const SERVICE_ACCOUNT_KEY = PropertiesService.getScriptProperties().getProperty('SERVICE_ACCOUNT_KEY');
  const DELEGATED_EMAIL = "automation@futuretilt.com";

  try {
    // Prepare request payload
    const payload = {
      sheet_id: spreadsheetId,
      sheet_name: sheetName,
      service_account_key: SERVICE_ACCOUNT_KEY,
      delegated_email: DELEGATED_EMAIL
    };

    // Make request to microservice
    const response = UrlFetchApp.fetch(MICROSERVICE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify(payload)
    });

    const responseData = JSON.parse(response.getContentText());

    if (responseData.success) {
      // Display columns in current sheet (for demonstration)
      Logger.log(`Found ${responseData.column_count} columns:`);
      responseData.columns.forEach((column, index) => {
        Logger.log(`${index + 1}. ${column}`);
      });

      // You can also write the results somewhere in the sheet
      const outputRange = sheet.getRange('A1:A' + responseData.columns.length);
      const columnData = responseData.columns.map(col => [col]);
      outputRange.setValues(columnData);

      SpreadsheetApp.getUi().alert(
        `Success! Found ${responseData.column_count} columns.\\n` +
        `Check the logs and column A for the results.`
      );

      return responseData.columns;

    } else {
      throw new Error(responseData.error || 'Unknown error occurred');
    }

  } catch (error) {
    Logger.log('Error calling microservice: ' + error.toString());
    SpreadsheetApp.getUi().alert('Error: ' + error.toString());
    return null;
  }
}

/**
 * Function to set up the service account key in Apps Script properties
 * Run this once to configure your service account credentials
 */
function setupServiceAccount() {
  // Replace this with your actual service account JSON
  const serviceAccountJson = `{
    "type": "service_account",
    "project_id": "your-project-id",
    "private_key_id": "key-id",
    "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
    "client_email": "service-account@your-project.iam.gserviceaccount.com",
    "client_id": "client-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
  }`;

  PropertiesService.getScriptProperties().setProperty('SERVICE_ACCOUNT_KEY', serviceAccountJson);
  SpreadsheetApp.getUi().alert('Service account key configured successfully!');
}

/**
 * Create a custom menu in the Google Sheet
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Sheet Column Extractor')
    .addItem('Get Sheet Columns', 'getSheetColumns')
    .addSeparator()
    .addItem('Setup Service Account', 'setupServiceAccount')
    .addToUi();
}