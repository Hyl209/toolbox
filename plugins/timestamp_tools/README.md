# 时间戳工具插件

用于 Unix 时间戳、毫秒时间戳和本地日期时间互转，默认使用 `+08:00` 时区。

插件命令：

```python
plugin.handle_command("timestamp_to_datetime", text="1717041600")
plugin.handle_command("datetime_to_timestamp", text="2024-05-30 12:00:00")
plugin.handle_command("current_time")
```
