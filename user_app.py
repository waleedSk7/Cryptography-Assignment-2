# user_app.py
import socket
import json

BANK_HOST = "127.0.0.1"  # Adjust if Bank server is remote
BANK_PORT = 9000
UPI_HOST = "127.0.0.1"   # Adjust if UPI Machine is remote
UPI_PORT = 9001

def user_register():
    print("=== User Registration ===")
    username = input("Enter Username: ")
    password = input("Enter Password: ")
    mobile_number = input("Enter Mobile Number: ")
    upi_pin = input("Enter UPI PIN: ")
    initial_balance = input("Enter Initial Balance: ")
    try:
        float(initial_balance)
    except ValueError:
        print("Error: Initial balance must be a number")
        return None, None
    request = {
        "type": "user_registration",
        "username": username,
        "password": password,
        "mobile_number": mobile_number,
        "upi_pin": upi_pin,
        "initial_balance": initial_balance
    }
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((BANK_HOST, BANK_PORT))
    s.sendall(json.dumps(request).encode())
    response = s.recv(4096)
    s.close()
    response_data = json.loads(response.decode())
    if response_data.get("status") == "success":
        uid = response_data.get("uid")
        mmid = response_data.get("mmid")
        print("User registered successfully!")
        print("Your User ID (UID):", uid)
        print("Your Mobile Money Identifier (MMID):", mmid)
        return uid, mmid
    else:
        print("Registration failed:", response_data.get("message"))
        return None, None

def user_login():
    print("=== User Login ===")
    username = input("Enter Username: ")
    password = input("Enter Password: ")
    request = {
        "type": "user_login",
        "username": username,
        "password": password
    }
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((BANK_HOST, BANK_PORT))
    s.sendall(json.dumps(request).encode())
    response = s.recv(4096)
    s.close()
    response_data = json.loads(response.decode())
    if response_data.get("status") == "success":
        uid = response_data.get("uid")
        mmid = response_data.get("mmid")
        print("User login successful!")
        print("Your User ID (UID):", uid)
        print("Your Mobile Money Identifier (MMID):", mmid)
        return uid, mmid
    else:
        print("Login failed:", response_data.get("message"))
        return None, None

def initiate_transaction():
    print("\n=== Initiate Transaction ===")
    vmid = input("Enter the VMID from the scanned QR code: ")
    mmid = input("Enter your MMID: ")
    amount = input("Enter transaction amount: ")
    upi_pin = input("Enter your UPI PIN: ")
    user_details = {
        "mmid": mmid,
        "amount": amount,
        "upi_pin": upi_pin
    }
    request = {
        "type": "transaction_request",
        "vmid": vmid,
        "user_details": user_details
    }
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((UPI_HOST, UPI_PORT))
    s.sendall(json.dumps(request).encode())
    response = s.recv(4096)
    s.close()
    response_data = json.loads(response.decode())
    if response_data.get("status") == "approved":
        print("Transaction approved!")
    else:
        print("Transaction failed:", response_data.get("message"))

def main():
    print("=== User Application ===")
    choice = input("Do you want to (1) Register or (2) Login? Enter 1 or 2: ")
    if choice == "1":
        uid, mmid = user_register()
    elif choice == "2":
        uid, mmid = user_login()
    else:
        print("Invalid choice")
        return
    
    if uid:
        proceed = input("Do you want to initiate a transaction? (y/n): ")
        if proceed.lower() == 'y':
            initiate_transaction()

if __name__ == "__main__":
    main()
