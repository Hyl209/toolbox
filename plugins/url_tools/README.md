# URL 工具插件

用于 URL 编码、解码、查询参数解析和完整 URL 摘要。

插件命令：

```python
plugin.handle_command("encode_url", text="中文 参数")
plugin.handle_command("decode_url", text="%E4%B8%AD%E6%96%87")
plugin.handle_command("parse_query", text="https://x.test?a=1&b=2")
plugin.handle_command("summarize_url", text="https://x.test/path?a=1#top")
```
