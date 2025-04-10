from flask import Flask, render_template, request, redirect, session, url_for, send_file
import socket
import threading
import json
import qrcode
from io import BytesIO
import os
import uuid

app = Flask(__name__)
app.secret_key = "supersecretkey123!"  # Replace with a secure secret key

# Configuration
BANK_HOST = "10.210.156.1"       # Bind to all interfaces (for the socket server)
BANK_PORT = 9000            # Socket server port (for internal bank communications)
UPI_HOST = "10.210.156.44"  # Update to the correct UPI machine IP address
UPI_PORT = 9001             # Port for UPI socket communications

BLOCKCHAIN_FILE = "blockchain.json"

# In-memory databases (for demo purposes)
users = {}
merchants = {}
blockchain = []

def write_blockchain_to_file():
    """Write the in-memory blockchain to a file."""
    try:
        with open(BLOCKCHAIN_FILE, "w") as f:
            json.dump(blockchain, f, indent=4)
    except Exception as e:
        print("Failed to write blockchain:", e)

def send_request(data, host, port):
    """Send a JSON request over a socket to the specified host and port."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall(json.dumps(data).encode())
        response = s.recv(4096)
        decoded = json.loads(response.decode())
        # If the request is one that alters the blockchain, update the file
        if data.get("type") in ["merchant_registration", "user_registration", "transaction_request"]:
            write_blockchain_to_file()
        return decoded
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        s.close()

# ------------------- Flask routes -------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/merchant/register", methods=["GET", "POST"])
def merchant_register():
    if request.method == "POST":
        data = {
            "type": "merchant_registration",
            "name": request.form["name"],
            "password": request.form["password"],
            "initial_balance": request.form["initial_balance"],
            "ifsc_code": request.form["ifsc_code"]
        }
        response = send_request(data, BANK_HOST, BANK_PORT)
        if response.get("status") == "success":
            return render_template("transaction_result.html",
                                   message=f"Merchant Registered! MID: {response['mid']}")
        return render_template("merchant_register.html", error=response.get("message"))
    return render_template("merchant_register.html")

@app.route("/user/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        data = {
            "type": "user_registration",
            "username": request.form.get("username"),
            "password": request.form.get("password"),
            "mobile_number": request.form.get("mobile"),
            "upi_pin": request.form.get("pin"),
            "initial_balance": request.form.get("initial_balance")
        }
        response = send_request(data, BANK_HOST, BANK_PORT)
        if response.get("status") == "success":
            session["uid"] = response["uid"]
            session["mmid"] = response["mmid"]
            return render_template("transaction_result.html",
                                   message=f"User Registered! UID: {response['uid']}, MMID: {response['mmid']}")
        return render_template("user_register.html", error=response.get("message"))
    return render_template("user_register.html")

@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        data = {
            "type": "user_login",
            "username": request.form["user_id"],
            "password": request.form["password"]
        }
        response = send_request(data, BANK_HOST, BANK_PORT)
        if response.get("status") == "success":
            session["uid"] = response["uid"]
            session["mmid"] = response["mmid"]
            return redirect(url_for("initiate_transaction"))
        return render_template("user_login.html", error=response.get("message"))
    return render_template("user_login.html")

@app.route("/transaction", methods=["GET", "POST"])
def initiate_transaction():
    if "mmid" not in session:
        return redirect(url_for("user_login"))
    if request.method == "POST":
        data = {
            "type": "transaction_request",
            "vmid": request.form["vmid"],
            "user_details": {
                "mmid": session["mmid"],
                "amount": request.form["amount"],
                "upi_pin": request.form["upi_pin"]
            }
        }
        response = send_request(data, UPI_HOST, UPI_PORT)
        return render_template("transaction_result.html", 
                               message=response.get("message", "Unknown error occurred"))
    return render_template("initiate_transaction.html")

@app.route("/generate_qr", methods=["GET", "POST"])
def generate_qr():
    if request.method == "POST":
        data = {
            "type": "qr_request",
            "merchant_id": request.form["mid"]
        }
        response = send_request(data, UPI_HOST, UPI_PORT)
        if response.get("status") == "success":
            qr = qrcode.make(response["vmid"])
            buf = BytesIO()
            qr.save(buf, format="PNG")
            buf.seek(0)
            return send_file(buf, mimetype="image/png")
        return render_template("generate_qr.html", error=response.get("message"))
    return render_template("generate_qr.html")

@app.route("/view_blockchain", methods=["GET"])
def view_blockchain():
    if os.path.exists(BLOCKCHAIN_FILE):
        with open(BLOCKCHAIN_FILE, "r") as f:
            bc = json.load(f)
    else:
        bc = []
    return render_template("bank_dashboard.html", blockchain=bc)

# ------------------- Socket Server -------------------

def bank_socket_server():
    """Runs the bank's socket server to process incoming JSON requests."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((BANK_HOST, BANK_PORT))
    server.listen(5)
    print(f"[✓] Bank socket server running on {BANK_HOST}:{BANK_PORT}")

    while True:
        client, addr = server.accept()
        print(f"[+] Connection from {addr}")
        try:
            data = client.recv(4096)
            req = json.loads(data.decode())

            # Handle different request types
            if req["type"] == "user_registration":
                uid = str(uuid.uuid4())[:8]
                mmid = str(uuid.uuid4())[:8]
                users[uid] = {
                    **req,
                    "uid": uid,
                    "mmid": mmid,
                    "balance": float(req["initial_balance"])
                }
                blockchain.append({"event": "user_registration", "uid": uid})
                resp = {"status": "success", "uid": uid, "mmid": mmid}

            elif req["type"] == "merchant_registration":
                mid = str(uuid.uuid4())[:8]
                merchants[mid] = {
                    **req,
                    "mid": mid,
                    "balance": float(req["initial_balance"])
                }
                blockchain.append({"event": "merchant_registration", "mid": mid})
                resp = {"status": "success", "mid": mid}

            elif req["type"] == "user_login":
                for u in users.values():
                    if u["username"] == req["username"] and u["password"] == req["password"]:
                        resp = {"status": "success", "uid": u["uid"], "mmid": u["mmid"]}
                        break
                else:
                    resp = {"status": "error", "message": "Invalid credentials"}

            elif req["type"] == "get_blockchain":
                resp = {"status": "success", "chain": blockchain}

            else:
                resp = {"status": "error", "message": "Invalid request type"}

            client.sendall(json.dumps(resp).encode())
        except Exception as e:
            err_resp = {"status": "error", "message": str(e)}
            client.sendall(json.dumps(err_resp).encode())
        finally:
            client.close()

if __name__ == "__main__":
    # Start the bank socket server in a background thread
    threading.Thread(target=bank_socket_server, daemon=True).start()
    # Start the Flask web server
    app.run(debug=True, host="0.0.0.0", port=5000)
