# DHL-API Integration to Google Sheets Backend

These are some python classes to integrate DHL-API to Google Sheets Backend using Flask. The classes include
* DHL express API Class
* DHL Global Mail API Class
* Google Sheets API Class
* Google Sheet API Class for Development
* Google Drive API Class
* Google Drive API Class for Development

The scope of the project was to automatically get Rates from the DHL API and update the Google Sheet with the rates. After getting the rates, the user can select the rate and the shipment will be created in the DHL API. The shipment details will be updated in the Google Sheet. The label from the DHL API will be automatically uploaded to Google Drive. The link to the label will be updated in the Google Sheet.

The project was developed in Python 3.8.5 and the libraries used are listed in the requirements.txt file.

```
make setup
```
