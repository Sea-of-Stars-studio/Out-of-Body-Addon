import os

import requests
import time
import hashlib
import json
import re

def calculate_signature(token,params, ts, user_id):
    """计算签名：将 params、ts、user_id 的值拼接后计算 MD5"""
    # 注意：params 已经是字符串形式的 JSON

    sign_str = f"{token}params{params}ts{ts}user_id{user_id}"
    return hashlib.md5(sign_str.encode()).hexdigest()

def fetch_api_data(user_id,token):
    # 获取当前时间戳
    current_ts = int(time.time())
    print(f"当前时间戳: {current_ts}")

    # API 配置
    api_url = "https://afdian.com/api/open/query-order"
    params_str = '{"page":1}'  # 字符串形式的 JSON
    # 计算签名
    signature = calculate_signature(token,params_str, current_ts, user_id)

    # 构建请求体
    payload = {
        "user_id": user_id,
        "params": params_str,
        "ts": current_ts,
        "sign": signature
    }

    # 发送请求
    headers = {"Content-Type": "application/json"}

    response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=10)

    # 检查HTTP响应状态码
    if response.status_code != 200:
        raise Exception(f"API请求失败，状态码: {response.status_code}，响应内容: {response.text}")

    # 检查响应内容是否为空
    if not response.text:
        raise Exception("API返回空响应")

    # 尝试解析JSON
    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise Exception(f"JSON解析失败，响应内容")

def process_data(data):
    """处理从API获取的数据，提取用于徽章显示的内容"""
    data_content = 0
    if data and isinstance(data, dict) and data.get("ec") == 200:
        total_count = data.get('data', {}).get('total_count', 0)
        data_content = int(total_count)
    return data_content

def update_readme_file(file_path, pattern, replacement):
    """更新单个README文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    except FileNotFoundError:
        print(f"{file_path} 文件未找到")

def mask_user_id(user_id):
    """将user_id中间8位字符替换为********"""
    if not user_id or len(user_id) <= 16:
        return user_id
    # 将中间8位替换为********
    masked_id = user_id[:8] + "********" + user_id[16:]
    return masked_id

def update_readme(data_content):
    """更新README文件中的徽章数据"""
    # 处理 README.md
    pattern = r'https://img\.shields\.io/badge/a-.*?-c\?style=for-the-badge&label=爱发电&labelColor=%239469e3&color=%23B291F0'
    replacement = f'https://img.shields.io/badge/a-{data_content}-c?style=for-the-badge&label=爱发电&labelColor=%239469e3&color=%23B291F0'
    update_readme_file('README.md', pattern, replacement)

    # 处理 README.En.md
    pattern = r'https://img\.shields\.io/badge/a-.*?-c\?style=for-the-badge&label=Afdian&labelColor=%239469e3&color=%23B291F0'
    replacement = f'https://img.shields.io/badge/a-{data_content}-c?style=for-the-badge&label=Afdian&labelColor=%239469e3&color=%23B291F0'
    update_readme_file('README.En.md', pattern, replacement)

if __name__ == "__main__":
    try:
        # 从环境变量获取用户信息
        secret_key_str = os.environ.get("TOKEN", 'o')

        if secret_key_str == 'o':
            raise Exception("未设置TOKEN环境变量")

        # 解析JSON格式的用户信息
        try:
            user_info_list = json.loads(secret_key_str)
        except json.JSONDecodeError as e:
            raise Exception(f"TOKEN环境变量不是有效的JSON格式: {e}")

        if not isinstance(user_info_list, list):
            raise Exception("TOKEN环境变量应为JSON数组格式")

        data_content = 0
        # 遍历所有用户信息并累加数据
        for user_info in user_info_list:
            if isinstance(user_info, dict):  # 确保user_info是字典类型
                user_id = user_info.get("user_id")
                token = user_info.get("token")
                if user_id and token:  # 确保user_id和token都存在
                    try:
                        masked_user_id = mask_user_id(user_id)
                        data = fetch_api_data(user_id, token)
                        processed_data = process_data(data)
                        data_content += processed_data
                        print(f"用户 {masked_user_id} 数据处理完成，贡献数: {processed_data}")
                    except Exception as e:
                    # 对user_id进行掩码处理
                        masked_user_id = mask_user_id(user_id) if user_id else "未知用户"
                        print(f"处理用户 {masked_user_id} 数据时出错: {e}")
                else:
                    print(f"用户信息不完整")
            else:
                print(f"用户信息格式错误")

        # 更新README文件
        update_readme(str(data_content))
        print(f"成功更新README文件，总计数: {data_content}")
    except Exception as e:
        print(f"程序执行出错: {e}")
