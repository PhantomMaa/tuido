from datetime import datetime
from typing import Any


def parse_feishu_timestamp(timestamp_value: Any) -> str:
    """将飞书返回的时间戳转换为本地格式.

    飞书可能返回:
    - 毫秒级 Unix 时间戳 (int): 1772260200000
    - ISO 格式字符串: "2026-02-28T14:30:00"
    - 空值

    返回:
        格式为 "YYYY-MM-DDTHH:MM" 的字符串，或空字符串
    """
    if not timestamp_value:
        return ""

    # 如果是数字（毫秒时间戳）
    if isinstance(timestamp_value, (int, float)):
        try:
            dt = datetime.fromtimestamp(timestamp_value / 1000)
            return dt.strftime("%Y-%m-%dT%H:%M")
        except (ValueError, OSError):
            return ""

    # 如果是字符串，尝试解析
    if isinstance(timestamp_value, str):
        # 已经是目标格式
        if len(timestamp_value) == 16 and timestamp_value[10] == "T":
            return timestamp_value

        # 尝试解析 ISO 格式 (2026-02-28T14:30:00)
        try:
            if "T" in timestamp_value:
                dt = datetime.fromisoformat(timestamp_value.replace("Z", "+00:00").replace("+00:00", ""))
                return dt.strftime("%Y-%m-%dT%H:%M")
        except ValueError:
            pass

    return ""
