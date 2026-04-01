from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import hashlib
from secret import *
import uid_generator_pb2
import requests
import struct
import datetime
from flask import Flask, jsonify
import json
from zitado_pb2 import Users
import random

app = Flask(__name__)

def hex_to_bytes(hex_string):
    return bytes.fromhex(hex_string)

def create_protobuf(saturn_, garena):
    message = uid_generator_pb2.uid_generator()
    message.saturn_ = saturn_
    message.garena = garena
    return message.SerializeToString()

def protobuf_to_hex(protobuf_data):
    return binascii.hexlify(protobuf_data).decode()

def decode_hex(hex_string):
    byte_data = binascii.unhexlify(hex_string.replace(' ', ''))
    users = Users()
    users.ParseFromString(byte_data)
    return users

def encrypt_aes(hex_data, key, iv):
    key = key.encode()[:16]
    iv = iv.encode()[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(bytes.fromhex(hex_data), AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    return binascii.hexlify(encrypted_data).decode()

def apis(idd, token):
    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)',
        'Connection': 'Keep-Alive',
        'Expect': '100-continue',
        'Authorization': f'Bearer {token}',
        'X-Unity-Version': '2018.4.11f1',
        'X-GA': 'v1 1',
        'ReleaseVersion': 'OB50',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = bytes.fromhex(idd)
    response = requests.post('https://clientbp.ggblueshark.com/GetPlayerPersonalShow', headers=headers, data=data)
    hex_response = response.content.hex()
    return hex_response

def token():
    try:
        resp = requests.get("https://scromnyi-jwt.onrender.com/oauth/guest/token/grant?uid=4020527751&password=9F0A4A0EB31A5A6ABF60C156659FA176B75AB4134263FD3292EE6668BF37A752", timeout=5)
        resp.raise_for_status()
        tokens = resp.json()
        token_list = tokens.get('tokens', [])
        if not token_list:
            raise ValueError("Empty token list")
        return random.choice(token_list)
    except Exception as e:
        print(f"Error fetching token: {e}")
        return None

# حل مشكلة favicon
@app.route('/favicon.ico')
def favicon():
    return "", 204

@app.route('/<uid>', methods=['GET'])
def main(uid):
    if not uid.isdigit():
        return jsonify({"error": "Invalid UID"}), 400

    saturn_ = int(uid)
    garena = 1
    protobuf_data = create_protobuf(saturn_, garena)
    hex_data = protobuf_to_hex(protobuf_data)
    aes_key = key
    aes_iv = iv
    encrypted_hex = encrypt_aes(hex_data, aes_key, aes_iv)

    tokenn = token()
    if not tokenn:
        return jsonify({"error": "Could not fetch token"}), 500

    infoo = apis(encrypted_hex, tokenn)
    if not infoo:
        return jsonify({"error": "API response empty"}), 500

    try:
        users = decode_hex(infoo)
    except binascii.Error:
        return jsonify({"error": "Invalid hex data"}), 400

    result = {}

    if users.basicinfo:
        result['basicinfo'] = []
        for user_info in users.basicinfo:
            result['basicinfo'].append({
                'username': user_info.username,
                'region': user_info.region,
                'level': user_info.level,
                'Exp': user_info.Exp,
                'bio': users.bioinfo[0].bio if users.bioinfo else None,
                'banner': user_info.banner,
                'avatar': user_info.avatar,
                'brrankscore': user_info.brrankscore,
                'BadgeCount': user_info.BadgeCount,
                'likes': user_info.likes,
                'lastlogin': user_info.lastlogin,
                'csrankpoint': user_info.csrankpoint,
                'csrankscore': user_info.csrankscore,
                'brrankpoint': user_info.brrankpoint,
                'createat': user_info.createat,
                'OB': user_info.OB
            })

    if users.claninfo:
        result['claninfo'] = []
        for clan in users.claninfo:
            result['claninfo'].append({
                'clanid': clan.clanid,
                'clanname': clan.clanname,
                'guildlevel': clan.guildlevel,
                'livemember': clan.livemember
            })

    if users.clanadmin:
        result['clanadmin'] = []
        for admin in users.clanadmin:
            result['clanadmin'].append({
                'idadmin': admin.idadmin,
                'adminname': admin.adminname,
                'level': admin.level,
                'exp': admin.exp,
                'brpoint': admin.brpoint,
                'lastlogin': admin.lastlogin,
                'cspoint': admin.cspoint
            })

    result['Owners'] = ['@8GRAFIXxAURA']
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
