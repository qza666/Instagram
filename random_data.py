import random
import string

def random_string(length=8):
    """生成随机字符串（包含大小写字母和数字）"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def insert_random_dots(username, max_dots=3):
    """在用户名中插入随机数量的句点"""
    if len(username) < 2:
        return username
    
    positions = list(range(1, len(username)-1))
    random.shuffle(positions)
    num_dots = random.randint(1, max_dots)
    
    username_list = list(username)
    for pos in sorted(positions[:num_dots], reverse=True):
        username_list.insert(pos, '.')
    return ''.join(username_list)

def generate_gmail_alias(code, email):
    """生成Gmail邮箱别名"""
    if code:
        email = email.split('@')[0]
        suffix = random_string(random.randint(5, 10))
        domain = random.choice(["gmail.com", "googlemail.com"])
        email = f"{email}+{suffix}@{domain}".lower()
    return email

def generate_random_user_data(code, email):
    """生成完整的注册表单数据"""
    full_name = random_string(random.randint(6, 12))
    base_username = random_string(random.randint(8, 12))
    username = insert_random_dots(base_username)
    
    return {
        "fullName": full_name,
        "username": username,
        "email": generate_gmail_alias(code, email),
        "password": random_string(random.randint(12, 16)) + random.choice(["!", "@", "#", "$"])
    }