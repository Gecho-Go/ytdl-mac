# YouTube 下载工具

双击即用的 macOS YouTube 下载小工具，基于 yt-dlp。

![macOS](https://img.shields.io/badge/macOS-11%2B-blue) ![Python](https://img.shields.io/badge/Python-3.11%2B-green)

## 使用

1. 安装依赖（只需一次）：

```bash
brew install yt-dlp python-tk@3.12
```

2. 将 `YouTubeDownloader.app` 拖到任意位置（如应用程序文件夹或桌面）

3. 双击打开，粘贴链接，下载

> 首次打开如提示"无法验证开发者"，右键 → 打开 即可。

## 功能

- 支持粘贴长链接，完整显示不截断
- 自动检测并使用系统代理（Clash、Shadowsocks 等），大陆用户无需额外配置
- 记住上次下载位置
- 下载进度在终端实时显示

## 依赖

| 依赖 | 用途 |
|------|------|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 视频下载核心 |
| python-tk@3.12 | GUI 界面（Tk 8.6+） |
