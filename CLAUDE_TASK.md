# 任务：审查并整理42个未提交文件

你好，我是立哥。请审查当前项目42个未提交文件的改动。

## 背景
上次提交是 "Fix 52 bugs found in full codebase review"，之后有42个文件被修改。
经初步审查约35个文件只有空白/格式化改动，7个有实际逻辑改动。438测试全通过。

## 步骤

### 1. 分类文件
运行 `git diff --stat --ignore-all-space` 确认哪些有逻辑改动、哪些只有空白格式化。

### 2. 检查逻辑改动是否有bug
- auth_dialog.py: 首次默认密码登录强制改密码流程是否完整
- updater.py: is_relative_to() 替代字符串匹配是否正确
- password_policy.py: DEFAULT_ADMIN_PASSWORD 值
- paths.py: 异常日志改进
- tests: 密码同步是否完整

### 3. 修复bug
如发现问题直接修复。

### 4. 分组提交
- commit 1: 逻辑改动（安全修复、新测试、bug修复）
- commit 2: 纯格式化/空白改动

## 约定
- 用 python 不是 python3
- 测试命名 tests_*.py
- pytest 在 tests/ 目录
