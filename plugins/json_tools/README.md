# JSON 工具插件

用于格式化、压缩和校验 JSON 文本。支持保留中文字符输出，并可选择按键排序。

插件命令：

```python
plugin.handle_command("format_json", text='{"name":"HylToolbox"}')
plugin.handle_command("minify_json", text='{"name": "HylToolbox"}')
plugin.handle_command("validate_json", text='{"name":"HylToolbox"}')
```
