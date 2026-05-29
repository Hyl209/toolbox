# 文件哈希校验插件

用于计算并校验文件 `MD5`、`SHA1`、`SHA256`。支持在 GUI 中选择或拖入文件，也支持通过插件命令调用：

```python
plugin.handle_command("calculate_hashes", path="demo.zip")
plugin.handle_command("verify_hash", path="demo.zip", expected="<checksum>")
```

校验时默认根据哈希长度自动识别算法。
