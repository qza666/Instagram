import requests
from config import EMAIL_API, EMAIL_API_KEY
import re
import time

# 获取余额
def get_balance():
    url = EMAIL_API + 'balance?apiKey=' + EMAIL_API_KEY
    response = requests.get(url)
    if response.json()['code'] == 200:
        return response.json()['data']
    return None

# 找到Instagram注册
def find_instagram_register():
    url = EMAIL_API + 'services'
    response = requests.get(url)
    if response.json()['code'] == 200:
        for service in response.json()['data']:
            if service['serviceName'] == 'Instagram':
                return service['serviceId']
    return None

# 查询邮箱类型
def query_email_types():
    url = EMAIL_API + 'types'
    response = requests.get(url)
    if response.json()['code'] == 200:
        email_mapping = {}
        for email_type in response.json().get('data', []):
            name = email_type.get('name')
            if name in ['Outlook', 'Hotmail', 'Gmail']:
                email_mapping[name] = email_type.get('id')
        return email_mapping
    return None


# 购买邮箱，优先微软
def buy_email():
    balance = get_balance()
    if not balance:
        print('获取余额失败')
        return None
    
    if balance < 0.03:
        print('余额不足')
        return None

    email_types = query_email_types()
    if not email_types:
        print('查询邮箱类型失败')
        return None
    
    service_id = find_instagram_register()
    if not service_id:
        print('找不到Instagram注册')
        return None
    
    priority_list = ['Outlook', 'Hotmail', 'Gmail']

    for email_type in priority_list:
        if email_type in email_types:
            email_type_id = email_types[email_type]
            url = f"{EMAIL_API}mailbox?apiKey={EMAIL_API_KEY}&serviceId={service_id}&emailTypeId={email_type_id}"
            response = requests.get(url)
            
            if response.json()['code'] == 200:
                print(f"成功购买 {email_type} 邮箱")
                orders = response.json()['data'].get('orders')
                if orders and isinstance(orders, list):
                    order = orders[0]
                    return order.get('orderId'), order.get('email')
    
    print('购买失败')
    return None, None

# 获取验证码
def latest(orderId):
    url = f"{EMAIL_API}latest/code?orderId={orderId}"
    start_time = time.time()
    while True:
        if time.time() - start_time > 300:
            return None
        
        response = requests.get(url)
        data = response.json()
        
        if data['code'] == 200:
            code = data['data']['code']
            
            if code is not None and code.isdigit():
                return code
            else:
                code = data['data']['title']
                code = re.findall(r'\d{6}', code)
                return code[0]    
        time.sleep(1)


