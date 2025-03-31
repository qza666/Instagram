import os
import base64
import re
import pickle
import time
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """认证Gmail服务"""
    creds = None
    token_file = f'token.pickle'
    credentials_file = f'credentials.json'
    
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def search_emails(service, target_email, max_results=10):
    """搜索目标邮件"""
    messages = []
    for label in ['INBOX', 'CATEGORY_SOCIAL']:
        result = service.users().messages().list(
            userId='me',
            labelIds=[label],
            maxResults=max_results,
            q=f'to:{target_email} from:no-reply@mail.instagram.com'
        ).execute()
        messages.extend(result.get('messages', []))
    return messages[:max_results]

def extract_html_content(payload):
    """提取邮件HTML内容"""
    if payload['mimeType'] == 'text/html':
        data = payload['body'].get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8')
    elif 'parts' in payload:
        for part in payload['parts']:
            content = extract_html_content(part)
            if content:
                return content
    return ''

def parse_verification_code(html):
    """解析验证码"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # 匹配包含验证码的HTML元素
        code_element = soup.find('td', style=re.compile(r'font-size:\s*32px'))
        if code_element and code_element.text.strip().isdigit():
            return code_element.text.strip()
        return None
    except Exception as e:
        #print(f"❌ HTML解析失败: {e}")
        return None

def fetch_verification_code(service, target_email, retries=3, delay=5):
    """获取验证码主逻辑"""
    for attempt in range(1, retries+1):
        #print(f"\n🔄 尝试第 {attempt} 次获取（共 {retries} 次）")
        messages = search_emails(service, target_email)
        
        if not messages:
            #print("⚠️ 未找到目标邮件")
            time.sleep(delay)
            continue
            
        #print(f"📨 找到 {len(messages)} 封相关邮件")
        
        for i, msg in enumerate(messages):
            full_msg = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            # 提取邮件内容
            html_content = extract_html_content(full_msg['payload'])
            if not html_content:
                continue
                
            # 解析验证码
            if code := parse_verification_code(html_content):
                #print(f"✅ 在第 {i+1} 封邮件中发现验证码")
                return code
                
        #print(f"⏳ 等待 {delay} 秒后重试...")
        time.sleep(delay)
        
    return None