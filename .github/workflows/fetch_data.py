import os
import requests
import time
import hashlib
import json
import re
from collections import defaultdict

# 控制是否显示最近30天发电列表
SHOW_RECENT_30_DAYS = True

def calculate_signature(token, params, ts, user_id):
    """计算签名：将 params、ts、user_id 的值拼接后计算 MD5"""
    # 注意：params 已经是字符串形式的 JSON
    sign_str = f"{token}params{params}ts{ts}user_id{user_id}"
    return hashlib.md5(sign_str.encode()).hexdigest()

def fetch_api_data(user_id, token, page=1):
    # 获取当前时间戳
    current_ts = int(time.time())
    print(f"当前时间戳: {current_ts}")

    # API 配置
    api_url = "https://afdian.com/api/open/query-order"
    params_str = json.dumps({"page": page})  # 字符串形式的 JSON
    # 计算签名
    signature = calculate_signature(token, params_str, current_ts, user_id)

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
        raise Exception(f"API请求失败，状态码: {response.status_code}")

    # 检查响应内容是否为空
    if not response.text:
        raise Exception("API返回空响应")

    # 尝试解析JSON
    try:
        return response.json()
    except json.JSONDecodeError as e:
        raise Exception(f"JSON解析失败，响应内容")

def process_all_data(user_id, token):
    """获取所有页面的数据"""
    # 先获取第一页，确定总页数
    first_page_data = fetch_api_data(user_id, token, 1)

    if not (first_page_data and isinstance(first_page_data, dict) and first_page_data.get("ec") == 200):
        return [], 0

    total_page = first_page_data.get('data', {}).get('total_page', 1)
    total_count = first_page_data.get('data', {}).get('total_count', 0)
    all_orders = first_page_data.get('data', {}).get('list', [])

    # 获取剩余页面的数据
    for page in range(2, total_page + 1):
        page_data = fetch_api_data(user_id, token, page)
        if page_data and isinstance(page_data, dict) and page_data.get("ec") == 200:
            all_orders.extend(page_data.get('data', {}).get('list', []))

    return all_orders, total_count

def aggregate_user_data(orders):
    """聚合用户数据，按用户汇总金额"""
    user_data = defaultdict(float)

    for order in orders:
        user_name = order.get('user_name', '未知用户')
        amount = float(order.get('total_amount', '0.00'))
        # 只统计金额大于0的订单
        if amount > 0:
            user_data[user_name] += amount

    # 转换为列表并按金额排序
    sorted_data = sorted(user_data.items(), key=lambda x: x[1], reverse=True)
    return sorted_data

def filter_recent_orders(orders, days=30):
    """过滤最近指定天数的订单"""
    # 计算30天前的时间戳
    cutoff_time = int(time.time()) - (days * 24 * 60 * 60)

    recent_orders = []
    for order in orders:
        create_time = order.get('create_time', 0)
        if create_time >= cutoff_time:
            recent_orders.append(order)

    return recent_orders

def generate_ranking_table(sorted_data, is_english=False):
    """生成排名表格（支持中英文）"""
    if not sorted_data:
        if not is_english:
            return "| 排名 | 用户名称 | 金额 |\n| --- | --- | --- |\n| 暂无数据 | 暂无数据 | 暂无数据 |"
        else:
            return "| Rank | User Name | Amount |\n| --- | --- | --- |\n| No Data | No Data | No Data |"

    if not is_english:
        table_lines = ["| 排名 | 用户名称 | 金额 |", "| --- | --- | --- |"]
        for rank, (user_name, amount) in enumerate(sorted_data, 1):
            # 去除小数点后末尾的0
            formatted_amount = f"{amount:g}"
            table_lines.append(f"| {rank} | {user_name} | {formatted_amount} |")
    else:
        table_lines = ["| Rank | User Name | Amount |", "| --- | --- | --- |"]
        for rank, (user_name, amount) in enumerate(sorted_data, 1):
            # 去除小数点后末尾的0
            formatted_amount = f"{amount:g}"
            table_lines.append(f"| {rank} | {user_name} | {formatted_amount} |")

    return "\n".join(table_lines)

