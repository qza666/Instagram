from selenium_driver import BrowserAutomator
import json

def main():
    try:
        bot = BrowserAutomator()
        bot.initialize_browser()
        status, user, pwd, email = bot.register_instagram_account()
        
        if status:
            data = {"username":user, "password":pwd, "email":email}
            print(f"注册成功: {json.dumps(data)}")
            with open('data.json','a') as f:
                json.dump(data, f)
                f.write('\n')
    finally:
        bot.close()

if __name__ == "__main__":
    main()

