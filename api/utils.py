# api/utils.py
import re

def decode_st_squashed_payload(body, messages):
    """[全自适应流量清洗] 动态解析 ST 压缩的单维字符串"""
    if len(messages) != 1 or not messages[0].get("content"):
        return messages

    raw_text = messages[0]["content"]
    user_name = body.get("user_name", "User")
    char_name = body.get("char_name", "Assistant")

    split_pattern = re.compile(
        rf'\n(?=(?:Human|Assistant|User|AI|{re.escape(user_name)}|{re.escape(char_name)}):|'
        rf'\[(?:Human|Assistant|User|AI|{re.escape(user_name)}|{re.escape(char_name)})\]:|'
        rf'<role>(?:user|model|system|{re.escape(user_name)}|{re.escape(char_name)}))',
        re.IGNORECASE
    )

    print(f"🕵️ [流量清洗] 探测到单维压缩载荷！启动自适应动态切割 (User: {user_name}, Char: {char_name})...")
    parts = split_pattern.split(raw_text)

    if len(parts) <= 1:
        print("⚠️ [流量清洗] 载荷过于紧密，无法切片，放行原始数据。")
        return messages

    reconstructed_array = []
    user_match = re.compile(rf'^(?:Human|User|{re.escape(user_name)}):|^\[(?:Human|User|{re.escape(user_name)})\]:|^<role>(?:user|{re.escape(user_name)})', re.IGNORECASE)
    char_match = re.compile(rf'^(?:Assistant|AI|{re.escape(char_name)}):|^\[(?:Assistant|AI|{re.escape(char_name)})\]:|^<role>(?:model|{re.escape(char_name)})', re.IGNORECASE)

    for part in parts:
        part = part.strip()
        if not part: continue
        if user_match.search(part):
            reconstructed_array.append({"role": "user", "content": user_match.sub('', part).strip()})
        elif char_match.search(part):
            reconstructed_array.append({"role": "assistant", "content": char_match.sub('', part).strip()})
        else:
            reconstructed_array.append({"role": "user", "content": part})

    print(f"✅ [流量清洗] 逆转成功！重组为 {len(reconstructed_array)} 维的标准时间线。")
    return reconstructed_array