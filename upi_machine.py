# upi_machine.py
import socket
import json
from crypto_utils import speck_encrypt_mid, speck_decrypt_vmid
import qrcode
import threading

BANK_HOST = "127.0.0.1"  # Adjust if Bank server is remote
BANK_PORT = 9000

HOST = '0.0.0.0'
PORT = 9001

def forward_transaction(merchant_id, user_details):
    request = {
        "type": "transaction_request",
        "merchant_id": merchant_id,
        "user_details": user_details
    }
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((BANK_HOST, BANK_PORT))
    s.sendall(json.dumps(request).encode())
    response = s.recv(4096)
    s.close()
    return json.loads(response.decode())

def handle_client(conn, addr):
    print("[UPI Machine] Connected by", addr)
    data = conn.recv(4096)
    if not data:
        conn.close()
        return
    try:
        request = json.loads(data.decode())
    except:
        conn.sendall(json.dumps({"status": "error", "message": "Invalid JSON"}).encode())
        conn.close()
        return

    req_type = request.get("type")
    if req_type == "qr_request":
        merchant_id = request.get("merchant_id")
        if merchant_id:
            vmid = speck_encrypt_mid(merchant_id)
            response = {"status": "success", "vmid": vmid}
        else:
            response = {"status": "error", "message": "Missing merchant_id"}
    elif req_type == "transaction_request":
        vmid = request.get("vmid")
        user_details = request.get("user_details")
        if vmid and user_details:
            # Decrypt VMID to recover the original MID
            merchant_id = speck_decrypt_vmid(vmid)
            bank_response = forward_transaction(merchant_id, user_details)
            response = bank_response
        else:
            response = {"status": "error", "message": "Missing vmid or user_details"}
    else:
        response = {"status": "error", "message": "Unknown request type"}

    conn.sendall(json.dumps(response).encode())
    conn.close()

def start_upi_machine_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"[UPI Machine] Server listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()
    except KeyboardInterrupt:
        print("Shutting down UPI Machine server")
    s.close()

def get_merchant_name(merchant_id):
    request = {"type": "get_merchant_name", "merchant_id": merchant_id}
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((BANK_HOST, BANK_PORT))
    s.sendall(json.dumps(request).encode())
    response = s.recv(4096)
    s.close()
    response_data = json.loads(response.decode())
    if response_data.get("status") == "success":
         return response_data.get("merchant_name")
    else:
         return None

def generate_qr_code_for_merchant():
    print("=== QR Code Generation ===")
    merchant_id = input("Enter the Merchant ID (MID) provided by the Bank: ")
    merchant_name = get_merchant_name(merchant_id)
    if merchant_name is None:
        print("Merchant not found. Using default name for QR code file.")
        merchant_name = "merchant"
    vmid = speck_encrypt_mid(merchant_id)
    print("Generated Virtual Merchant ID (VMID):", vmid)
    # Generate and save a QR code containing the VMID
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(vmid)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # Save the image with filename format: qr_merchantname.png
    sanitized_name = merchant_name.replace(" ", "_")
    filename = f"qr_{sanitized_name}.png"
    img.save(filename)
    print(f"QR code generated and saved as {filename}")
    return vmid

def run_server_in_thread():
    server_thread = threading.Thread(target=start_upi_machine_server, daemon=True)
    server_thread.start()

def main():
    print("=== UPI Machine Application ===")
    print("Starting UPI Machine server...")
    run_server_in_thread()
    
    # Main loop: allow the user to generate new QR codes as needed while the server remains active.
    while True:
        print("\nOptions:")
        print("1: Generate QR code for a merchant")
        print("q: Quit")
        choice = input("Enter your choice: ").strip().lower()
        if choice == "1":
            generate_qr_code_for_merchant()
        elif choice == "q":
            print("Exiting application.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
