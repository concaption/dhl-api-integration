import requests
import base64
import os
import pandas as pd
from pprint import pprint

class Dhl:
    BASE_URL = "https://express.api.dhl.com/mydhlapi/test/"

    def __init__(self, username=None, password=None):
        self.username = os.environ.get('DHL_EXPRESS_USERNAME') if not username else username
        self.password = os.environ.get('DHL_EXPRESS_PASSWORD') if not password else password

    def getOffers(self, order, totalWeight=None, totalPrice=0.0):
        if not (totalWeight):
            pkg_weight = float(order['Weight (kg)']) if order['Weight (kg)'] != "" else 0.0
        else:
            pkg_weight = float(totalWeight)

        if not (totalPrice):
            totalPrice = float(order['listing price (EUR)']) if order['listing price (EUR)'] != "" else 0.0

        today = pd.Timestamp.now().normalize()
        next_bday = today + pd.tseries.offsets.BDay()
        next_bday = next_bday.date()
        params = {
            "accountNumber": "336986890",
            "originCountryCode": "LT",
            "originCityName": "Vilnius",
            "destinationCountryCode": order['country'],
            "destinationPostalCode": order["postal_code"],
            "destinationCityName": order["city"],
            "weight": pkg_weight,
            "length": order["L (cm)"],
            "width": order["W (cm)"],
            "height": order["W (cm)"],
            "plannedShippingDate": next_bday,
            "isCustomsDeclarable": "false",
            "unitOfMeasurement": "metric"
        }
        print("DHl Params:: ", params)
        # Convert the username and password to a base64 encoded string for basic authentication
        credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()

        headers = {
            "Authorization": f"Basic {credentials}",
        }
        print(self.BASE_URL + "rates")
        response = requests.get(self.BASE_URL + "rates", headers=headers, params=params)
        if response.status_code == 200:
            ret_data = response.json()
            print("DHL responses::", ret_data)
            return ret_data.get('products', [])  # Assuming the API responds with JSON. Otherwise, use response.text
        print("Failed to get quote.", str(response.content))
        raise Exception("Failed to get quote. error: %s" % str(response.content))

    def formatOffers(self, offers):
        formatted_offers = []
        for offer in offers:
            productName = offer.get('productName')
            productCode = offer.get('productCode')
            localProductCode = offer.get('localProductCode')
            localProductCountryCode = offer.get('localProductCountryCode')
            networkTypeCode = offer.get('networkTypeCode')
            isCustomerAgreement = offer.get('isCustomerAgreement')
            totalPrice = float(offer.get('totalPrice')[0].get('price'))
            isMarketingService = offer.get('isMarketingService')

            # Create a string representation of the offer
            offer_string = f"DHL - {totalPrice} - {productName} - {productCode} ({localProductCode})"

            # Add additional information to the string representation
            if isCustomerAgreement:
                offer_string += " (Customer Agreement)"
            elif isMarketingService:
                offer_string += " (Marketed Service)"
            formatted_offers.append(offer_string)
            print("succefully formatted DHL")
        # hardcoded services
        formatted_offers.append("DHL - DHL Global Mail - Packet Tracked - GPT (GPT)")
        formatted_offers.append("DHL - DHL Global Mail - Packet Plus - GPP (GPP)")
        return formatted_offers

    def book_courier(self, weight):
        today = pd.Timestamp.now().normalize()
        next_bday = today + pd.tseries.offsets.BDay()
        next_bday_utc = next_bday.tz_localize('UTC')
        next_bday = next_bday_utc.strftime('%Y-%m-%dT%H:%M:%S') + "GMT+01:00"
        payload = {
            "plannedPickupDateAndTime": next_bday,
            "accounts": [{
                "typeCode": "shipper",
                "number": "336986890"}],
            "specialInstructions": [{
                "value": "Outside door code 1752#"}],
            "customerDetails": {
                "shipperDetails": {
                    "postalAddress": {
                        "postalCode": "03202",
                        "cityName": "Vilnius",
                        "countryCode": "LT",
                        "addressLine1": "Smolensko 1"},
                    "contactInformation": {
                        "email": "info@linencouture.com",
                        "phone": "+37068409080",
                        "fullName": "Edita L",
                        "companyName": "Linen Couture"}},
                "pickupDetails": {
                    "postalAddress": {
                        "postalCode": "03202",
                        "cityName": "Vilnius",
                        "countryCode": "LT",
                        "addressLine1": "Smolensko 1"},
                    "contactInformation": {
                        "email": "info@linencouture.com",
                        "phone": "+37068409080",
                        "fullName": "Edita L",
                        "companyName": "Linen Couture"}}
            },
            "shipmentDetails": [{
                "productCode": "U",
                "isCustomsDeclarable": False,
                "unitOfMeasurement": "metric",
                "accounts": [{
                    "typeCode": "shipper",
                    "number": "336986890"}],
                "packages": [{
                    "weight": weight,
                    "dimensions": {
                        "length": 40,
                        "width": 35,
                        "height": 10}}]
            }]
        }
        print("Doing booking for params below")
        pprint(payload)
        credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()

        headers = {
            "Authorization": f"Basic {credentials}",
        }
        response = requests.post(self.BASE_URL + "pickups", headers=headers, json=payload)
        ret_data = response.json()
        pprint(ret_data)
        return ret_data