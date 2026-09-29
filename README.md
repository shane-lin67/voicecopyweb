# 口播提取器（VoiceCopyWeb）

一个只在本机运行的网页工具，把视频或音频转换成可编辑的中文口播文字。它是为手机拍完视频后快速提取文案、减少手工听打而做的。

## 使用

双击 `start.command`，或运行 `./start.sh`。电脑和手机连接同一 Wi‑Fi 后，在页面粘贴链接或上传文件。首次转写会下载本地 Whisper 模型。小红书、抖音等链接解析需要用户自行配置 AI Douyin API；直接上传本地文件不需要该服务。

## 注意

发布版不包含 `.access_token`、`data/`、`logs/`、虚拟环境或任何 API Key。语音内容可能包含个人信息，请只处理你有权处理的素材。API、模型和平台下载服务的费用与可用性由用户自行承担。问题和建议请通过 GitHub Issues 联系作者。

配套 AI 工作流见 [`skills/voicecopy-transcription`](skills/voicecopy-transcription/SKILL.md)。

一个只在你的 Mac 上运行的私人网页工具：电脑和同一 Wi-Fi 下的手机都能粘贴视频链接或上传文件，使用 Apple Silicon 的 MLX Whisper 提取中文口播。

## 启动

双击 `start.command`，或在终端运行：

```bash
./start.sh
```

首次运行会安装 MLX Whisper，并在第一次转写时下载模型。终端会显示：

- 电脑访问地址
- 手机访问地址
- 手机访问口令

手机必须和 Mac 连接同一个 Wi-Fi；Mac 必须保持开机且服务正在运行。

## 后台常驻

双击 `install-service.command` 可将工具安装为 macOS 用户后台服务。安装后：

- 登录 Mac 时自动启动
- 终端窗口可以关闭
- 进程异常退出后会自动重启
- 日志保存在 `~/Library/Application Support/VoiceCopyWeb/logs/`

如需取消常驻，双击 `uninstall-service.command`。

## 支持

- 小红书、抖音、B站：复用 `video-to-subtitle-summary` 已有的 AI Douyin 配置
- YouTube 和其他 `yt-dlp` 支持的链接
- 本地视频与音频上传
- 电脑/手机响应式页面
- SSE 实时进度
- 一键复制、结果可继续编辑

## 隐私

语音识别在本机运行。短视频平台链接可能需要调用已有的 AI Douyin 服务解析下载地址；直接上传本地文件不会调用该解析服务。
