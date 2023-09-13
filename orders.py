from dhl.dhldpi import DHLDPI

def generate_dhl_order():
    """
    Generate DHL order
    :return:
    """
    sheet_id = "Your sheet id"
    sheets = Sheets()
    dhl_client = DHLDPI()
    print("Getting Orders data from sheet")
    orders = sheets.get_spreadsheet(sheet_id, range='A2:AI')
    print("orders")
    df = pd.DataFrame(orders)
    df = df.rename(columns=df.iloc[0]).drop(df.index[0])
    df['Weight (kg)'] = df['Weight (kg)'].apply(utils.convert_weight) * 1000
    df['listing price (EUR)'] = df['listing price (EUR)'].apply(utils.convert_listing_price).astype(int)
    df['total_items (EUR)'] = df['total_items (EUR)'].apply(utils.convert_listing_price).astype(int)
    order_rows = df[(df['Carrier'] == "DHL Global Mail") & (df['Create Shipment'] == "TRUE") & (df['Validation'] == "FALSE")]
    if not order_rows.empty:
        print("Loaded Data for orders")
    else:
        print("No order rows found for the dataframe below")
        print(df)
    dhl_client.get_access_token()
    order_id = dhl_client.create_order()
    item_ids = []
    item_barcodes = []
    for idx, item in order_rows.iterrows():
        row_number = idx + 2
        print(f"Item in row number: {row_number}:")
        try:
            sheets.update_spreadsheet(f'Orders!AN{row_number}', "", sheet_id)
            item_content = df[df["order_id"] == item['order_id']]
            service = "GPT" if "GPT" in item['Suggested Shipment Type'] else "GPP"
            print(f"Service type is {service}")
            dhl_client.get_access_token()
            item_details = dhl_client.add_order_item(order_id, item_content, utils.is_eu_country(item['country'], sheets), product=service)
            item_id = item_details[0].get('id')
            item_ids.append(item_id)
            item_barcode = item_details[0].get('barcode')
            item_barcodes.append(item_barcode)
            label = dhl_client.get_item_label(item_id)
            if label:
                _upload_label_info(label, item_barcode, row_number, sheets,
                                   sheet_id, order_id, carrier="DHL")
            if item_barcode:
                print(f"Tracking number {item_barcode}")
                tracking_link = dhl_client.get_tracking_link(item_barcode)
                _update_order_info(item_barcode, row_number, sheets, sheet_id, tracking_link)
                _update_carrier_name(item, row_number, sheets, sheet_id)
            else:
                sheets.update_spreadsheet(f'Orders!AN{row_number}', f'Order ID:Item ID:{order_id}:{item_id}', sheet_id)
        except Exception as e:
            print(traceback.format_exc())
            sheets.update_spreadsheet(f'Orders!AN{row_number}', str(e), sheet_id)
    try:
        finalized_items = dhl_client.finalize_order(order_id)
    except Exception as e:
        print(traceback.format_exc())
        if not item_ids:
            for idx, item in order_rows.iterrows():
                row_number = idx + 2
                sheets.update_spreadsheet(f'Orders!AN{row_number}', str(e), sheet_id)
    if item_ids:
        print(f"Order placed with order id: {order_id}")
        print(f"Items: {item_ids}")
        print(f"Barcodes: {item_barcodes}")


def add_items_dhl():
    """
    Add items to DHL order
    :return:
    """
    sheet_id = "1Your sheet id"
    sheets = Sheets()
    drive = Drive()
    dhl_client = DHLDPI(auth_token="SUFPNjFNT3VaRWhmdTY4YU1EWVhTR0cwd3ZkWWZEWmU6QlRuUnJCR0c1M0VGN0QwVQ==")
    print("Getting Orders data from sheet")
    orders = sheets.get_spreadsheet(sheet_id, range='A2:AI')
    print("orders")
    df = pd.DataFrame(orders)
    df = df.rename(columns=df.iloc[0]).drop(df.index[0])
    df['Weight (kg)'] = df['Weight (kg)'].apply(utils.convert_weight) * 1000
    df['listing price (EUR)'] = df['listing price (EUR)'].apply(utils.convert_listing_price).astype(float)
    df['total_items (EUR)'] = df['total_items (EUR)'].apply(utils.convert_listing_price).astype(float)
    item_rows = df[
        (df['Carrier'] == "DHL Global Mail") & (df['Create Shipment'] == "TRUE") & (df['Validation'] == "FALSE")]
    if not item_rows.empty:
        print("Loaded Data for items")
    else:
        print(df)
        print("No item rows found for the dataframe below")
        return
    dhl_client.get_access_token()
    item_ids = []
    item_barcodes = []
    for idx, item in item_rows.iterrows():
        row_number = idx + 2
        print(f"Item in row number: {row_number}")
        try:
            sheets.update_spreadsheet(f'Orders!AN{row_number}', "", sheet_id)
            item_content = df[df['order_id'] == item['order_id']]
            service = "GPT" if "GPT" in item['Suggested Shipment Type'] else "GPP"
            print(f"Service type is {service}")
            dhl_client.get_access_token()
            item_details = dhl_client.create_single_item(item_content, product=service)
            item_barcode = item_details.get('barcode')
            item_id = item_details.get('id')
            if item_barcode:
                item_barcodes.append(item_barcode)
                sheets.update_spreadsheet(f'Orders!AK{row_number}', item_barcode, sheet_id)
                tracking_link = dhl_client.get_tracking_link(item_barcode)
                _update_order_info(item_barcode, row_number, sheets, sheet_id, tracking_link)
                _update_carrier_name(item, row_number, sheets, sheet_id)
                label = dhl_client.get_label_for_item(item_barcode)
                if label:
                    print(f"Adding labels for {item_barcode}")
                    label_filename = f"DHL_{item_barcode}_{datetime.datetime.now().strftime('%Y-%m-%d')}"
                    file_id = drive.upload_shipping_label(label,label_filename)
                if not file_id:
                    sheets.update_spreadsheet(f'Orders!AN{row_number}',
                                              f"Label not found. ID:Barcode:{item_id}:{item_barcode}",
                                              sheet_id)
                else:
                    sheets.add_formula(row_number, row_number, 37, 38,
                                       f"""=HYPERLINK("https://drive.google.com/file/d/{file_id}", "Get slip")""",
                                       sheet_id=sheet_id)
                    print("Shipping label uploaded successfully to Google Drive folder.")
            else:
                print(f"Barcode not found for {row_number}")
                sheets.update_spreadsheet(f'Orders!AK{row_number}', "Not Found", sheet_id)
            if item_id:
                item_ids.append(item_id)
            else:
                print("Item id not found")
        except Exception as e:
            print(traceback.format_exc())
            sheets.update_spreadsheet(f'Orders!AN{row_number}', str(e), sheet_id)
    print(f"Item IDs: {item_ids}")
    print(f"Barcode: {item_barcodes}")


