from datetime import datetime, timedelta
from typing import Any
from loguru import logger
import requests


class FeishuTable:
    """飞书多维表格，传入机器人认证信息，支持自动token续期管理"""

    def __init__(self, api_endpoint: str, bot_app_id: str, bot_app_secret: str, table_app_token: str, table_id: str):
        """
        初始化飞书多维表格类
        """
        self.api_endpoint = api_endpoint
        self.bot_app_id = bot_app_id
        self.bot_app_secret = bot_app_secret
        self.table_app_token = table_app_token
        self.table_id = table_id

    def get_access_token(self) -> str:
        """
        获取tenant_access_token

        Returns:
            tenant_access_token字符串

        Raises:
            Exception: 获取token失败时抛出异常
        """
        url = f"{self.api_endpoint}/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.bot_app_id, "app_secret": self.bot_app_secret}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"获取tenant_access_token失败: {result.get('msg')}")

            token = result.get("tenant_access_token")
            expire_in = result.get("expire", 7200)  # 默认2小时过期

            # 设置过期时间，提前5分钟刷新
            self.token_expire_time = datetime.now() + timedelta(seconds=expire_in - 300)

            logger.info(f"成功获取tenant_access_token，过期时间: {self.token_expire_time}")
            return token

        except Exception as e:
            logger.error(f"获取tenant_access_token失败: {e}")
            raise

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        发起API请求的通用方法

        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: 其他请求参数

        Returns:
            Response对象
        """
        url = f"{self.api_endpoint}{endpoint}"

        # 获取有效token
        token = self.get_access_token()
        # logger.debug(f"使用token: {token} 发送请求: {method} {url}")

        # 设置认证头
        headers = kwargs.get("headers", {"Content-Type": "application/json"})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers

        response: requests.Response | None = None
        try:
            response = requests.request(method, url, **kwargs)
            # logger.debug(f"response_json: {response.json()}")
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            error_detail = response.json() if response is not None else "无响应"
            logger.error(f"API请求失败: {method} {url}, error: {e}, response_json: {error_detail}")
            raise

    def batch_create(self, records: list[Any]) -> bool:
        payload = {"records": records}

        try:
            endpoint = f"/bitable/v1/apps/{self.table_app_token}/tables/{self.table_id}/records/batch_create"
            response = self._make_request("POST", endpoint, json=payload)
            result = response.json()
            if result.get("code") != 0:
                logger.error(f"批量创建表格记录失败: {result.get('msg')}")
                return False

            return True

        except Exception as e:
            logger.error(f"批量创建表格记录失败: {e}")
            return False

    def update(self, table_app_token: str, table_id: str, record_id: str, fields: dict[str, Any]) -> bool:
        payload = {"fields": fields}

        try:
            endpoint = f"/bitable/v1/apps/{table_app_token}/tables/{table_id}/records/{record_id}"
            response = self._make_request("PUT", endpoint, json=payload)
            result = response.json()
            if result.get("code") != 0:
                logger.error(f"更新表格记录失败: {result.get('msg')}")
                return False

            return True

        except Exception as e:
            logger.error(f"更新表格记录失败: {e}")
            return False

    def fetch_records(self, table_view_id: str, field_names: list[str], page_size: int = 100, page_token: str | None = None) -> dict[str, Any]:
        """
        获取表格记录

        Args:
            page_size: 每页记录数，最大500
            page_token: 分页标记

        Returns:
            API响应数据
        """
        endpoint = f"/bitable/v1/apps/{self.table_app_token}/tables/{self.table_id}/records/search"
        params = {"page_size": page_size, "user_id_type": "open_id"}
        if page_token:
            params["page_token"] = page_token

        payload = {"field_names": field_names, "view_id": table_view_id}

        try:
            response = self._make_request("POST", endpoint, json=payload, params=params)
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"API请求失败: {result.get('msg')}")

            return result.get("data", {})

        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"获取记录失败: {e}")
            raise

    def _parse_record(self, record: dict[str, Any], field_names: list[str] | None = None) -> dict[str, Any]:
        """
        解析单条记录，动态提取指定字段

        Args:
            record: 飞书表格记录
            field_names: 需要解析的字段名列表，如果为None则解析所有字段

        Returns:
            解析后的记录信息，包含record_id和指定的字段
        """
        fields = record.get("fields", {})
        result: dict[str, Any] = {"record_id": record.get("record_id", "")}

        # 如果没有指定字段名，则解析所有字段
        target_fields = field_names if field_names else list(fields.keys())

        # 动态解析每个字段
        for field_name in target_fields:
            field_value = fields.get(field_name, [])

            # 处理列表类型字段，支持多值
            if isinstance(field_value, list):
                if len(field_value) == 1:
                    result[field_name] = field_value[0].get("text", "")
                else:
                    parsed_values = []
                    for value in field_value:
                        if isinstance(value, dict) and "text" in value:
                            parsed_values.append(value.get("text", ""))
                        else:
                            parsed_values.append(value)
                    result[field_name] = parsed_values
            else:
                # 非列表类型保持原值
                result[field_name] = field_value

        return result

    def fetch_all(self, table_view_id: str, field_names: list[str], limit: int | None = None) -> list[dict[str, Any]]:
        """
        抓取视图中的所有记录

        Args:
            limit: 可选的记录处理限制数量
        """
        logger.info("开始获取飞书多维表格数据...")

        page_count = 0
        total_count = 0
        processed_count = 0
        page_token = None

        records: list[dict[str, Any]] = []
        while True:
            page_count += 1
            logger.info(f"正在获取第 {page_count} 页数据...")

            try:
                data = self.fetch_records(table_view_id, field_names, page_size=200, page_token=page_token)
                items = data.get("items", [])
                size = len(items)
                total_count += size
                page_token = data.get("page_token")
                logger.info(f"第 {page_count} 页获取到 {size} 条记录，next page_token: {page_token}")

                # 处理每条记录
                for item in items:
                    # 检查是否达到处理限制
                    if limit and processed_count >= limit:
                        logger.info(f"已达到处理限制 {limit}，停止处理")
                        break

                    try:
                        parsed_record = self._parse_record(item)
                        processed_count += 1

                        records.append(parsed_record)

                    except Exception as e:
                        logger.error(f"处理记录失败: {e}, 记录: {item}")
                        continue

                # 如果达到处理限制，退出外层循环
                if limit and processed_count >= limit:
                    break

                # 检查是否还有更多数据
                if not data.get("has_more", False) or not page_token:
                    break

            except Exception as e:
                logger.error(f"获取第 {page_count} 页数据失败: {e}")
                break

        logger.info(f"总共获取到 {total_count} 条记录，成功处理 {processed_count} 条")
        logger.info("数据遍历完成")
        return records


DEFAULT_FIELD_NAMES = ["Task", "Project", "Status", "Tags", "Priority"]


def fetch_existing_tasks(
    api_endpoint: str,
    bot_app_id: str,
    bot_app_secret: str,
    table_app_token: str,
    table_id: str,
    table_view_id: str,
    project_name: str,
    field_names: list[str] = DEFAULT_FIELD_NAMES,
) -> list[dict[str, Any]]:
    """Fetch existing tasks from Feishu table for a specific project.

    Args:
        api_endpoint: Feishu API endpoint
        bot_app_id: Feishu bot app ID
        bot_app_secret: Feishu bot app secret
        table_app_token: Table app token
        table_id: Table ID
        table_view_id: Table view ID
        project_name: Project name to filter by
        field_names: Fields to fetch; defaults to Task/Project/Status/Tags/Priority

    Returns:
        List of parsed records keyed by the requested field names
    """
    bot = FeishuTable(api_endpoint, bot_app_id, bot_app_secret, table_app_token, table_id)
    records = bot.fetch_all(table_view_id, field_names)

    def _normalize(value: Any) -> Any:
        if isinstance(value, list):
            return ", ".join(map(str, value)) if value else ""
        return value if value is not None else ""

    # Filter by project name and normalize
    result = []
    for record in records:
        record_project = record.get("Project", "")
        if record_project == project_name:
            result.append({field: _normalize(record.get(field)) for field in field_names})

    return result


def fetch_global_tasks(
    api_endpoint: str,
    bot_app_id: str,
    bot_app_secret: str,
    table_app_token: str,
    table_id: str,
    table_view_id: str,
    field_names: list[str] = DEFAULT_FIELD_NAMES,
) -> list[dict[str, Any]]:
    """Fetch all tasks from Feishu table for global view.

    Args:
        api_endpoint: Feishu API endpoint
        bot_app_id: Feishu bot app ID
        bot_app_secret: Feishu bot app secret
        table_app_token: Table app token
        table_id: Table ID
        table_view_id: Table view ID
        field_names: Fields to fetch; defaults to Task/Project/Status/Tags/Priority

    Returns:
        List of parsed records keyed by the requested field names
    """
    bot = FeishuTable(api_endpoint, bot_app_id, bot_app_secret, table_app_token, table_id)
    records = bot.fetch_all(table_view_id, field_names)

    def _normalize(value: Any) -> Any:
        if isinstance(value, list):
            return ", ".join(map(str, value)) if value else ""
        return value if value is not None else ""

    return [{field: _normalize(record.get(field)) for field in field_names} for record in records]
