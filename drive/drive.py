from __future__ import print_function
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import secretmanager

from io import BytesIO

import codecs
import httplib2
import json


class Drive:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    def __init__(self):
        client = secretmanager.SecretManagerServiceClient()
        project_id = '636214203825'
        secret_id = 'google_service_account_for_the_spreadsheet'
        version_id = '1'

        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict=json.loads(response.payload.data.decode("UTF-8")), scopes=Drive.SCOPES)
        # credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scopes=Drive.SCOPES)

        http = httplib2.Http()
        http = credentials.authorize(http)

        self.service_drive = build('drive', 'v3', http=http)
    
    def upload_shipping_label(self, file_content_base64, filename):
        """
        Upload a shipping label to the drive
        :param file_content_base64: base64 string of the file
        :param filename: name of the file
        :return: file id
        """
        
        if isinstance(file_content_base64, str):
            print("file is a string")
            base64String = bytes(file_content_base64.replace("data:application/pdf;base64,", ""), 'utf-8')
            pdf = BytesIO(codecs.decode(base64String, "base64"))
        else:
            print("file is a bytes")
            pdf = BytesIO(file_content_base64)
    
        # base64String = bytes(file_content_base64.replace("data:application/pdf;base64,", ""), 'utf-8')
        # pdf = BytesIO(codecs.decode(base64String, "base64"))

        # Parent folder
        p_folders = {
            "DHLGMLabels": "Put your folder id here",
            "DHL_GM_AWB": "Put your folder id here",
        }
        p_folder = filename.split("_")[0]
        body = {'name': f'{filename}.pdf', 'parents': [p_folders[p_folder]]}

        media = MediaIoBaseUpload(pdf, mimetype="application/pdf", resumable=True)
        response = self.service_drive.files().create(body=body, media_body=media, supportsAllDrives=True).execute()
        return response['id']

    def create_folder(self, name):
        """
        Create a folder in the drive
        :param name: name of the folder
        :return: folder id
        """
        # SHIPPING_LABELS/<YEAR>/<MONTH>/<CARRIER>_<ORDER_ID>_<CUSTOMER NAME>_<DATE>

        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': ['11EH7q5rF2jQTmFVPG_TiKQ_M_-VkrfqA']
        }

        file = self.service_drive.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()

        print('Folder ID: %s' % file.get('id'))
