from flask import Flask, request, jsonify, render_template
import json
import os
from datetime import datetime
import pandas as pd
import random
import string
import sys
import shutil
import time

app = Flask(__name__)

# Lấy đường dẫn tuyệt đối của thư mục hiện tại
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Thư mục lưu trữ file Excel
EXCEL_FOLDER = os.path.join(CURRENT_DIR, 'orders')
EXCEL_FILE = os.path.join(EXCEL_FOLDER, 'orders.xlsx')
BACKUP_FILE = os.path.join(EXCEL_FOLDER, 'orders_backup.xlsx')
MENU_FILE = os.path.join(CURRENT_DIR, 'menu.xlsx')
SETTINGS_FILE = os.path.join(CURRENT_DIR, 'settings.json')

# Cài đặt mặc định
DEFAULT_SETTINGS = {
    "bankName": "vietinbank",
    "accountNo": ""
}

def load_settings():
    """Đọc cài đặt từ file JSON"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return DEFAULT_SETTINGS.copy()
    except Exception as e:
        print(f"Lỗi đọc file cài đặt: {e}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Lưu cài đặt vào file JSON"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Lỗi lưu file cài đặt: {e}")
        return False

def init_excel_file():
    """Khởi tạo file Excel nếu chưa tồn tại"""
    if not os.path.exists(EXCEL_FOLDER):
        try:
            os.makedirs(EXCEL_FOLDER, exist_ok=True)
            print(f"Đã tạo thư mục: {EXCEL_FOLDER}")
        except Exception as e:
            print(f"Lỗi tạo thư mục {EXCEL_FOLDER}: {e}")
            return False

    if not os.path.exists(EXCEL_FILE):
        try:
            # Tạo DataFrame với cấu trúc cột
            df = pd.DataFrame(columns=[
                'Order_ID', 
                'Dish_Number',  # Số thứ tự món
                'Size_Number',  # Số thứ tự size
                'Dish_Name',    # Tên món
                'Size_Name',    # Tên size
                'Quantity',     # Số lượng
                'Price',        # Giá tiền
                'Total',        # Tổng tiền món
                'Timestamp',    # Thời gian đặt hàng
                'QR_Code'       # Mã QR thanh toán
            ])
            # Lưu file Excel với engine openpyxl
            df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
            print(f"Đã tạo file Excel mới: {EXCEL_FILE}")
            return True
        except Exception as e:
            print(f"Lỗi tạo file Excel: {e}")
            return False
    return True

def backup_excel_file():
    """Tạo bản sao lưu của file Excel"""
    try:
        if os.path.exists(EXCEL_FILE):
            shutil.copy2(EXCEL_FILE, BACKUP_FILE)
            print(f"Đã tạo bản sao lưu: {BACKUP_FILE}")
            return True
    except Exception as e:
        print(f"Lỗi tạo bản sao lưu: {e}")
    return False

def read_excel_file():
    """Đọc file Excel và trả về DataFrame"""
    try:
        if os.path.exists(EXCEL_FILE):
            # Đọc file Excel với engine openpyxl
            df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
            # Chuyển đổi các cột số thành kiểu dữ liệu Python thông thường
            numeric_columns = ['Dish_Number', 'Size_Number', 'Quantity', 'Price', 'Total']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].astype(float)
            return df
        return pd.DataFrame(columns=[
            'Order_ID', 
            'Dish_Number',
            'Size_Number',
            'Dish_Name',
            'Size_Name',
            'Quantity',
            'Price',
            'Total',
            'Timestamp',
            'QR_Code'
        ])
    except Exception as e:
        print(f"Loi doc file Excel: {e}")
        return None

def save_excel_file(df):
    """Lưu DataFrame vào file Excel"""
    try:
        # Tạo bản sao lưu trước khi lưu
        backup_excel_file()
        # Chuyển đổi các cột số thành kiểu dữ liệu Python thông thường
        numeric_columns = ['Dish_Number', 'Size_Number', 'Quantity', 'Price', 'Total']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].astype(float)
        # Lưu file Excel với engine openpyxl
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        print(f"Da luu file Excel thanh cong")
        return True
    except Exception as e:
        print(f"Loi luu file Excel: {e}")
        return False

def init_menu_file():
    """Khởi tạo file menu Excel nếu chưa tồn tại"""
    if not os.path.exists(MENU_FILE):
        try:
            # Tạo DataFrame với dữ liệu mẫu
            data = {
                'ID': [1, 2, 3, 4, 5, 6],
                'Dish': ['Cà phê đen', 'Cà phê đen', 'Cà phê đen', 
                        'Cà phê sữa', 'Cà phê sữa', 'Cà phê sữa'],
                'Size': ['S', 'M', 'L', 'S', 'M', 'L'],
                'Price': [25000, 30000, 35000, 30000, 35000, 40000]
            }
            df = pd.DataFrame(data)
            
            # Lưu file Excel với engine openpyxl
            df.to_excel(MENU_FILE, index=False, engine='openpyxl')
            print(f"Đã tạo file menu Excel mới: {MENU_FILE}")
            return True
        except Exception as e:
            print(f"Lỗi tạo file menu Excel: {e}")
            return False
    return True

def read_menu():
    """Đọc file menu Excel và trả về DataFrame"""
    try:
        if os.path.exists(MENU_FILE):
            # Đọc file Excel với engine openpyxl
            df = pd.read_excel(MENU_FILE, engine='openpyxl')
            # Chuyển đổi các cột số thành kiểu dữ liệu Python thông thường
            df['ID'] = df['ID'].astype(int)
            df['Price'] = df['Price'].astype(float)
            return df
        else:
            # Nếu file không tồn tại, tạo file mới
            if init_menu_file():
                df = pd.read_excel(MENU_FILE, engine='openpyxl')
                df['ID'] = df['ID'].astype(int)
                df['Price'] = df['Price'].astype(float)
                return df
            return pd.DataFrame(columns=['ID', 'Dish', 'Size', 'Price'])
    except Exception as e:
        print(f"Loi doc file menu Excel: {e}")
        # Nếu có lỗi, thử tạo lại file
        if init_menu_file():
            try:
                df = pd.read_excel(MENU_FILE, engine='openpyxl')
                df['ID'] = df['ID'].astype(int)
                df['Price'] = df['Price'].astype(float)
                return df
            except:
                pass
        return None

def save_menu(df):
    """Lưu DataFrame menu vào file Excel"""
    try:
        # Lưu file Excel với engine openpyxl
        df.to_excel(MENU_FILE, index=False, engine='openpyxl')
        print(f"Đã lưu file menu Excel thành công")
        return True
    except Exception as e:
        print(f"Lỗi lưu file menu Excel: {e}")
        return False

# Khởi tạo file Excel khi khởi động server
if not init_excel_file():
    print("Không thể khởi tạo file Excel. Vui lòng kiểm tra quyền truy cập.")
    sys.exit(1)

# Khởi tạo file menu khi khởi động server
if not init_menu_file():
    print("Không thể khởi tạo file menu Excel. Vui lòng kiểm tra quyền truy cập.")
    sys.exit(1)

# Hàm tạo mã đơn hàng ngẫu nhiên
def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

def tinh_crc16_ccitt(data: bytes) -> str:
    """Tính CRC16-CCITT cho chuỗi QR"""
    crc = 0xFFFF
    poly = 0x1021

    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFF
    
    return f"{crc:04X}"

def tao_vietqr(ten_ngan_hang: str, so_tai_khoan: str, so_tien=None):
    """Tạo chuỗi QR VietQR"""
    # Dictionary chứa mã ngân hàng
    ma_ngan_hang_dict = {
        "saigonbank":"970400","scb":"970400","sacombank":"970403","agribank":"970405",
        "dongabank":"970406","techcombank":"970407","tcb":"970407","gpbank":"970408",
        "bacabank":"970409","standardchartered":"970410","pvcombank":"970412",
        "oceanbank":"970414","bidv":"970415","acb":"970416","vietbank":"970418",
        "ncb":"970419","vrb":"970421","mbbank":"970422","mb":"970422",
        "vietinbank":"970423","tpbank":"970423","shinhanbank":"970424",
        "abbank":"970425","maritimebank":"970426","msb":"970426","vietabank":"970427",
        "namabank":"970428","sgb":"970429","pgbank":"970430","eximbank":"970431",
        "vpbank":"970432","vietcombank":"970436","hdbank":"970437","baovietbank":"970438",
        "publicbank":"970439","seabank":"970440","vib":"970441","hongleong":"970442",
        "shb":"970443","cbbank":"970444","coopbank":"970446","ocb":"970448",
        "lienvietpostbank":"970449","lpb":"970449","kienlongbank":"970452",
        "vietcapitalbank":"970454","ibk":"970455","ibk2":"970456","wooribank":"970457",
        "uob":"970458","cimb":"970459","fccom":"970460","kookmin1":"970462",
        "kookmin2":"970463","cdc":"970464","sinopac":"970465","kebhana1":"970466",
        "kebhana2":"970467","mirae":"970468","mbshinsei":"970470"
    }

    # Lấy mã ngân hàng từ tên ngân hàng
    ma_ngan_hang = ma_ngan_hang_dict.get(ten_ngan_hang.lower().replace(" ","").replace("-",""))
    if not ma_ngan_hang:
        return f"Lỗi: Không tìm thấy ngân hàng '{ten_ngan_hang}'"

    def add_field(tag: str, value: str) -> str:
        return f"{tag}{len(value):02d}{value}"

    # Khởi tạo chuỗi QR
    qr_data = ""
    
    # Thêm các trường cơ bản
    qr_data += add_field("00", "01")  # ID 00 - Phiên bản
    qr_data += add_field("01", "11")  # ID 01 - Định dạng QR

    # Tạo thông tin tài khoản người bán (Tag 38)
    sub_tag_01 = add_field("00", ma_ngan_hang) + add_field("01", so_tai_khoan)
    
    merchant_account = add_field("00", "A000000727")  # NAPAS ID
    merchant_account += add_field("01", sub_tag_01)
    merchant_account += add_field("02", "QRIBFTTA")
    
    qr_data += add_field("38", merchant_account)

    # Thêm các trường khác
    qr_data += add_field("53", "704")  # Đơn vị tiền tệ VND

    if so_tien:
        so_tien_str = str(int(float(so_tien)))
        qr_data += add_field("54", so_tien_str)  # Số tiền

    qr_data += add_field("58", "VN")  # Quốc gia

    # Thêm CRC
    qr_data += "6304"  # Chừa chỗ cho CRC
    crc_value = tinh_crc16_ccitt(qr_data.encode('ascii'))
    qr_data += crc_value

    return qr_data

def generate_vietqr_string(account_no, account_name, acq_id, amount):
    """Tạo chuỗi QR VietQR"""
    try:
        # Lấy cài đặt ngân hàng
        settings = load_settings()
        bank_name = settings.get('bankName')
        
        if not bank_name:
            print("Lỗi: Chưa cấu hình ngân hàng")
            return None
        
        # Tạo chuỗi QR
        qr_string = tao_vietqr(
            ten_ngan_hang=bank_name,
            so_tai_khoan=settings.get('accountNo'),
            so_tien=amount
        )
        
        if qr_string and not qr_string.startswith("Lỗi"):
            print(f"Tạo mã QR thành công cho ngân hàng {bank_name}")
            return qr_string
        else:
            print(f"Lỗi tạo mã QR: {qr_string}")
            return None
            
    except Exception as e:
        print(f"Lỗi khi tạo mã QR: {e}")
        return None

@app.route('/order', methods=['POST'])
def receive_order():
    try:
        data = request.get_json()
        print("\n=== Thong tin nhan don hang ===")
        print("Data:", data)
        
        # Kiểm tra dữ liệu đầu vào
        if not data or 'items' not in data:
            print("Loi: Khong co du lieu hoac thieu truong 'items'")
            return jsonify({
                'status': 'error',
                'message': 'Dữ liệu không hợp lệ: thiếu trường items'
            }), 400
            
        if not isinstance(data['items'], list):
            print("Loi: Truong 'items' khong phai la list")
            return jsonify({
                'status': 'error',
                'message': 'Dữ liệu không hợp lệ: items phải là một mảng'
            }), 400
            
        # Tạo mã đơn hàng tự động
        order_id = generate_order_id()
        print(f"\nMã đơn hàng tự động: {order_id}")
        
        # Đọc file Excel hiện tại
        df = read_excel_file()
        if df is None:
            print("Loi: Khong the doc file Excel")
            return jsonify({'status': 'error', 'message': 'Không thể đọc file Excel'}), 500

        # Đọc menu để lấy giá
        menu_df = read_menu()
        if menu_df is None:
            print("Loi: Khong the doc file menu")
            return jsonify({'status': 'error', 'message': 'Không thể đọc file menu'}), 500

        # Tính tổng tiền đơn hàng dựa trên số thứ tự món và size
        total_amount = 0.0
        order_details = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for item in data['items']:
            print(f"\nXu ly mon: {item}")
            
            # Kiểm tra dữ liệu món
            if not all(k in item for k in ['dish', 'size', 'quantity']):
                print(f"Loi: Thieu thong tin mon - {item}")
                return jsonify({
                    'status': 'error',
                    'message': f'Thiếu thông tin món: {item}'
                }), 400
                
            try:
                dish_number = int(item.get('dish'))  # Số thứ tự món (1-9)
                size_number = int(item.get('size'))  # Size (1-3)
                quantity = int(item.get('quantity', 1))
            except ValueError as e:
                print(f"Loi: Khong the chuyen doi so - {e}")
                return jsonify({
                    'status': 'error',
                    'message': f'Dữ liệu số không hợp lệ: {e}'
                }), 400
            
            print(f"Tim mon: ID={dish_number}, Size={size_number}")
            
            # Tìm món trong menu dựa trên số thứ tự và size
            menu_item = menu_df[(menu_df['ID'] == dish_number) & (menu_df['Size'] == size_number)]
            if menu_item.empty:
                print(f"Loi: Khong tim thay mon ID={dish_number}, Size={size_number}")
                return jsonify({
                    'status': 'error', 
                    'message': f'Không tìm thấy món số {dish_number} size {size_number} trong menu'
                }), 400
            
            dish_name = menu_item.iloc[0]['Dish']
            size_name = menu_item.iloc[0]['Size']
            price = float(menu_item.iloc[0]['Price'])
            
            print(f"Tim thay mon: {dish_name}, Size={size_name}, Gia={price}")
            
            # Tính tiền cho món này
            item_total = price * quantity
            total_amount += item_total
            
            # Lưu chi tiết món
            order_details.append({
                'dish_number': int(dish_number),
                'size_number': int(size_number),
                'dish_name': str(dish_name),
                'size_name': str(size_name),
                'quantity': int(quantity),
                'price': float(price),
                'total': float(item_total)
            })

        print(f"\nTong tien don hang: {total_amount:,} VNĐ")

        # Tạo chuỗi QR VietQR
        vietqr_string = generate_vietqr_string(
            account_no="44040505906",
            account_name="NGUYEN THANH SON",
            acq_id=970423,
            amount=int(total_amount),
        )
        
        # Kiểm tra nếu không tạo được QR code
        if not vietqr_string:
            print("Loi: Khong the tao ma QR")
            return jsonify({
                'status': 'error',
                'message': 'Không thể tạo mã QR thanh toán'
            }), 500

        # Thêm các món vào DataFrame
        for detail in order_details:
            order_info = {
                'Order_ID': order_id,
                'Dish_Number': detail['dish_number'],
                'Size_Number': detail['size_number'],
                'Dish_Name': detail['dish_name'],
                'Size_Name': detail['size_name'],
                'Quantity': detail['quantity'],
                'Price': detail['price'],
                'Total': detail['total'],
                'Timestamp': timestamp,
                'QR_Code': vietqr_string
            }
            df = pd.concat([df, pd.DataFrame([order_info])], ignore_index=True)

        # Lưu lại vào file Excel
        if not save_excel_file(df):
            print("Loi: Khong the luu file Excel")
            return jsonify({'status': 'error', 'message': 'Không thể lưu đơn hàng vào file Excel'}), 500

        print(f"\n=== Thong tin don hang ===")
        print(f"Mã đơn hàng: {order_id}")
        print(f"Tổng tiền: {total_amount:,} VNĐ")
        print(f"Mã QR: {vietqr_string}")
        print("Chi tiết đơn hàng:")
        for detail in order_details:
            print(f"- Món {detail['dish_name']}, Size {detail['size_name']}, "
                  f"Số lượng {detail['quantity']}, Giá {detail['price']:,} VNĐ, "
                  f"Tổng: {detail['total']:,} VNĐ")
        print("========================")

        response = {
            'status': 'success',
            'message': 'Đơn hàng đã được nhận',
            'order_id': order_id,
            'total_amount': total_amount,
            'qr_code': vietqr_string,
            'order_details': order_details
        }
        return jsonify(response)
    except Exception as e:
        print("\n=== Loi khong xac dinh ===")
        print("Error:", str(e))
        print("=========================")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/orders', methods=['GET'])
def get_orders():
    try:
        df = pd.read_excel(EXCEL_FILE)
        return jsonify(df.to_dict('records'))
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/menu', methods=['GET'])
def get_menu():
    """Lấy toàn bộ menu"""
    try:
        df = read_menu()
        if df is None:
            return jsonify({'status': 'error', 'message': 'Không thể đọc file menu'}), 500
        return jsonify(df.to_dict('records'))
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/settings/bank', methods=['GET', 'POST'])
def bank_settings():
    """Quản lý cài đặt thông tin ngân hàng"""
    if request.method == 'GET':
        settings = load_settings()
        return jsonify({
            'status': 'success',
            'bankName': settings.get('bankName', ''),
            'accountNo': settings.get('accountNo', '')
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'Không có dữ liệu được gửi'
                }), 400

            # Kiểm tra dữ liệu
            required_fields = ['bankName', 'accountNo']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({
                        'status': 'error',
                        'message': f'Thiếu thông tin {field}'
                    }), 400

            # Lưu cài đặt
            settings = {
                'bankName': data['bankName'],
                'accountNo': data['accountNo']
            }
            
            if save_settings(settings):
                return jsonify({
                    'status': 'success',
                    'message': 'Lưu cài đặt thành công'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Không thể lưu cài đặt'
                }), 500

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

@app.route('/settings', methods=['GET'])
def settings_page():
    """Trang cài đặt"""
    return render_template('settings.html')

if __name__ == '__main__':
    print("Server đang chạy tại http://localhost:5000")
    print("Chờ đơn hàng từ ESP32...")
    app.run(host='0.0.0.0', port=5000) 