from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import random
import string

app = Flask(__name__)
CORS(app)  # السماح بطلبات من المتصفح

# Headers ثابتة
HEADERS = {
    'User-Agent': 'okhttp/4.12.0',
    'clientId': 'AnaVodafoneAndroid',
    'Accept-Language': 'ar',
    'x-agent-operatingsystem': '16',
    'x-agent-device': 'Samsung SM-A165F',
    'x-agent-version': '2025.11.1',
    'x-agent-build': '1063',
    'digitalId': '',
    'device-id': 'b26ba335813fad21'
}

@app.route('/connect', methods=['GET'])
def connect():
    """الاتصال بالمحفظة والحصول على seamlessToken"""
    try:
        url = "http://mobile.vodafone.com.eg/checkSeamless/realms/vf-realm/protocol/openid-connect/auth?client_id=cash-app"
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        
        if data.get('seamlessToken') and data.get('msisdn'):
            msisdn = data['msisdn']
            if msisdn.startswith('1'):
                msisdn = '0' + msisdn
            return jsonify({
                'success': True,
                'seamlessToken': data['seamlessToken'],
                'msisdn': msisdn
            })
        return jsonify({'success': False, 'error': 'فشل الاتصال'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/charge', methods=['POST'])
def charge():
    """شحن الرصيد"""
    try:
        data = request.json
        receiver = data.get('receiver')
        pin = data.get('pin')
        amount = data.get('amount')  # المبلغ المخصوم
        seamless_token = data.get('seamlessToken')
        sender_msisdn = data.get('senderMsisdn')
        
        if not all([receiver, pin, amount, seamless_token, sender_msisdn]):
            return jsonify({'success': False, 'error': 'بيانات ناقصة'})
        
        # 1. الحصول على access token
        token_url = "https://mobile.vodafone.com.eg/auth/realms/vf-realm/protocol/openid-connect/token"
        token_headers = HEADERS.copy()
        token_headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'seamlessToken': seamless_token,
            'silentLogin': 'true',
            'CRP': 'false',
            'firstTimeLogin': 'true'
        })
        token_data = {
            'grant_type': 'password',
            'client_id': 'cash-app',
            'client_secret': 'b86e30a8-ae29-467a-a71f-65c73f2ff5e3'
        }
        
        token_res = requests.post(token_url, data=token_data, headers=token_headers)
        token_json = token_res.json()
        access_token = token_json.get('access_token')
        
        if not access_token:
            return jsonify({'success': False, 'error': 'فشل الحصول على access token'})
        
        # 2. إنشاء digital ID عشوائي
        digital_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=14))
        
        # 3. طلب الشحن
        order_url = "https://mobile.vodafone.com.eg/services/dxl/pom/productOrder"
        order_headers = {
            'User-Agent': 'okhttp/4.12.0',
            'clientId': 'AnaVodafoneAndroid',
            'Accept-Language': 'ar',
            'x-agent-operatingsystem': '16',
            'x-agent-device': 'Samsung SM-A165F',
            'x-agent-version': '2025.11.1',
            'x-agent-build': '1063',
            'digitalId': '',
            'device-id': 'b26ba335813fad21',
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json; charset=UTF-8',
            'api-host': 'ProductOrderingManagement',
            'useCase': 'CashFakkaAndMared',
            'X-Request-ID': 'bb81cbe5-0c77-4673-945e-d2c0de90007a',
            'api-version': 'v2',
            'msisdn': sender_msisdn,
            'Accept': 'application/json'
        }
        
        order_payload = {
            "payment": [
                {
                    "characteristics": [
                        {"name": "authorizationCode", "value": pin},
                        {"name": "digitalTransactionId", "value": digital_id}
                    ],
                    "@type": "digitalWallet"
                }
            ],
            "productOrderItem": [
                {
                    "characteristics": [
                        {"name": "MSISDN", "@type": "receiver", "value": receiver},
                        {"name": "MSISDN", "@type": "sender", "value": sender_msisdn}
                    ],
                    "itemTotalPrice": [
                        {
                            "price": {
                                "taxIncludedAmount": {
                                    "unit": "EGP",
                                    "value": int(amount)
                                }
                            }
                        }
                    ]
                }
            ],
            "@type": "paymentRecharge"
        }
        
        order_res = requests.post(order_url, json=order_payload, headers=order_headers)
        response_text = order_res.text
        
        # محاولة تحليل الاستجابة
        try:
            response_json = order_res.json()
        except:
            response_json = None
        
        return jsonify({
            'success': True,
            'status_code': order_res.status_code,
            'response': response_json,
            'raw': response_text[:500]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)