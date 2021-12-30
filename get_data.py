import os

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

TOKEN_DICT = {
    "type": os.environ.get('TYPE'),
    "project_id": os.environ.get('PROJECT_ID'),
    "private_key_id": os.environ.get('PRIVATE_KEY_ID'),
    "private_key": os.environ.get('PRIVATE_KEY'),
    "client_email": os.environ.get('CLIENT_EMAIL'),
    "client_id": os.environ.get('CLIENT_ID'),
    "auth_uri": os.environ.get('AUTH_URI'),
    "token_uri": os.environ.get('TOKEN_URI'),
    "auth_provider_x509_cert_url": os.environ.get('AUTH_PROVIDER'),
    "client_x509_cert_url": os.environ.get('CLIENT_CERT')
}


def get_all_data():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(TOKEN_DICT, scope)
    client = gspread.authorize(creds)
    sheet = client.open('Results_AllData')
    sheet_instance = sheet.get_worksheet(0)
    records_data = sheet_instance.get_all_records()
    df = pd.DataFrame(records_data)
    return df.dropna()
