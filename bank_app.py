import socket
import json
import threading
from datetime import datetime
import hashlib
from crypto_utils import generate_id

# In-memory "database" for registrations
merchants = {}  # key: merchant name, value: dict with details (mid, password, bank, ifsc_code, initial_balance)
users = {}      # key: username, value: dict with details (uid, mmid, password, bank, ifsc_code, mobile_number, upi_pin, initial_balance)

# ---------------------------
# Blockchain Classes
# ---------------------------
class Block:
    def _init_(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()
        
    def compute_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
class Blockchain:
    def _init_(self):
        self.chain = []
        self.create_genesis_block()
        
    def create_genesis_block(self):
        genesis_block = Block(0, str(datetime.now()), "Genesis Block", "0")
        self.chain.append(genesis_block)
        
    def add_block(self, data):
        previous_block = self.chain[-1]
        new_block = Block(len(self.chain), str(datetime.now()), data, previous_block.hash)
        self.chain.append(new_block)
        # Modified print statement to also display timestamp
        print(f"Block added: {new_block.index} at {new_block.timestamp} with data: {data}")
        return new_block

blockchain = Blockchain()

# ---------------------------
# Bank Server: Socket Setup
# ---------------------------
HOST = '0.0.0.0'
PORT = 9000

def handle_client(conn, addr):
    print(f"[Bank] Connected by {addr}")
    data = conn.recv(4096)
    if not data:
        conn.close()
        return
    try:
        request = json.loads(data.decode())
    except Exception as e:
        conn.sendall(json.dumps({"status": "error", "message": "Invalid JSON"}).encode())
        conn.close()
        return

    response = {}
    req_type = request.get("type")
    
    if req_type == "merchant_registration":
        name = request.get("name")
        password = request.get("password")
        initial_balance = request.get("initial_balance")
        ifsc_code = request.get("ifsc_code")
        bank = request.get("bank")  # New field for bank selection
        if name in merchants:
            response = {"status": "error", "message": "Merchant already registered. Please login."}
        else:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            mid_input = name + timestamp + password
            mid = generate_id(mid_input, 16)
            merchants[name] = {
                "mid": mid,
                "password": password,
                "bank": bank,
                "ifsc_code": ifsc_code,
                "initial_balance": initial_balance
            }
            data_block = {
                "type": "merchant_registration",
                "name": name,
                "bank": bank,
                "ifsc_code": ifsc_code,
                "initial_balance": initial_balance,
                "mid": mid
            }
            blockchain.add_block(data_block)
            response = {"status": "success", "mid": mid}
            
    elif req_type == "merchant_login":
        name = request.get("name")
        password = request.get("password")
        if name in merchants and merchants[name]["password"] == password:
            mid = merchants[name]["mid"]
            response = {"status": "success", "mid": mid}
        else:
            response = {"status": "error", "message": "Invalid merchant credentials"}
            
    elif req_type == "user_registration":
        username = request.get("username")
        password = request.get("password")
        mobile_number = request.get("mobile_number")
        upi_pin = request.get("upi_pin")
        initial_balance = request.get("initial_balance")
        bank = request.get("bank")
        ifsc_code = request.get("ifsc_code")
        if username in users:
            response = {"status": "error", "message": "User already registered. Please login."}
        else:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            uid_input = username + timestamp + password
            uid = generate_id(uid_input, 16)
            mmid_input = uid + mobile_number
            mmid = generate_id(mmid_input, 16)
            users[username] = {
                "uid": uid,
                "mmid": mmid,
                "password": password,
                "mobile_number": mobile_number,
                "upi_pin": upi_pin,
                "initial_balance": initial_balance,
                "bank": bank,
                "ifsc_code": ifsc_code
            }
            data_block = {
                "type": "user_registration",
                "username": username,
                "mobile_number": mobile_number,
                "initial_balance": initial_balance,
                "uid": uid,
                "mmid": mmid,
                "bank": bank,
                "ifsc_code": ifsc_code
            }
            blockchain.add_block(data_block)
            response = {"status": "success", "uid": uid, "mmid": mmid}
            
    elif req_type == "user_login":
        username = request.get("username")
        password = request.get("password")
        if username in users and users[username]["password"] == password:
            uid = users[username]["uid"]
            mmid = users[username]["mmid"]
            response = {"status": "success", "uid": uid, "mmid": mmid}
        else:
            response = {"status": "error", "message": "Invalid user credentials"}
            
    elif req_type == "transaction_request":
        # Transaction forwarded from UPI Machine
        merchant_id = request.get("merchant_id")
        user_details = request.get("user_details")  # Expecting dict: {mmid, amount, upi_pin}
        if merchant_id and user_details:
            mmid = user_details.get("mmid")
            amount_str = user_details.get("amount")
            upi_pin = user_details.get("upi_pin")
            try:
                amount = float(amount_str)
            except:
                response = {"status": "error", "message": "Invalid amount"}
                conn.sendall(json.dumps(response).encode())
                conn.close()
                return
            # Find user by mmid
            user_found = False
            for username, details in users.items():
                if details.get("mmid") == mmid:
                    user_found = True
                    # Verify UPI PIN
                    if details.get("upi_pin") != upi_pin:
                        response = {"status": "error", "message": "Invalid UPI PIN"}
                    else:
                        current_balance = float(details.get("initial_balance"))
                        if amount > current_balance:
                            response = {"status": "error", "message": "Insufficient balance"}
                        else:
                            # Update user's balance
                            details["initial_balance"] = str(current_balance - amount)
                            data_block = {
                                "type": "transaction",
                                "merchant_id": merchant_id,
                                "user_details": user_details
                            }
                            blockchain.add_block(data_block)
                            response = {"status": "approved", "message": "Transaction approved"}
                    break
            if not user_found:
                response = {"status": "error", "message": "User not found"}
        else:
            response = {"status": "error", "message": "Invalid transaction details"}
    
    elif req_type == "get_merchant_name":
        merchant_id = request.get("merchant_id")
        found = False
        for name, details in merchants.items():
            if details.get("mid") == merchant_id:
                response = {"status": "success", "merchant_name": name}
                found = True
                break
        if not found:
            response = {"status": "error", "message": "Merchant not found"}

    # NEW: Get all transactions
    elif req_type == "get_transactions":
        transactions = []
        for block in blockchain.chain:
            # Filter for blocks that were added as transactions
            if isinstance(block.data, dict) and block.data.get("type") == "transaction":
                transactions.append(block.data)
        response = {"status": "success", "transactions": transactions}
    
    else:
        response = {"status": "error", "message": "Unknown request type"}

    conn.sendall(json.dumps(response).encode())
    conn.close()

def start_bank_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"[Bank] Server listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()
    except KeyboardInterrupt:
        print("Shutting down Bank server")
    s.close()

if __name__ == "__main__":
    start_bank_server()