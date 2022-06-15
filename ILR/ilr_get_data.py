import os
import base64

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()
TOKEN_DICT = {
    "type": os.getenv('TYPE_ILR'),
    "project_id": os.getenv('PROJECT_ID_ILR'),
    "private_key_id": os.getenv('PRIVATE_KEY_ID_ILR'),
    "private_key": base64.b64decode(
        os.getenv('PRIVATE_KEY_ILR')
    ).decode("UTF-8"),
    "client_email": os.getenv('CLIENT_EMAIL_ILR'),
    "client_id": os.getenv('CLIENT_ID_ILR'),
    "auth_uri": os.getenv('AUTH_URI_ILR'),
    "token_uri": os.getenv('TOKEN_URI_ILR'),
    "auth_provider_x509_cert_url": os.getenv('AUTH_PROVIDER_ILR'),
    "client_x509_cert_url": os.getenv('CLIENT_CERT_ILR')
}


def get_all_data_ilr():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(TOKEN_DICT, scope)
    client = gspread.authorize(creds)
    sheet = client.open('Results_Run_AllData')
    sheet_instance = sheet.get_worksheet(0)
    records_data = sheet_instance.get_all_records()
    df = pd.DataFrame(records_data)
    return df.dropna()
