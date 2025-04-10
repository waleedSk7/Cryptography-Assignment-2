# merchant_app.py
import socket
import json

BANK_HOST = "127.0.0.1"  # Update if Bank server is on a different machine
BANK_PORT = 9000

def register_merchant():
    print("=== Merchant Registration ===")
    name = input("Enter Merchant Name: ")
    password = input("Enter Password: ")
    initial_balance = input("Enter Initial Balance: ")
    ifsc_code = input("Enter IFSC Code: ")

    # Create a registration request in JSON format
    request = {
        "type": "merchant_registration",
        "name": name,
        "password": password,
        "initial_balance": initial_balance,
        "ifsc_code": ifsc_code
    }

    # Establish a socket connection to the Bank server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((BANK_HOST, BANK_PORT))
    s.sendall(json.dumps(request).encode())

    # Receive and process the Bank server's response
    response = s.recv(4096)
    s.close()
    response_data = json.loads(response.decode())
    
    if response_data.get("status") == "success":
        mid = response_data.get("mid")
        print("Merchant registered successfully!")
        print("Your Merchant ID (MID):", mid)
        return mid
    else:
        print("Registration failed:", response_data.get("message"))
        return None

def main():
    mid = register_merchant()
    if mid:
        # Merchant is now registered; further functionality such as login or QR code generation can be added here.
        print("You are now registered with MID:", mid)
    else:
        print("Merchant registration was not successful.")

if __name__ == "__main__":
    main()
