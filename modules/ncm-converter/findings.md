# Findings

- 现有文件：
  - ncm_to_mp3.py：命令行转换入口
  - tests_ncm_to_mp3.py：基础测试
- GUI 新需求：
  - 使用 PySide6
  - 支持批量拖拽文件和文件夹
  - 支持指定输出目录
  - 支持批量转换与日志展示
- 设计方向：复用现有核心转换逻辑，新增独立 GUI 入口，避免把转换逻辑写死在界面层。
- 已补充需求：输出目录需要记忆，且允许随时修改。
- Task 1 RED/GREEN 完成：已补共享收集接口 `collect_input_paths` 与 `convert_many`。
- PySide6 安装受网络影响：首次超时，第二次下载 addons 包时 read timeout，当前尚未安装成功。
