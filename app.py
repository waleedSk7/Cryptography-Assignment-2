from flask import Flask, render_template, request, redirect, session, url_for, send_file
import socket
import json
import qrcode
from io import BytesIO
import os

app = Flask(__name__)
app.secret_key = "supersecretkey123!"  # Replace with a secure secret key

# Configuration for connecting to backend services
# Update these IP addresses as necessary when deploying on different machines.
BANK_HOST = "172.20.44.211"  # IP address of the Bank Server (Laptop A)
BANK_PORT = 9000
UPI_HOST = "172.20.44.96"   # IP address of the UPI Machine (Laptop B)
UPI_PORT = 9001

def send_request(data, host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall(json.dumps(data).encode())
        response = s.recv(4096)
        return json.loads(response.decode())
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        s.close()

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
            "ifsc_code": request.form["ifsc_code"],
            "bank": request.form["bank"]  # New field for bank selection
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
            "initial_balance": request.form.get("initial_balance"),
            "ifsc_code": request.form.get("ifsc_code"),  # New field for user IFSC code
            "bank": request.form.get("bank")             # New field for bank selection
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

# New Route: View all transactions
@app.route("/view_transactions", methods=["GET"])
def view_transactions():
    data = {"type": "get_transactions"}
    response = send_request(data, BANK_HOST, BANK_PORT)
    if response.get("status") == "success":
        transactions = response.get("transactions", [])
        return render_template("transactions.html", transactions=transactions)
    else:
        return render_template("transaction_result.html", message=response.get("message"))

# Optionally, you can also leave your existing blockchain view route if desired.
@app.route('/view_blockchain', methods=['GET'])
def view_blockchain():
    blockchain_file = 'blockchain.json'
    if os.path.exists(blockchain_file):
        with open(blockchain_file, 'r') as f:
            blockchain = json.load(f)
    else:
        blockchain = []
    return render_template('bank_dashboard.html', blockchain=blockchain)

if __name__ == "__main__":
    # If you want to allow external access to the frontend, use host='0.0.0.0'
    app.run(debug=True, port=5000)