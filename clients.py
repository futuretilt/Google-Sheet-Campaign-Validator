import boto3
import logging
import ujson
from ujson import JSONDecodeError
from typing import Dict, Any

from botocore.exceptions import ClientError
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth.exceptions import GoogleAuthError
from googleapiclient.discovery import build
from klaviyo_api import KlaviyoAPI

logger = logging.getLogger()

def get_secret(secret_name: str, region_name: str = "us-east-2") -> Dict[str, Any]:
    """
    Retrieve and parse a secret from AWS Secrets Manager.

    Handles:
    - Flat dicts (e.g. {"api_key": "..."})
    - Nested dicts with "secret_value" (raw string or JSON)
    Always returns a dictionary.
    
    :param secret_name: The name or ARN of the secret.
    :param region_name: AWS region where the secret is stored. Defaults to "us-east-2".
    :return: A dictionary containing the parsed secret.
    """
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    logger.info(f"Getting secret value for {secret_name}")

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response['SecretString']
    except ClientError as e:
        logger.error(f"Failed to retrieve secret '{secret_name}'. Error: {e}", exc_info=True)
        raise

    try:
        parsed = ujson.loads(secret_string)
    except JSONDecodeError:
        logger.debug(f"Wrapped raw string as dict for: {secret_name}")
        return {"value": secret_string}

    if isinstance(parsed, dict) and "secret_value" in parsed:
        inner = parsed["secret_value"]
        try:
            inner_parsed = ujson.loads(inner)
            return inner_parsed
        except JSONDecodeError:
            return {"value": inner}
    else:
        return parsed



def get_bigquery_client() -> bigquery.Client:
    """
    Creates and returns a Google BigQuery client from secret credentials.
    :return: bigquery.Client
    """
    credentials_dict = get_secret("gcp/bigquery")
    try:
        return bigquery.Client(
            credentials=service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        )
    except (GoogleAuthError, JSONDecodeError, ValueError, Exception) as e:
        logger.critical(f"Could not create Google client. Error: {e}", exc_info=True)
        raise


def get_klaviyo_client(dataset_id: str, max_delay: int = None, max_retries: int = None) -> KlaviyoAPI:
    """
    Creates a KlaviyoAPI client for a specific dataset/client.
    :param dataset_id: Identifier used in the secret name
    :param max_delay: Optional max delay for retries
    :param max_retries: Optional max retry count
    :return: KlaviyoAPI instance
    """
    secret = get_secret(f"klaviyo/{dataset_id}_create_campaigns")
    try:
        # Support both nested and flat keys
        api_key = secret.get("api_key") or secret.get("value")
        kwargs = {}
        if max_delay is not None:
            kwargs['max_delay'] = max_delay
        if max_retries is not None:
            kwargs['max_retries'] = max_retries
        return KlaviyoAPI(api_key, **kwargs)
    except Exception as e:
        logger.critical(f"Could not create Klaviyo client. Error: {e}", exc_info=True)
        raise



def get_sheets_client(delegated_email: str = "automation@futuretilt.com"):
    """
    Creates and returns a Google Sheets API client from secret credentials.
    :param delegated_email: Email to delegate authentication to
    :return: Google Sheets service object
    """
    credentials_dict = get_secret("gcp/sheets")
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPES
        )

        # Create delegated credentials
        delegated_credentials = credentials.with_subject(delegated_email)

        return build('sheets', 'v4', credentials=delegated_credentials)
    except (GoogleAuthError, JSONDecodeError, ValueError, Exception) as e:
        logger.critical(f"Could not create Google Sheets client. Error: {e}", exc_info=True)
        raise


def get_trello_client() -> Dict[str, Any]:
    """
    Retrieves Trello credentials from secret manager.
    :return: Dict containing Trello API credentials
    """
    try:
        return get_secret("trello/api_keys")
    except Exception as e:
        logger.critical(f"Could not retrieve Trello API credentials. Error: {e}", exc_info=True)
        raise
