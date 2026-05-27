"""用户友好的错误报告生成器"""
from __future__ import annotations

import re
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional


# 敏感信息过滤模式
_SENSITIVE_PATTERNS = [
    re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),  # 邮箱
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),                       # IP
    re.compile(r"(?i)(password|passwd|token|secret|api[_-]?key)\s*[=:]\s*\S+"),  # 密钥
    re.compile(r"[A-Z]:\\Users\\[^\\]+"),                               # Windows 用户路径
    re.compile(r"/home/[^/]+"),                                         # Linux 用户路径
]


def _sanitize(text: str) -> str:
    """移除文本中的敏感信息"""
    for pat in _SENSITIVE_PATTERNS:
        text = pat.sub("[已隐藏]", text)
    return text


class ErrorReportGenerator:
    """生成用户友好的错误报告，不含敏感数据"""

    def generate_report(self, exception: Exception, context: dict | None = None) -> str:
        """生成错误报告

        Args:
            exception: 捕获的异常
            context: 上下文信息（如操作名称、文件路径等）

        Returns:
            结构化的错误报告文本
        """
        now = datetime.now()
        context = context or {}

        error_type = type(exception).__name__
        error_msg = _sanitize(str(exception))

        # 安全地获取 traceback
        tb = _sanitize("".join(traceback.format_exception(type(exception), exception, exception.__traceback__)))

        # 构建上下文摘要
        ctx_lines = []
        for k, v in context.items():
            ctx_lines.append(f"  {k}: {_sanitize(str(v))}")
        ctx_section = "\n".join(ctx_lines) if ctx_lines else "  (无)"

        report = (
            f"=== 错误报告 ===\n"
            f"时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"错误类型: {error_type}\n"
            f"摘要: {error_msg}\n"
            f"\n--- 上下文信息 ---\n"
            f"{ctx_section}\n"
            f"\n--- 技术详情 ---\n"
            f"{tb}"
        )
        return report

    def format_for_user(self, report: str) -> str:
        """将报告格式化为用户可读的简短文本

        提取错误摘要和时间，去掉技术 traceback，适合弹窗展示。
        """
        lines = report.splitlines()
        summary_lines: list[str] = []
        for line in lines:
            # 只保留时间、错误类型、摘要
            if line.startswith(("时间:", "错误类型:", "摘要:")):
                summary_lines.append(line)
            elif line.startswith("--- 上下文信息 ---"):
                break

        if not summary_lines:
            return "发生未知错误，请查看日志获取详情。"

        return "\n".join(summary_lines)

    def save_report(self, report: str, log_dir: str | Path) -> Path:
        """将报告保存到 logs/crash/ 目录

        Args:
            report: 错误报告文本
            log_dir: 日志根目录

        Returns:
            保存的文件路径
        """
        crash_dir = Path(log_dir) / "crash"
        crash_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = crash_dir / f"error_report_{timestamp}.txt"
        report_file.write_text(report, encoding="utf-8")
        return report_file
