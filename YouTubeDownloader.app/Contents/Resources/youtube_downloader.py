#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess, os, json, re, shutil

CONFIG_FILE = os.path.expanduser("~/.ytdl_config.json")
DEFAULT_DIR  = os.path.expanduser("~/Downloads")


def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            data = json.load(open(CONFIG_FILE))
            return {
                "download_dir": data.get("download_dir", DEFAULT_DIR),
                "remember_dir": data.get("remember_dir", True),
            }
    except Exception:
        pass
    return {"download_dir": DEFAULT_DIR, "remember_dir": True}


def save_config(cfg):
    try:
        json.dump(cfg, open(CONFIG_FILE, "w"), indent=2)
    except Exception:
        pass


def is_youtube(url):
    return bool(re.search(r"(youtube\.com|youtu\.be)", url, re.I))


def detect_proxy():
    try:
        out = subprocess.check_output(["scutil", "--proxy"], text=True, timeout=3)
        if re.search(r"SOCKSEnable\s*:\s*1", out):
            h = re.search(r"SOCKSProxy\s*:\s*(\S+)", out)
            p = re.search(r"SOCKSPort\s*:\s*(\d+)", out)
            if h:
                return f"socks5://{h.group(1)}:{p.group(1) if p else '1080'}"
        if re.search(r"HTTPEnable\s*:\s*1", out):
            h = re.search(r"HTTPProxy\s*:\s*(\S+)", out)
            p = re.search(r"HTTPPort\s*:\s*(\d+)", out)
            if h:
                return f"http://{h.group(1)}:{p.group(1) if p else '7890'}"
    except Exception:
        pass
    return None


def find_ytdlp():
    for p in [
        "/opt/homebrew/bin/yt-dlp",
        "/usr/local/bin/yt-dlp",
        shutil.which("yt-dlp") or "",
        os.path.expanduser("~/.local/bin/yt-dlp"),
    ]:
        if p and os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def sh_q(s):
    return "'" + s.replace("'", "'\\''") + "'"


def launch_download(ytdlp, url, download_dir, proxy):
    args = [ytdlp]
    if proxy:
        args += ["--proxy", proxy]
    args += [
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", os.path.join(download_dir, "%(title)s.%(ext)s"),
        "--", url,
    ]
    cmd = " ".join(sh_q(a) for a in args)

    script = "\n".join([
        "#!/bin/bash",
        f'echo "📁 {download_dir}"',
        'echo ""',
        cmd,
        "STATUS=$?",
        'echo ""',
        'if [ $STATUS -eq 0 ]; then echo "✅ 下载完成！"',
        'else',
        '  echo "❌ 下载失败（错误码: $STATUS）"',
        '  echo "💡 大陆用户请确认代理已开启并设为系统代理。"',
        'fi',
        'echo ""',
        'printf "按回车键关闭..."',
        'read -r',
    ])
    with open("/tmp/ytdl_run.sh", "w") as f:
        f.write(script)
    os.chmod("/tmp/ytdl_run.sh", 0o755)

    subprocess.Popen([
        "osascript", "-e",
        'tell application "Terminal"\n'
        '  do script "bash /tmp/ytdl_run.sh"\n'
        '  activate\n'
        'end tell'
    ])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self._build()

    def _build(self):
        from tkinter import ttk

        self.title("YouTube 下载")
        self.resizable(False, False)

        W, H = 460, 252
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//3}")

        # 外层 Frame，统一内边距
        root = ttk.Frame(self, padding=(22, 18, 22, 20))
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)

        # ── 链接标签
        ttk.Label(root, text="视频链接").grid(
            row=0, column=0, sticky="w", pady=(0, 6))

        # ── 链接输入框（边框跟随焦点变色，模拟原生文本框）
        border = tk.Frame(root,
                          highlightbackground="#c8c8c8",
                          highlightcolor="#c8c8c8",
                          highlightthickness=1, bd=0)
        border.grid(row=1, column=0, sticky="ew")

        self.url_box = tk.Text(
            border, height=3, wrap="word",
            font=("TkDefaultFont", 13),
            relief="flat", bd=0,
            highlightthickness=0,
            padx=8, pady=7, undo=True,
        )
        self.url_box.pack(fill="x")
        self.url_box.focus()
        self.url_box.bind("<FocusIn>",
            lambda e: border.config(highlightbackground="#0064D2",
                                    highlightcolor="#0064D2"))
        self.url_box.bind("<FocusOut>",
            lambda e: border.config(highlightbackground="#c8c8c8",
                                    highlightcolor="#c8c8c8"))

        # ── 下载位置行
        dir_row = ttk.Frame(root)
        dir_row.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        dir_row.columnconfigure(1, weight=1)

        ttk.Label(dir_row, text="存储到",
                  foreground="#888888").grid(row=0, column=0, sticky="w")

        self.dir_var = tk.StringVar(value=self._pretty(self.cfg["download_dir"]))
        ttk.Label(dir_row, textvariable=self.dir_var).grid(
            row=0, column=1, sticky="w", padx=(8, 0))

        ttk.Button(dir_row, text="更改",
                   command=self._pick_dir).grid(row=0, column=2, sticky="e")

        # ── 记住位置复选框
        self.remember_var = tk.BooleanVar(value=self.cfg.get("remember_dir", True))
        ttk.Checkbutton(root, text="记住存储位置",
                        variable=self.remember_var).grid(
            row=3, column=0, sticky="w", pady=(8, 0))

        # ── 主按钮：ttk default="active" → Aqua 主题自动渲染为蓝色主按钮
        btn = ttk.Button(root, text="开始下载",
                         command=self._download, default="active")
        btn.grid(row=4, column=0, pady=(18, 0))
        self.bind("<Return>", lambda e: self._download())

    def _pretty(self, path):
        home = os.path.expanduser("~")
        return "~" + path[len(home):] if path.startswith(home) else path

    def _pick_dir(self):
        d = filedialog.askdirectory(initialdir=self.cfg["download_dir"])
        if d:
            self.cfg["download_dir"] = d
            self.dir_var.set(self._pretty(d))

    def _download(self):
        url = self.url_box.get("1.0", "end").strip().replace("\n", "").replace("\r", "")
        if not url:
            messagebox.showwarning("提示", "请输入视频链接", parent=self)
            return

        if not is_youtube(url):
            ok = messagebox.askokcancel(
                "链接提示",
                "该链接不是 YouTube 链接，继续可能报错。\n\n要继续吗？",
                parent=self, default="cancel",
            )
            if not ok:
                return

        ytdlp = find_ytdlp()
        if not ytdlp:
            messagebox.showerror(
                "未找到 yt-dlp",
                "请先安装 yt-dlp：\n\n  brew install yt-dlp",
                parent=self,
            )
            return

        remember = self.remember_var.get()
        save_config({
            "download_dir": self.cfg["download_dir"] if remember else DEFAULT_DIR,
            "remember_dir": remember,
        })

        proxy = detect_proxy()
        launch_download(ytdlp, url, self.cfg["download_dir"], proxy)
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
