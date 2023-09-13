from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import secretmanager
import httplib2
import json


class Sheets:
    """
    This class is used for production purposes only.
    """
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    def __init__(self):
        client = secretmanager.SecretManagerServiceClient()
        project_id = 'your_project_id'
        secret_id = 'google_service_account_for_the_spreadsheet'
        version_id = '1'

        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})

        credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict=json.loads(response.payload.data.decode("UTF-8")), scopes=Sheets.SCOPES)
        # credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scopes=Sheets.SCOPES)

        http = httplib2.Http()
        http = credentials.authorize(http)

        self.service = build('sheets', 'v4', http=http)
        self.service_drive = build('drive', 'v3', http=http)
    
    def get_spreadsheet(self, spreadsheet_id, range):
        """
        Get the spreadsheet values
        :param spreadsheet_id: id of the spreadsheet
        :param range: range of the spreadsheet
        :return: values
        """
        result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range).execute()
        values = result.get('values', [])

        return values

    def update_spreadsheet(self, range_name, values, spreadsheet_id):
        """
        Update the spreadsheet values
        :param range_name: range of the spreadsheet
        :param values: values to be updated
        :param spreadsheet_id: id of the spreadsheet
        :return: None
        """
        batch_update_values_request_body = {
            "valueInputOption": "RAW",
            "data": [
                {
                "range": range_name,
                "values": [
                    [values]
                ],
                "majorDimension": "ROWS"
                }
            ]
            }

        request = self.service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_values_request_body)
        request.execute()

    def clear_spreadsheet(self, spreadsheet_id):
        sheet_name = 'Orders!A3:AM'
        request = self.service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range=sheet_name)
        response = request.execute()
        print(response)

    def add_empty_row(self, spreadsheet_id, sheet_id=0):
        batch_update_values_request_body = {'requests': {
            "appendDimension": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "length": 1
            }
        }}
        request = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_values_request_body)
        response = request.execute()
        print(response)

    def delete_rows(self, spreadsheet_id, start_row, end_row, sheet_id=0):
        batch_update_values_request_body = {'requests': {
            "deleteDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": start_row,
                    "endIndex": end_row
                }
            }
        }}
        request = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_values_request_body)
        response = request.execute()
        print(response)

    def update_orders_spreadsheet(self, df_values, sheet_name, spreadsheet_id):
        rows = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=f"{sheet_name}!A:A").execute().get('values', [])

        resource = {
            "majorDimension": "ROWS",
            "values": df_values if rows == [] else df_values[1:]
        }
        spreadsheetId = spreadsheet_id
        range = f"{sheet_name}!A:A"

        result = self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheetId,
            range=range,
            body=resource,
            valueInputOption="USER_ENTERED"
        ).execute()

        print(result)

    def add_sheet(self, spreadsheet_id, name):
        batch_update_values_request_body = {'requests': [{'addSheet':{'properties':{'title': name}}}]}

        request = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_values_request_body)

        try:
            response = request.execute()
            print(response)
            return response
        except Exception as e:
            print(str(e))
    
    def add_dropdowns(self, row_number, column, values, spreadsheet_id):
        values = [{"userEnteredValue": v} for v in values]
        payload = {
            "requests": [
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": row_number - 1,
                            "endRowIndex": row_number,
                            "startColumnIndex": column,
                            "endColumnIndex": column + 1
                        },
                        "rule": {
                            "condition": {
                                "type": 'ONE_OF_LIST',
                                "values": values
                            },
                            "showCustomUi": True,
                            "strict": False
                        }
                    }
                }
            ]
        }

        request = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=payload)
        response = request.execute()
    
    def remove_dropdowns(self, row_number, column, spreadsheet_id):
        payload = {
            "requests": [
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": row_number - 1,
                            "endRowIndex": row_number,
                            "startColumnIndex": column,
                            "endColumnIndex": column + 1
                        },
                        "rule": None,
                        "showCustomUi": True,
                        "strict": False
                    }
                }
            ]
        }

        request = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=payload)
        response = request.execute()
    
    def add_checkboxes(self, row_number, column, spreadsheet_id):
        payload = {
            "requests": [
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": row_number - 1,
                            "endRowIndex": row_number,
                            "startColumnIndex": column,
                            "endColumnIndex": column + 3
                        },
                        "rule": {
                            "condition": {
                                "type": 'BOOLEAN'
                            },
                            "showCustomUi": True,
                            "strict": False
                        }
                    }
                }
            ]
        }

        request = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=payload)
        response = request.execute()
    
    def add_checkboxes_true_(self, row_number, column, spreadsheet_id):
        payload = {
            "requests": [
                {
                    "setDataValidation": {
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": row_number - 1,
                            "endRowIndex": row_number,
                            "startColumnIndex": column,
                            "endColumnIndex": column + 1
                        },
                        "rule": {
                            "condition": {
                                "type": 'BOOLEAN',
                                "values": [],
                            },
                            "showCustomUi": True,
                            "strict": False
                        }
                    }
                }
            ]
        }

        request = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=payload)
        response = request.execute()

    def add_checkboxes_true(self, row_number, column, spreadsheet_id):
        gridRange = {
            "sheetId": 0,
            "startRowIndex": row_number - 1,
            "endRowIndex": row_number,
            "startColumnIndex": column,
            "endColumnIndex": column + 1
        }
        payload = {
            "requests": [
                {
                    "setDataValidation": {
                        "range": gridRange,
                        "rule": {
                            "condition": {
                                "type": 'BOOLEAN',
                                "values": [],
                            },
                            "showCustomUi": True,
                            "strict": False
                        }
                    }
                },
                {
                    "repeatCell": {
                        "range": gridRange,
                        "cell": {
                            "userEnteredValue": {
                                "boolValue": True
                            }
                        },
                        "fields": "userEnteredValue"
                    }
                }
            ]
        }

        request = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=payload)
        response = request.execute()

    def add_formula(self, first_row_number, last_row_number, startColumnIndex, endColumnIndex, formula, sheet_id='1VUZyqOdE1SSGzSB_uue_Tk5_ig8GXYiCqTCknXt92Uw'):
        payload =  {
            "requests": [
                {
                "repeatCell": {
                    "range": {
                    "startRowIndex": first_row_number - 1,
                    "endRowIndex": last_row_number,
                    "startColumnIndex": startColumnIndex,
                    "endColumnIndex": endColumnIndex
                    },
                    "cell": {
                    "userEnteredValue": {
                        "formulaValue": formula
                    }
                    },
                    "fields": "userEnteredValue"
                }
                }
            ]
        }

        request = self.service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=payload)
        response = request.execute()

    
    def hyperlink(self, row_number, link, spreadsheet_id):
        payload =  {
            "requests": [
                {
                "repeatCell": {
                    "range": {
                    "startRowIndex": row_number - 1,
                    "endRowIndex": row_number,
                    "startColumnIndex": 36,
                    "endColumnIndex": 37
                    },
                    "cell": {
                    "userEnteredValue": {
                        "formulaValue": f"""=HYPERLINK("{link}", "Get slip")"""
                    }
                    },
                    "fields": "userEnteredValue"
                }
                }
            ]
        }

        request = self.service.spreadsheets().batchUpdate(spreadsheetId='1VUZyqOdE1SSGzSB_uue_Tk5_ig8GXYiCqTCknXt92Uw', body=payload)
        response = request.execute()

    def send_batch_update(self, spreadsheet_id, requests):
        payload = {"requests": requests}
        request = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=payload)
        response = request.execute()

    def get_data_validation_request(self, start_row, end_row, column, rule):

        return {
            "setDataValidation": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": start_row,
                    "endRowIndex": end_row,
                    "startColumnIndex": column,
                    "endColumnIndex": column + 1
                },
                "rule": {
                    "condition": rule,
                    "showCustomUi": True,
                    "strict": False
                }
            }
        }


    def clear_data_validation(self, spreadsheet_id):

        payload = {
            "requests": [
                {
                    "setDataValidation": {

                    }
                }
            ]
        }

        request = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=payload)
        response = request.execute()
        # print(response)

    def add_column_number_formatting(self, start_row, end_row, column, number_format, spreadsheet_id):

        payload = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": start_row,
                            "endRowIndex": end_row,
                            "startColumnIndex": column,
                            "endColumnIndex": column + 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": number_format
                            }
                        },
                        "fields": "userEnteredFormat.numberFormat"
                    }
                }
            ]
        }

        request = self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=payload)
        response = request.execute()
        # print(response)

    def get_update_column_value_request(self, start_row, end_row, column, value):
        return {
            "repeatCell": {
                "range": {
                    "sheetId": 0,
                    "startRowIndex": start_row,
                    "endRowIndex": end_row,
                    "startColumnIndex": column,
                    "endColumnIndex": column + 1
                },
                "cell": {
                    "userEnteredValue": {
                        "stringValue": value
                    }
                },
                "fields": "userEnteredValue.stringValue"
            }
        }

    def get_spreadsheet_with_formulas(self, spreadsheet_id, range):
        result = self.service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,
                                                          range=range,
                                                          valueRenderOption='FORMULA').execute()
        values = result.get('values', [])

        return values
