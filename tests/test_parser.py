"""Tests for tuido.parser module."""

from tuido.parser import parse_task_content


# pytest tests/test_parser.py -s
class TestParseTaskContent:
    """Test cases for parse_task_content function."""

    def test_empty_content(self):
        """Test parsing empty content."""
        result = parse_task_content("")
        assert result["title"] == ""
        assert result["project"] is None
        assert result["tags"] == []
        assert result["priority"] is None
        assert result["updated_at"] is None

    def test_simple_task(self):
        """Test parsing a simple task without metadata."""
        result = parse_task_content("完成文档编写")
        assert result["title"] == "完成文档编写"
        assert result["project"] is None
        assert result["tags"] == []
        assert result["priority"] is None
        assert result["updated_at"] is None

    def test_task_with_tags(self):
        """Test parsing task with tags."""
        result = parse_task_content("修复登录bug #bug #urgent")
        assert result["title"] == "修复登录bug"
        assert result["tags"] == ["bug", "urgent"]

    def test_task_with_priority(self):
        """Test parsing task with priority."""
        result = parse_task_content("完成API开发 !P1")
        assert result["title"] == "完成API开发"
        assert result["priority"] == "P1"

    def test_task_with_lowercase_priority(self):
        """Test parsing task with lowercase priority."""
        result = parse_task_content("完成任务 !p2")
        assert result["title"] == "完成任务"
        assert result["priority"] == "P2"

    def test_task_with_project(self):
        """Test parsing task with project name (global view format)."""
        result = parse_task_content("新增过滤接口 「my-project」")
        assert result["title"] == "新增过滤接口"
        assert result["project"] == "my-project"

    def test_task_with_project_and_metadata(self):
        """Test parsing task with project and other metadata."""
        result = parse_task_content("新增过滤接口 「dts-dancer」 #去n8n依赖 !P1")
        assert result["title"] == "新增过滤接口"
        assert result["project"] == "dts-dancer"
        assert result["tags"] == ["去n8n依赖"]
        assert result["priority"] == "P1"

    def test_task_with_timestamp(self):
        """Test parsing task with timestamp."""
        result = parse_task_content("完成任务 ~2026-02-28T14:30")
        assert result["title"] == "完成任务"
        assert result["updated_at"] == "2026-02-28T14:30"

    def test_task_with_all_metadata(self):
        """Test parsing task with all metadata types."""
        result = parse_task_content("新增过滤接口 「my-project」 #标签1 #标签2 !P0 ~2026-02-28T16:00")
        assert result["title"] == "新增过滤接口"
        assert result["project"] == "my-project"
        assert result["tags"] == ["标签1", "标签2"]
        assert result["priority"] == "P0"
        assert result["updated_at"] == "2026-02-28T16:00"

    def test_project_with_special_characters(self):
        """Test parsing task with project name containing special characters."""
        result = parse_task_content("任务 「project_name-v1.0」 #tag")
        assert result["title"] == "任务"
        assert result["project"] == "project_name-v1.0"
        assert result["tags"] == ["tag"]

    def test_multiple_tags(self):
        """Test parsing task with multiple tags."""
        result = parse_task_content("任务 #tag1 #tag2 #tag3")
        assert result["title"] == "任务"
        assert result["tags"] == ["tag1", "tag2", "tag3"]

    def test_task_with_chinese_content(self):
        """Test parsing task with Chinese content."""
        result = parse_task_content("新增 过滤有效任务 的接口，并在 spacex 上任务上完成替换 「dts-dancer」 #去n8n依赖 !P1 ~2026-02-28T16:00")
        assert result["title"] == "新增 过滤有效任务 的接口，并在 spacex 上任务上完成替换"
        assert result["project"] == "dts-dancer"
        assert result["tags"] == ["去n8n依赖"]
        assert result["priority"] == "P1"
        assert result["updated_at"] == "2026-02-28T16:00"

    def test_task_without_space_between_metadata(self):
        """Test parsing task where metadata is tightly packed."""
        result = parse_task_content("任务#tag!P1")
        assert result["title"] == "任务"
        assert result["tags"] == ["tag"]
        assert result["priority"] == "P1"

    def test_invalid_priority_not_extracted(self):
        """Test that invalid priority levels (P5-P9) are not extracted."""
        result = parse_task_content("任务 !P5 !P6 !invalid")
        # P5, P6 and invalid are not valid priorities (only P0-P4)
        assert result["priority"] is None
        # But they should still be in the content
        assert "!P5" in result["content"]

    def test_project_with_brackets_in_middle(self):
        """Test that project brackets in middle of text are handled correctly."""
        result = parse_task_content("「project」 开头的任务 #tag")
        assert result["project"] == "project"
        # The project should be removed from title
        assert result["title"] == "开头的任务"

    def test_content_field_contains_original(self):
        """Test that content field contains original content without timestamp and project."""
        result = parse_task_content("任务 「proj」 #tag !P1 ~2026-01-01T12:00")
        # content should have tags and priority but not timestamp or project
        assert "~2026-01-01T12:00" not in result["content"]
        assert "「proj」" not in result["content"]
        assert "#tag" in result["content"]
        assert "!P1" in result["content"]
