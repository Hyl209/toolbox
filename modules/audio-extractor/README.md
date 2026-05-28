# mp4-mp3

一个简洁的 mp4 转 mp3 Python 小工具。

功能：
- 支持拖拽 mp4 到命令行调用
- 支持自定义输出 mp3 路径
- 支持记忆默认输出目录
- 支持随时查看、修改、清除默认输出目录
- 提供可给外部 UI 调用的函数：converter.convert_mp4_to_mp3

要求：
- 系统已安装 ffmpeg，并已加入 PATH

用法：
1. 直接转换
   python app.py input.mp4

2. 指定输出 mp3 路径
   python app.py input.mp4 output.mp3

3. 指定输出目录
   python app.py input.mp4 output_folder

4. 设置默认输出目录
   python app.py --set-output-dir output_folder

5. 查看默认输出目录
   python app.py --show-output-dir

6. 清除默认输出目录
   python app.py --clear-output-dir

给 UI 调用示例：
from converter import convert_mp4_to_mp3
result = convert_mp4_to_mp3('a.mp4', 'b.mp3')
print(result)
