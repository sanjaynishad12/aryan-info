from flask import Flask, request, jsonify
import requests
import json
import base64
import random
import string
import hmac
import hashlib
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

app = Flask(__name__)

# ========== REAL GARENA KEYS ==========
KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
HMAC_KEY = bytes.fromhex("32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533")

REGIONS = {
    'IND': {
        'register': 'https://100067.connect.garena.com/oauth/guest/register',
        'token': 'https://100067.connect.garena.com/oauth/guest/token/grant',
        'major_login': 'https://loginbp.common.ggbluefox.com/MajorLogin'
    },
    'ID': {
        'register': 'https://100067.connect.garena.com/oauth/guest/register',
        'token': 'https://100067.connect.garena.com/oauth/guest/token/grant',
        'major_login': 'https://loginbp.ggblueshark.com/MajorLogin'
    }
}

def encrypt_aes(plain_hex):
    try:
        plain_bytes = bytes.fromhex(plain_hex)
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        encrypted = cipher.encrypt(pad(plain_bytes, AES.block_size))
        return encrypted.hex()
    except:
        return None

def generate_password():
    return 'ARYAN_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) + '_FF'

def create_guest_account(region_code):
    config = REGIONS[region_code]
    password = generate_password()
    data = f"password={password}&client_type=2&source=2&app_id=100067"
    signature = hmac.new(HMAC_KEY, data.encode(), hashlib.sha256).hexdigest()
    
    headers = {
        'User-Agent': 'GarenaMSDK/4.0.19P8',
        'Authorization': f'Signature {signature}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        r = requests.post(config['register'], headers=headers, data=data, timeout=25, verify=False)
        res = r.json()
        if 'uid' in res:
            return {'success': True, 'uid': res['uid'], 'password': password}
        return {'success': False}
    except:
        return {'success': False}

def get_token(uid, password, region_code):
    config = REGIONS[region_code]
    data = {
        'uid': uid, 'password': password,
        'response_type': 'token', 'client_type': '2',
        'client_secret': CLIENT_SECRET, 'client_id': '100067'
    }
    try:
        r = requests.post(config['token'], data=data, timeout=25, verify=False)
        res = r.json()
        if 'access_token' in res:
            return {'success': True, 'access_token': res['access_token'], 'open_id': res['open_id']}
        return {'success': False}
    except:
        return {'success': False}

def major_login(access_token, open_id, region_code):
    config = REGIONS[region_code]
    payload_hex = "1a13323032352d30372d33302031313a30323a3531220966726565206669726528013a07312e3132302e32422c416e64726f6964204f5320372e312e32202f204150492d323320284e32473438482f373030323530323234294a0848616e6468656c645207416e64726f69645a045749464960c00c68840772033332307a1f41524d7637205646507633204e454f4e20564d48207c2032343635207c203480019a1b8a010f416472656e6f2028544d292036343092010d4f70656e474c20455320332e319a012b476f6f676c657c31663361643662372d636562342d343934622d383730622d623164616364373230393131a2010c3139372e312e31322e313335aa0102656eb201203939366136323964626364623339363462653662363937386635643831346462ba010134c2010848616e6468656c64ea014066663930633037656239383135616633306134336234613966363031393531366530653463373033623434303932353136643064656661346365663531663261f00101ca0207416e64726f6964d2020457494649ca03203734323862323533646566633136343031386336303461316562626665626466e003daa907e803899b07f003bf0ff803ae088004999b078804daa9079004999b079804daa907c80403d204262f646174612f6170702f636f6d2e6474732e667265656669726574682d312f6c69622f61726de00401ea044832303837663631633139663537663261663465376665666630623234643964397c2f646174612f6170702f636f6d2e6474732e667265656669726574682d312f626173652e61706bf00403f804018a050233329a050a32303139313138363933b205094f70656e474c455332b805ff7fc00504e005dac901ea0507616e64726f6964f2055c4b71734854394748625876574c6668437950416c52526873626d43676542557562555551317375746d525536634e30524f3751453141486e496474385963784d614c575437636d4851322b7374745279377830663935542b6456593d8806019006019a060134a2060134"
    
    OLD_OPEN_ID = b"996a629dbcdb3964be6b6978f5d814db"
    OLD_ACCESS_TOKEN = b"ff90c07eb9815af30a43b4a9f6019516e0e4c703b44092516d0defa4cef51f2a"
    
    payload = bytes.fromhex(payload_hex)
    payload = payload.replace(OLD_OPEN_ID, open_id.encode())
    payload = payload.replace(OLD_ACCESS_TOKEN, access_token.encode())
    
    encrypted = encrypt_aes(payload.hex())
    if not encrypted:
        return {'success': False}
    
    headers = {
        'X-Unity-Version': '2018.4.11f1',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Dalvik/2.1.0'
    }
    
    try:
        r = requests.post(config['major_login'], headers=headers, data=bytes.fromhex(encrypted), timeout=25, verify=False)
        if r.status_code == 200:
            text = r.text
            jwt_match = re.search(r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+', text)
            if jwt_match:
                jwt = jwt_match.group(0)
                return {'success': True, 'jwt': jwt}
        return {'success': False}
    except:
        return {'success': False}

def generate_one(region, name_prefix):
    guest = create_guest_account(region)
    if not guest['success']:
        return None
    
    token = get_token(guest['uid'], guest['password'], region)
    if not token['success']:
        return None
    
    login = major_login(token['access_token'], token['open_id'], region)
    if not login['success']:
        return None
    
    return {
        'uid': guest['uid'],
        'password': guest['password'],
        'name': f"{name_prefix}{random.randint(100,999)}",
        'region': region
    }

@app.route('/')
def home():
    return jsonify({'name': 'ARYAN APIS', 'status': 'online', 'message': 'REAL Free Fire Accounts'})

@app.route('/gen')
def generate():
    name = request.args.get('name', 'ARYAN')
    count = min(int(request.args.get('count', 1)), 2)
    region = request.args.get('region', 'IND').upper()
    
    if region not in REGIONS:
        return jsonify({'error': 'Invalid region'})
    
    accounts = []
    for i in range(count):
        acc = generate_one(region, name)
        if acc:
            accounts.append(acc)
    
    return jsonify({
        'success': True,
        'total': len(accounts),
        'accounts': accounts,
        'note': 'Use these UID & Password in Free Fire Guest Login'
    })
