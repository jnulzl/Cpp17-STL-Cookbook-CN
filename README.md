# C++17 STL Cookbook（中文翻译版 · LaTeX 工程）

把 Jacek Galowicz 的 *C++17 STL Cookbook*（Packt, 2017）译为中文，

- 原书：*C++17 STL Cookbook — Discover the latest enhancements to functional programming and lambda expressions*
- 作者：Jacek Galowicz
- 译者：[陈晓伟](https://github.com/xiaoweiChen/CPP-17-STL-cookbook)
- 中文名：**C++17 STL 库实战手册**

---

## 目录结构

```
latex_source/                  # 本目录即工程根
├── main.tex                   # 编译入口：\input{book/ccs.tex} + \subfile{book/index.tex}
├── build.bat                  # 一键编译：三遍 xelatex，成功后清理 *.minted 缓存
├── main.pdf                   # 编译成品（390 页）
├── images/                    # 53 张插图（按章分目录）+ cover.jpg + icon_info / icon_warning
├── tools/
│   └── convert.py             # Markdown → LaTeX 转换器（同时生成 index.tex）
└── book/
    ├── ccs.tex                # 导言区：自定义命令/环境、minted v3 缓存配置、本项目补丁
    ├── index.tex              # 章节装配（由 tools/convert.py 生成，勿手改）
    ├── manning-pygments-style.tex  # 代码高亮配色
    └── content/
        ├── front/             # 00-cover(封面图) / 00-title(扉页) / preface / about / chapters-summary
        └── main/              # 第 1–10 章：chapter1.tex … chapter10.tex
```

> 正文源文件必须放 `book/content/` 下：`\subfile` 的相对基准是 `book/`，图片路径仍写 `images/...`（相对 `latex_source/`）。
> 上一层目录另有 Markdown 译稿（`content/`）、原书封面（`cover.jpg`）与插图原图（`images/`）。

---

## 环境依赖

| 依赖 | 版本 / 说明 |
|---|---|
| TeX Live | 2026（含 `xelatex`、minted **v3** / `latexminted`、`tcolorbox`、`tabularx`、`booktabs`、`tikz`） |
| Python | 3.x + **Pygments**（`latexminted` 调它做语法高亮）；本机 `D:\anaconda3` |
| 中文字体 | **Source Han Serif SC（思源宋体）**、**Microsoft YaHei** |
| 拉丁字体 | Cambria、Franklin Gothic Medium |
| 等宽字体 | Consolas（`book/ccs.tex` 里写死 `C:/Windows/Fonts/consola*.ttf`） |

> 字体缺失会导致编译报 "font not found"。思源宋体需本机已安装，微软雅黑为 Windows 自带。

---

## 编译

本项目**使用** `build.bat`（与模板工程不同，那个 `build.bat` 是别的书遗留的脚本）：

```bat
build.bat          :: 三遍 xelatex，成功后删除 *.minted 缓存
build.bat keep     :: 三遍 xelatex，保留缓存（改稿期间更快）
```

手动编译时**必须**把 minted 缓存目录指成绝对路径（见「已知坑」第 2 条）：

```bash
# Python 根目录要在 TeX bin 之前，latexminted 才能找到 pygments
export PATH="/d/anaconda3:/d/ProgramData/texlive/2026/bin/windows:$PATH"
export TEXMF_OUTPUT_DIRECTORY="D:/Ego/trans/CPP-17-STL-cookbook/latex_source"
export TEXMFOUTPUT="$TEXMF_OUTPUT_DIRECTORY"

xelatex -shell-escape -interaction=nonstopmode -synctex=1 main.tex   # 跑三遍
```

- `-shell-escape` 是必须的（minted 调外部高亮器）。
- **必须三遍**：目录、书签、交叉引用要收敛；封面用 `remember picture` 定位，两遍才到位。
- 耗时：缓存清空后首遍约 **20 分钟**（1078 个代码块逐个高亮），第二、三遍各 1–2 分钟；
  缓存命中时整轮约 8 分钟。故高频改稿用 `build.bat keep`，出终版用 `build.bat`。
- 排错时给 `xelatex` 加 `-file-line-error`，可直接定位到文件与行号。
- 产物：`main.pdf`（390 页）、`main.aux`、`main.toc`、`main.log`、`main.synctex.gz`。

---

> 如果环境配置遇到问题或者编译失败可以直接到[releases](https://github.com/jnulzl/Cpp17-STL-Cookbook-CN/releases)下载最新的pdf文件
>
## 非官方代码

[Cpp17-STL-Cookbook](https://github.com/PacktPublishing/Cpp17-STL-Cookbook) —— 书中示例代码。
