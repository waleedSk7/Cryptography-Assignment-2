# crypto_utils.py
import hashlib

# ---------------------------
# SHA256-based Hashing Functions
# ---------------------------
def sha256_hash(data):
    return hashlib.sha256(data.encode()).hexdigest()

def generate_id(input_str, length=16):
    """
    Generate a unique ID by hashing the input string using SHA256
    and taking the first 'length' hex digits.
    """
    hash_val = sha256_hash(input_str)
    return hash_val[:length]

# ---------------------------
# SPECK64/128 Encryption & Decryption
# ---------------------------
# We work with a 64-bit block (our MID is 16 hex digits = 64 bits) and a fixed 128-bit key.
# Parameters follow the SPECK64/128 specification (27 rounds, alpha=8, beta=3).

def rol(x, r, bits=32):
    return ((x << r) & ((1 << bits) - 1)) | (x >> (bits - r))

def ror(x, r, bits=32):
    return (x >> r) | ((x << (bits - r)) & ((1 << bits) - 1))

def speck64_128_encrypt(plaintext, key):
    """
    Encrypt a 64-bit integer (plaintext) using SPECK64/128.
    `key` is a tuple of 4 32-bit integers.
    """
    alpha = 8
    beta = 3
    rounds = 27
    mask = 0xffffffff

    # Key schedule:
    k = [key[0]]
    l = list(key[1:])
    for i in range(rounds - 1):
        li_rot = ror(l[i], alpha, 32)
        new_k = ((k[i] + li_rot) & mask) ^ i
        k.append(new_k)
        li_new = rol(l[i], beta, 32) ^ new_k
        l.append(li_new)

    # Split plaintext into two 32-bit words
    x = (plaintext >> 32) & mask
    y = plaintext & mask

    for i in range(rounds):
        x = (((ror(x, alpha, 32) + y) & mask) ^ k[i])
        y = rol(y, beta, 32) ^ x

    encrypted = (x << 32) | y
    return encrypted

def speck_encrypt_mid(mid_hex):
    """
    Encrypt a 64-bit merchant ID (given as a 16-digit hex string)
    using the SPECK64/128 algorithm.
    """
    plaintext = int(mid_hex, 16)
    # Use the constant 128-bit key as specified in your PDF:
    key = (0x19181110, 0x11109887, 0x09080706, 0x01000302)
    encrypted = speck64_128_encrypt(plaintext, key)
    # Return encrypted result as a 16-digit hex string.
    return format(encrypted, '016x')

def speck64_128_decrypt(ciphertext, key):
    """
    Decrypt a 64-bit integer (ciphertext) using SPECK64/128.
    """
    alpha = 8
    beta = 3
    rounds = 27
    mask = 0xffffffff

    # Generate round keys (same as in encryption)
    k = [key[0]]
    l = list(key[1:])
    for i in range(rounds - 1):
        li_rot = ror(l[i], alpha, 32)
        new_k = ((k[i] + li_rot) & mask) ^ i
        k.append(new_k)
        li_new = rol(l[i], beta, 32) ^ new_k
        l.append(li_new)
    
    # Split ciphertext into two 32-bit words
    x = (ciphertext >> 32) & mask
    y = ciphertext & mask

    # Decryption rounds (reverse order)
    for i in reversed(range(rounds)):
        y = ror(y ^ x, beta, 32)
        x = rol(x ^ k[i], alpha, 32)
        x = (x - y) & mask

    plaintext = (x << 32) | y
    return plaintext

def speck_decrypt_vmid(vmid_hex):
    """
    Decrypt the VMID (16-digit hex string) to retrieve the original MID.
    """
    ciphertext = int(vmid_hex, 16)
    key = (0x19181110, 0x11109887, 0x09080706, 0x01000302)
    plaintext = speck64_128_decrypt(ciphertext, key)
    return format(plaintext, '016x')