def generate_recent_table(orders, is_english=False):
    """生成最近发电列表表格"""
    if not orders:
        if not is_english:
            return "\n\n## 最近30天发电记录\n\n| 用户名称 | 金额 | 时间 |\n| --- | --- | --- |\n| 暂无数据 | 暂无数据 | 暂无数据 |"
        else:
            return "\n\n## Recent 30 Days Sponsor Records\n\n| User Name | Amount | Time |\n| --- | --- | --- |\n| No Data | No Data | No Data |"

    # 按时间倒序排列（最新的在前面）
    sorted_orders = sorted(orders, key=lambda x: x.get('create_time', 0), reverse=True)

    if not is_english:
        table_lines = ["\n\n## 最近30天发电记录\n\n| 用户名称 | 金额 | 时间 |", "| --- | --- | --- |"]
        for order in sorted_orders:
            user_name = order.get('user_name', '未知用户')
            amount = f"{float(order.get('total_amount', '0.00')):g}"
            # 格式化时间
            create_time = order.get('create_time', 0)
            time_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(create_time)) if create_time else '未知时间'
            table_lines.append(f"| {user_name} | {amount} | {time_str} |")
    else:
        table_lines = ["\n\n## Recent 30 Days Sponsor Records\n\n| User Name | Amount | Time |", "| --- | --- | --- |"]
        for order in sorted_orders:
            user_name = order.get('user_name', 'Unknown User')
            amount = f"{float(order.get('total_amount', '0.00')):g}"
            # 格式化时间
            create_time = order.get('create_time', 0)
            time_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(create_time)) if create_time else 'Unknown Time'
            table_lines.append(f"| {user_name} | {amount} | {time_str} |")

    return "\n".join(table_lines)

def update_readme_with_table(file_path, table_content):
    """更新README文件中的发电表格"""
    try:
        # 读取README文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 替换表格内容
        pattern = r'<!-- RANKING_TABLE_START -->.*?<!-- RANKING_TABLE_END -->'
        replacement = f"<!-- RANKING_TABLE_START -->\n{table_content}\n<!-- RANKING_TABLE_END -->"
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"成功更新{file_path}中的发电排行榜")
    except FileNotFoundError:
        print(f"{file_path} 文件未找到")

def generate_recent_md_file(orders):
    """生成recentAfdian.md文件内容"""
    # 生成中英文最近发电列表
    chinese_recent_table = generate_recent_table(orders, is_english=False)
    english_recent_table = generate_recent_table(orders, is_english=True)

    # 创建完整的markdown文件内容
    md_content = f"""# 发电记录统计

## 中文版本
{chinese_recent_table}

## English Version
{english_recent_table}

> 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}
"""

    # 写入recentAfdian.md文件
    try:
        with open('recentAfdian.md', 'w', encoding='utf-8') as f:
            f.write(md_content)
        print("成功更新recentAfdian.md文件中的最近发电列表")
    except Exception as e:
        print(f"更新recentAfdian.md文件时出错")

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

if __name__ == "__main__":
    try:
        # 从环境变量获取用户信息
        secret_key_str = os.environ.get('TOKEN')
        # 解析JSON格式的用户信息
        try:
            user_info_list = json.loads(secret_key_str)
        except json.JSONDecodeError as e:
            raise Exception(f"TOKEN环境变量不是有效的JSON格式: {e}")

        if not isinstance(user_info_list, list):
            raise Exception("TOKEN环境变量应为JSON数组格式")

        data_content = 0
        all_orders = []
        # 遍历所有用户信息并累加数据
        for user_info in user_info_list:
            if isinstance(user_info, dict):  # 确保user_info是字典类型
                user_id = user_info.get("user_id")
                token = user_info.get("token")
                if user_id and token:  # 确保user_id和token都存在
                    try:
                        masked_user_id = mask_user_id(user_id)
                        orders, total_count = process_all_data(user_id, token)
                        all_orders.extend(orders)
                        data_content += total_count
                        print(f"用户 {masked_user_id} 数据处理完成，贡献数: {total_count}")
                    except Exception as e:
                        # 对user_id进行掩码处理
                        masked_user_id = mask_user_id(user_id) if user_id else "未知用户"
                        print(f"处理用户 {masked_user_id} 数据时出错: {e}")
                else:
                    print(f"用户信息不完整")
            else:
                print(f"用户信息格式错误")

        # 更新README文件中的徽章（保持原有功能）
        update_readme(str(data_content))
        print(f"成功更新README文件，总计数: {data_content}")

        # 聚合用户数据并生成排名表格（新增功能）
        sorted_user_data = aggregate_user_data(all_orders)

        # 生成中英文排行榜
        chinese_table = generate_ranking_table(sorted_user_data, is_english=False)
        english_table = generate_ranking_table(sorted_user_data, is_english=True)

        # 更新中英文README文件
        update_readme_with_table('README.md', chinese_table)
        update_readme_with_table('README.En.md', english_table)
        print("中英文发电排行榜已更新")

        # 如果启用最近30天发电列表功能
        if SHOW_RECENT_30_DAYS:
            # 生成最近30天发电列表
            recent_orders = filter_recent_orders(all_orders, 30)

            # 生成独立的recentAfdian.md文件
            generate_recent_md_file(recent_orders)
            print("recentAfdian.md文件已更新")

    except Exception as e:
        print(f"程序执行出错")