def create_dhl_order():
    sheet_id = "Your sheet id"
    sheets = Sheets()
    drive = Drive()
    dhl_client = DHLDPI()
    print("Getting Orders data from sheet")
    orders = sheets.get_spreadsheet(sheet_id, range='A2:AK')
    print("orders")
    df = pd.DataFrame(orders)
    df = df.rename(columns=df.iloc[0]).drop(df.index[0])
    print(df)
    item_rows = df[(df['Carrier'] == "DHL Global Mail") & (df['Create Shipment'] == "TRUE") & (df['Validation'] == "TRUE") & (df['Tracking ID'].notnull()) & (df["Registered Store"] == "FALSE")]
    if not item_rows.empty:
        print("Loaded Data for items")
    else:
        print(df)
        print("No item rows found for the dataframe below")
        return
    dhl_client.get_access_token()
    chunk_size = 5
    num_rows = len(item_rows)
    for start in range(0, num_rows, chunk_size):
        end = start + chunk_size
        order_items = item_rows[start:end]
        row_numbers = order_items.index.to_list()
        row_numbers = [x+2 for x in row_numbers]
        try:
            item_barcodes = order_items['Tracking ID'].tolist()
            message, order = dhl_client.create_order_from_barcodes(item_barcodes)
            if message:
                raise Exception(message)
            awb = order.get("shipments")[0].get("awb")
            label = dhl_client.get_awb_label(awb)
            file_id = None
            if label:
                print(f"Adding label for {awb}")
                label_filename = f"DHL_{awb}_{datetime.datetime.now().strftime('%Y-%m-%d')}"
                file_id = drive.upload_shipping_label(label, label_filename)
                print(f"Shipping label uploaded successfully to Google Drive folder for {file_id}")
            if not file_id:
                for row_number in row_numbers:
                    sheets.update_spreadsheet(f'Orders!AN{row_number}',
                                          f"Label not found. AWB:{awb}",
                                          sheet_id)
            else:
                for row_number in row_numbers:
                    sheets.add_formula(row_number, row_number, 39, 40,
                                   f"""=HYPERLINK("https://drive.google.com/file/d/{file_id}", "AWB")""",
                                   sheet_id=sheet_id)
                print(f"Shipping label hyperlinked")
        except Exception as e:
            print(traceback.format_exc())
            for row_number in row_numbers:
                sheets.update_spreadsheet(f'Orders!AN{row_number}', str(e), sheet_id)


def book_courier():
    sheet_id = "Your sheet id"
    sheets = Sheets()
    drive = Drive()
    dhl_client = Dhl()
    print("Getting Orders data from sheet")
    orders = sheets.get_spreadsheet(sheet_id, range='A2:AK')
    print("orders")
    df = pd.DataFrame(orders)
    df = df.rename(columns=df.iloc[0]).drop(df.index[0])
    df['Weight (kg)'] = df['Weight (kg)'].apply(utils.convert_weight)
    order_rows = df[
        (df['Carrier'] == "DHL Global Mail") & (df['Create Shipment'] == "TRUE") & (df['Validation'] == "TRUE") & (
            df['Tracking ID'].notnull()) & (df["Registered Store"] == "FALSE")]
    if not order_rows.empty:
        print("Loaded Data for items")
    else:
        print(df)
        print("No item rows found for the dataframe below")
        return
    weight = 0.00
    for idx, item in order_rows.iterrows():
        item_content = df[df["order_id"] == item['order_id']]
        weight = weight + item_content['Weight (kg)'].sum()
    weight = float(format(weight, '.2f'))
    dhl_client.book_courier(weight)
    print("Booked courier.")
    return True