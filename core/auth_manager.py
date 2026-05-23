# auth_manager.py
from DrissionPage import ChromiumPage, ChromiumOptions
import json
import os
import time
import shutil  # 用于删除文件夹

CONFIG_FILE = "auth_config.json"
PROFILE_DIR = "ds_browser_profile"


def refresh_credentials():
    """启动 DrissionPage 引擎，接管或重建登录态"""
    print("==================================================")
    print("🤖 [维生系统] 检测到凭证过期或缺失，启动 DrissionPage 引擎...")

    co = ChromiumOptions()
    co.set_user_data_path(PROFILE_DIR)

    page = None  # 提前声明，防止启动失败时 finally 报错
    try:
        page = ChromiumPage(co)
        page.get("https://chat.deepseek.com")

        print("⏳ [维生系统] 正在监听底层 LocalStorage 登录令牌...")

        token_data = None
        while True:
            try:
                token_str = page.run_js('return localStorage.getItem("userToken");')

                if token_str:
                    if "eyJ" in token_str and not token_str.startswith("{"):
                        token_data = {"token": token_str}
                        break

                    parsed_data = json.loads(token_str)
                    if parsed_data and parsed_data.get("token"):
                        token_data = parsed_data
                        break
                    elif parsed_data and parsed_data.get("value"):
                        token_data = {"token": parsed_data["value"]}
                        break
            except Exception:
                pass

            print("🚨 [维生系统] 尚未登录，请在弹出的浏览器窗口中手动扫码/登录...")
            time.sleep(3)

        print("✅ [维生系统] 成功捕获有效 Token！")

        # 全版本兼容的 Cookie 提取
        raw_cookies = page.cookies()
        cookie_str = ""
        if isinstance(raw_cookies, dict):
            cookie_str = "; ".join([f"{k}={v}" for k, v in raw_cookies.items()])
        elif isinstance(raw_cookies, list):
            cookie_str = "; ".join([f"{c.get('name')}={c.get('value')}" for c in raw_cookies if c.get('name')])

        auth_data = {
            "Authorization": f"Bearer {token_data['token']}",
            "Cookie": cookie_str
        }

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(auth_data, f, ensure_ascii=False, indent=4)

        print("💾 [维生系统] 凭证已完成本地持久化存储。")
        return auth_data

    except Exception as e:
        print(f"\n❌ [维生系统] 发生致命异常: {e}")
        return None

    finally:
        # 🚌 班车准时熄火：无论成功还是报错，绝对保证关闭浏览器
        if page:
            print("🚌 [维生系统] 任务结束，班车关门撤退...")
            page.quit()


def get_valid_auth():
    """对外暴露的凭证获取接口"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                auth_data = json.load(f)
                if auth_data.get("Authorization") and auth_data.get("Cookie"):
                    return auth_data
        except Exception:
            pass
    return refresh_credentials()


def force_logout():
    """核平协议：彻底销毁当前账号的所有痕迹"""
    print("==================================================")
    print("💥 [核平协议] 正在销毁本地所有凭证与浏览器配置...")

    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print("🗑️ 已删除本地 Token 配置 (auth_config.json)")

    if os.path.exists(PROFILE_DIR):
        try:
            shutil.rmtree(PROFILE_DIR)
            print("🗑️ 已销毁浏览器用户缓存 (ds_browser_profile)")
        except Exception as e:
            print(f"⚠️ 无法完全删除缓存目录 (可能被系统占用): {e}")

    print("✅ [状态重置] 撤退完成。下次启动将要求重新登录全新账号。")


if __name__ == "__main__":
    # 如果单独运行这个文件，可以作为注销工具使用
    choice = input("请输入指令 (1: 测试获取凭证, 2: 执行核平注销): ")
    if choice == "2":
        force_logout()
    else:
        get_valid_auth()