import requests
import os
import utils


class DHL_GM():
    BASE_URL = os.environ.get('DHL_GM_BASE_URL') or 'https://api-sandbox.dhl.com/dpi'

    def __init__(self, auth_token=None):
        self.access_token = None
        self.auth_token = os.environ.get('DHL_GM_AUTH_TOKEN') if not auth_token else auth_token
        self.customer_ekp = os.environ.get('DHL_GM_CUSTOMER_EKP') or '336986890'

    def _get_headers(self, content_type='application/json'):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': content_type
        }
        return headers

    def get_access_token(self):
        headers = {
            'Authorization': f'Basic {self.auth_token}'
        }
        response = requests.get(f'{self.BASE_URL}/v1/auth/accesstoken', headers=headers)
        if response.status_code == 200:
            self.access_token = response.json().get("access_token")
        else:
            print("Failed to get access token")

    def create_order(self, customer_ekp=None):
        data = {
            "customerEkp": self.customer_ekp,
            "orderStatus": "OPEN",
            "items": []
        }
        print('Opening an order')
        headers = self._get_headers()
        resp = requests.post(f'{self.BASE_URL}/shipping/v1/orders', headers=headers, json=data)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            print(resp.content)
            raise Exception(resp.content)
        resp_json = resp.json()
        print('Created an open Order: ' + str(resp_json.get('orderId')))
        if resp_json.get('code') and resp_json.get('code') != '200':
            raise Exception(resp_json['message'])
        return resp_json.get('orderId')

    @staticmethod
    def _generate_order_item_data(order_item, product='GPT'):
        if not order_item.empty:
            if order_item['country'].iloc[0] == "GB":
                senderTaxId = "EORI: 370600428"
            elif order_item['country'].iloc[0] == "NO":
                senderTaxId = "EORI: 2021137"
            else:
                senderTaxId = "EORI: LT305576960"
            is_gift = (order_item['gift'] == 'TRUE').any()
            if is_gift:
                shipmentNaturetype = "GIFT"
            else:
                shipmentNaturetype = "SALE_GOODS"
            basic_info = {
                "product": product,
                "serviceLevel": "PRIORITY",
                "recipient": order_item['name'].iloc[0],
                "addressLine1": order_item['address'].iloc[0],
                "postalCode": order_item['postal_code'].iloc[0],
                "city": order_item['city'].iloc[0],
                "destinationCountry": order_item['country'].iloc[0],
                "recipientPhone": order_item['Phone number'].iloc[0],
                "recipientEmail": order_item['buyer_email'].iloc[0],
                "shipmentGrossWeight": order_item['Weight (kg)'].sum(),
                "shipmentAmount": int(order_item['total_items (EUR)'].iloc[0]),
                "shipmentCurrency": "EUR",
                "senderTaxId": senderTaxId,
                "shipmentNaturetype": shipmentNaturetype,
            }
            basic_info
            contents = []
            for index, content in order_item.iterrows():
                contents.append({
                    "contentPieceDescription": str(content['listing_name'][:33]),
                    "contentPieceValue": format(content['listing price (EUR)']*int(content['quantity']), '.2f'),
                    "contentPieceNetweight": float(content['Weight (kg)']),
                    "contentPieceOrigin": "LT",
                    "contentPieceAmount": int(content['quantity']),
                })

            item_info = basic_info.copy()
            item_info['contents'] = contents
            print(item_info)
        return [item_info]

    def add_order_item(self, order_id, item_content, is_eu_country=True, product='GPT'):
        print(f"Adding item to {order_id}")
        order_items_data = self._generate_order_item_data(item_content, product)
        headers = self._get_headers()
        response = requests.post(f'{self.BASE_URL}/shipping/v1/orders/{order_id}/items', headers=headers,
                                 json=order_items_data)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.content)
            raise Exception(response.content)
        response_json = response.json()
        print(f"Added {len(response_json)} items")
        print(response_json)
        return response_json

    def update_order_item(self, item_id, item_data):
        headers = self._get_headers()
        response = requests.put(f'{self.BASE_URL}/shipping/v1/items/{item_id}', headers=headers, json=item_data)
        return response.json()

    def get_item_label(self, item_id):
        print(f"Getting label for item {item_id}")
        headers = self._get_headers()
        response = requests.get(f'{self.BASE_URL}/shipping/v1/items/{item_id}/label', headers=headers)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.content)
            raise Exception(response.content)
        label = {"file_name": item_id, "file_data": response.content}
        return [label]

    def finalize_order(self, order_id):
        print(f"Finalizing order {order_id}")
        data = {
            "contactName": "Edita L",
            "awbCopyCount": 1,
            "telephoneNumber": "+37068409080"
        }
        headers = self._get_headers()
        response = requests.post(f'{self.BASE_URL}/shipping/v1/orders/{order_id}/finalization', headers=headers,
                                 json=data)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.content)
            raise Exception(response.content)
        return response.json()

    def get_order_info(self, order_id):
        headers = self._get_headers()
        response = requests.get(f'{self.BASE_URL}/shipping/v1/orders/{order_id}', headers=headers)
        return response.json()

    def get_item_info(self, item_id):
        headers = self._get_headers()
        response = requests.get(f'{self.BASE_URL}/shipping/v1/items/{item_id}', headers=headers)
        return response.json()

    def get_tracking_id(self, order_id):
        headers = self._get_headers()
        response = requests.get(f'{self.BASE_URL}/shipping/v1/orders/{order_id}/shipments', headers=headers)
        response_json = response.json()[0]
        awb = response_json.get('awb')
        return awb

    def get_awb_label(self, awb):
        print("Getting AWB labels")
        headers = self._get_headers()
        response = requests.get(f'{self.BASE_URL}/shipping/v1/shipments/{awb}/awblabels', headers=headers)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.content)
            raise Exception(response.content)
        return response.content

    @staticmethod
    def get_tracking_link(barcode):
        url = "https://webtrack.dhlecs.com/orders?trackingNumber="
        tracking_links = url+barcode
        return tracking_links

    def create_single_item(self, item_content, product='GPT'):
        print(f"Creating Single Item item")
        order_items_data = self._generate_order_item_data(item_content, product)[0]
        headers = self._get_headers()
        response = requests.post(f'{self.BASE_URL}/shipping/v1/customers/{self.customer_ekp}/items', headers=headers,
                                 json=order_items_data)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.content)
            raise Exception(response.content)
        response_json = response.json()
        print(f"Single item created")
        print(response_json)
        return response_json

    def get_label_for_item(self, barcode):
        print(f"Creating labels for {barcode}")
        headers = self._get_headers(content_type='application/pdf')
        response = requests.get(f'{self.BASE_URL}/shipping/v1/customers/{self.customer_ekp}/items/{barcode}/label', headers=headers)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.content)
            raise Exception(response.content)
        if response.content:
            print(f"Found label for {barcode}")
        return response.content

    def create_order_from_barcodes(self, item_barcodes):
        print(f"Creating order for {item_barcodes}")
        data = {
            "itemBarcodes": item_barcodes,
            "paperwork": {
                "contactName": "Edita L",
                "awbCopyCount": 1,
                "telephoneNumber": "+37068409080"
            }
        }
        print(data)
        headers = self._get_headers()
        response = requests.post(f'{self.BASE_URL}/shipping/v1/customers/{self.customer_ekp}/orders', headers=headers, json=data)
        message = False
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.content)
            message = response.content
        if response.json:
            print(f"Created Order.")
        return message, response.json()
