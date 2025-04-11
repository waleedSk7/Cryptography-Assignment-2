# Centralized UPI Payment Gateway with Blockchain, LWC, and Quantum Cryptography

A secure payment processing system that integrates blockchain technology, lightweight cryptography (SPECK algorithm), and quantum security testing for future-proof transaction protection.

## Project Overview

This project implements a centralized UPI payment gateway with the following components:

1. **Bank Server**: Handles account management, transaction verification, and blockchain ledger maintenance
2. **UPI Machine**: Manages QR code generation and payment request processing
3. **User Interface**: Provides registration, login, and transaction functionality
4. **Merchant Interface**: Enables merchant registration and transaction processing
5. **Quantum Security Testing**: Demonstrates vulnerability analysis using Shor's algorithm

## System Architecture

The system consists of interconnected components that communicate via socket connections:
- Bank Server (TCP port 9000): Central authentication and transaction processing
- UPI Machine (TCP port 9001): QR code generation and payment routing
- Web Interface (HTTP port 5000): User-facing web application

## Security Features

1. **Blockchain Ledger**: Immutable transaction records for transparency and security
2. **SPECK Algorithm**: Lightweight cryptography for secure merchant ID encryption
3. **Quantum Security Analysis**: Vulnerability testing against quantum computing threats

## Installation Requirements

pip install -r requirements.txt


## Demonstration Setup (Three-Laptop Configuration)

### Prerequisites
- Three laptops connected to the same network
- Python 3.8+ installed on all systems
- Required dependencies installed via requirements.txt

### Laptop 1: Bank Server
1. Clone the repository
2. Navigate to the project directory
3. Update the `BANK_HOST` in bank_app.py to Laptop 1's IP address and `UPI_HOST` to Laptop 2's IP address
4. Run the bank server:
    python bank_app.py
5. The bank server will start on port 9000 and the web interface on port 5000

### Laptop 2: UPI Machine
1. Clone the repository
2. Navigate to the project directory 
3. Update the following in upi_machine.py:
- `BANK_HOST`: IP address of Laptop 1
- `HOST`: "0.0.0.0" (to accept connections from any device)
4. Run the UPI machine:
    python upi_machine.py
5. The UPI machine will start on port 9001

### Laptop 3: User/Merchant Client
1. Clone the repository
2. Navigate to the project directory
3. Update the following:
- In user_app.py: `BANK_HOST` to Laptop 1's IP and `UPI_HOST` to Laptop 2's IP
- In merchant_app.py: `BANK_HOST` to Laptop 1's IP
4. Run the appropriate application:
    python user_app.py 
    or
    python merchant_app.py


## Demonstration Workflow

1. **Merchant Registration**:
- Run merchant_app.py on Laptop 3
- Enter required details
- Note the generated Merchant ID (MID)

2. **QR Code Generation**:
- On Laptop 2, select option 1 in UPI Machine
- Enter the Merchant ID
- QR code is generated with encrypted VMID

3. **User Registration/Login**:
- Run user_app.py on Laptop 3
- Register with required details or login
- Note the User ID (UID) and MMID

4. **Transaction Processing**:
- When prompted to initiate a transaction, enter 'y'
- Enter VMID from QR code
- Enter MMID, amount, and UPI PIN
- Transaction is processed through UPI Machine to Bank

5. **Blockchain Verification**:
- Access the bank dashboard at http://[Laptop1-IP]:5000/view_blockchain
- View the immutable transaction records

## Web Interface Access

- Bank Dashboard: http://[Laptop1-IP]:5000/view_blockchain
- User Registration: http://[Laptop1-IP]:5000/user/register
- User Login: http://[Laptop1-IP]:5000/user/login
- Merchant Registration: http://[Laptop1-IP]:5000/merchant/register
- Generate QR: http://[Laptop1-IP]:5000/generate_qr

## Quantum Security Analysis

To demonstrate potential security vulnerabilities to quantum computing:
python shors_algorithm.py


This simulation shows how Shor's algorithm could potentially break classical cryptography used in the system, emphasizing the need for quantum-resistant approaches.

## Project Structure

- `bank_app.py`: Bank server implementation
- `upi_machine.py`: UPI machine for QR code generation and transaction routing
- `user_app.py`: User client application
- `merchant_app.py`: Merchant registration client
- `crypto_utils.py`: SPECK algorithm implementation
- `blockchain.py`: Simple blockchain implementation
- `quantum_vulnerability_test.py`: Shor's algorithm simulation on classical computer(local computer)
- `templates/`: Web interface HTML templates
- `static/`: CSS and JavaScript files for web interface

## Contributors

- Waleed Iqbal Shaikh
- Sthitaprajna
- Abhinav Srivastava 
- Dhruv Choudhary
- Riya Agrawal

## License

This project is licensed under the MIT License - see the LICENSE file for details.