# -*- coding: utf-8 -*-
"""
Markdown -> LaTeX 转换器（C++17 STL Cookbook 中文版）
严格套用《C++ Initialization Story》的 Manning 风格 LaTeX 模版（book/ccs.tex）。
用法：
    python convert.py            # 生成全部
    python convert.py --chapter 1 # 只生成前言 + 关于本书 + 各章梗概 + 第1章（用于调试）
"""
import os, re, sys, shutil

SRC = "D:/Ego/trans/CPP-17-STL-cookbook/content"
DST = "D:/Ego/trans/CPP-17-STL-cookbook/latex_source"
BOOK_D = os.path.join(DST, "book")
# 与模板一致：章节源文件放在 book/content/ 下（\subfile 的相对基准是 book/）
CONTENT = os.path.join(BOOK_D, "content")
FRONT_D = os.path.join(CONTENT, "front")
MAIN_D = os.path.join(CONTENT, "main")

LANGMAT = {
    "": "text", "text": "text", "txt": "text", "plain": "text", "plaintext": "text",
    "bash": "text", "sh": "text", "shell": "text", "console": "text",
    "output": "text", "log": "text", "make": "text", "cmake": "text", "ini": "text",
    "c++": "cpp", "cpp": "cpp", "c": "cpp", "cc": "cpp", "h": "cpp",
    "python": "python", "py": "python", "xml": "xml", "html": "html",
    "json": "json", "java": "java",
}

# ---- 转义 ----------------------------------------------------------------
CODESPEC = {
    '\\': r'\textbackslash{}', '%': r'\%', '#': r'\#', '&': r'\&',
    '_': r'\_', '$': r'\$', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
    '{': r'\{', '}': r'\}',
}

def esc_code(s):
    return re.sub(r'([\\%#&_$~^{}])', lambda m: CODESPEC[m.group(1)], s)

TEXTSPEC = {
    '\\': r'\textbackslash{}', '%': r'\%', '#': r'\#', '&': r'\&',
    '_': r'\_', '$': r'\$', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
    '<': r'\textless{}', '>': r'\textgreater{}',
}

def esc_text(s):
    # 只转义“裸”反斜杠（后面不紧跟字母），保护已生成的 \textbf/\emph 等命令
    s = re.sub(r'\\(?![A-Za-z])', r'\\textbackslash{}', s)
    s = re.sub(r'([#$%&~^<>])', lambda m: TEXTSPEC[m.group(1)], s)
    s = re.sub(r'(?<!\\)_', r'\\_', s)
    return s

def emph_pass(t):
    t = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', t)
    t = re.sub(r'__(.+?)__', r'\\textbf{\1}', t)
    t = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)', r'\\emph{\1}', t)
    t = re.sub(r'(?<!\w)_(?!\w)([^_]+?)_(?!\w)', r'\\emph{\1}', t)
    return t

# ---- 行内转换 ------------------------------------------------------------
def protect_texmath(text, tok):
    """原书 md 里的 \\( \\) 只是被转义的普通圆括号（如 O\\(log\\(n\\)\\)），
    并非数学公式，这里按字面还原成 ( )。"""
    return text.replace('\\(', '(').replace('\\)', ')')

def inline(text):
    tok = {}
    # md 里直接写的 \(...\) 先原样保住
    text = protect_texmath(text, tok)
    # 去掉 Markdown 删除线标记 ~~…~~（本书用它标记过时内容，排版时只保留文字）
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    # 先处理图片（含行内图片，如列表项末尾的插图），避免被当成链接
    def img_repl(m):
        k = f"IMGT{len(tok)}"
        path = norm_img_path(m.group(2))
        cap = m.group(1).strip()
        tok[k] = r'\myGraphic{0.9}{' + path + '}{' + (inline(cap) if cap else '') + '}'
        return k
    text = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)', img_repl, text)

    def code_repl(m):
        k = f"CODE{len(tok)}"
        tok[k] = r'\texttt{' + esc_code(m.group(1)) + '}'
        return k
    text = re.sub(r'`([^`]+)`', code_repl, text)

    def math_repl(m):
        k = f"MATH{len(tok)}"
        tok[k] = r'\(' + m.group(1) + r'\)'
        return k
    text = re.sub(r'(?<!\$)\$(?!\$)([^\$\n]+?)\$', math_repl, text)

    def link_repl(m):
        t = m.group(1)
        url = m.group(2)
        url_e = re.sub(r'([#%&])', lambda x: '\\' + x.group(1), url)
        k = f"LINK{len(tok)}"
        # 链接文字同样要做转义（否则 std::is_sorted 里的 _ 会触发 Missing $）
        tok[k] = r'\href{' + url_e + '}{' + esc_text(emph_pass(t)) + '}'
        return k
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_repl, text)

    def bare_repl(m):
        url = m.group(1)
        url_e = re.sub(r'([#%&])', lambda x: '\\' + x.group(1), url)
        k = f"LINK{len(tok)}"
        tok[k] = r'\texthref{' + url_e + '}'
        return k
    text = re.sub(r'(?<!\()(https?://[^\s)\]<>]+)', bare_repl, text)

    # 脚注引用（原书 md 少见，直接丢弃）
    text = re.sub(r'\[\^[^\]]+\]', '', text)

    text = emph_pass(text)
    # Markdown 的转义星号 \*
    text = text.replace('\\*', '*')
    text = esc_text(text)

    if tok:
        pat = re.compile('|'.join(re.escape(k) for k in tok))
        text = pat.sub(lambda m: tok[m.group(0)], text)
    return text

# ---- 段落（多行合并 + CJK 间空格清理 + 行内） -----------------------------
CJK = r'[\u4e00-\u9fff\u3400-\u4dbf]'
def paragraph_latex(lines):
    paras, cur = [], []
    for l in lines:
        if l.strip() == '':
            if cur:
                paras.append(cur); cur = []
        else:
            cur.append(l.strip())
    if cur:
        paras.append(cur)
    out = []
    for p in paras:
        text = ' '.join(p)
        text = re.sub(r'(?<=' + CJK + r')\s+(?=' + CJK + r')', '', text)
        text = re.sub(r'\s{2,}', ' ', text)
        if text.strip():
            out.append(inline(text))
    return '\n\\par\n'.join(out)

# ---- 行判定 --------------------------------------------------------------
def indent_of(line):
    return len(line) - len(line.lstrip(' '))

def is_list_line(line):
    return re.match(r'^\s*([-*+]|\d+[.)])\s+', line) is not None

def list_match(line):
    m = re.match(r'^(\s*)([-*+]|\d+[.)])\s+(.*)$', line)
    if not m:
        return None
    return indent_of(line), m.group(2), m.group(3)

def is_separator(line):
    s = line.strip()
    return ('|' in s) and (set(s) <= set('|-: '))

def display_width(s):
    """粗略估算单元格显示宽度：CJK 字符记 2，其余记 1。"""
    s = re.sub(r'`([^`]*)`', r'\1', s)
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)
    s = s.replace('**', '').replace('*', '')
    return sum(2 if re.match(CJK, ch) else 1 for ch in s)

def split_row(line):
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|') and not s.endswith('\\|'):
        s = s[:-1]
    cells = re.split(r'(?<!\\)\|', s)
    return [c.strip().replace('\\|', '|') for c in cells]

IMG_RE = re.compile(r'^\s*!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+"[^"]*")?\s*\)\s*$')

def norm_img_path(p):
    """../../images/chapter1/1-6-1.png -> images/chapter1/1-6-1.png"""
    p = p.strip().replace('\\', '/')
    while p.startswith('../'):
        p = p[3:]
    if p.startswith('./'):
        p = p[2:]
    return p

def is_special(line):
    if line.strip() == '':
        return True
    if IMG_RE.match(line):
        return True
    if re.match(r'^#{1,6}\s+', line):
        return True
    if re.match(r'^\s*```', line):
        return True
    if line.lstrip().startswith('>'):
        return True
    if re.match(r'^\s*\|', line):
        return True
    if is_list_line(line):
        return True
    return False

# ---- 解析器 --------------------------------------------------------------
HEAD_MAP = {
    'front':         {'consume_h1': True,  'h2': r'\subsection',  'h3': r'\subsubsection', 'h4': r'\paragraph'},
    'chapter_intro': {'consume_h1': True,  'h2': r'\mySmallsection', 'h3': r'\mySmallsection', 'h4': r'\paragraph'},
    'recipe':        {'consume_h1': False, 'h2': r'\mySmallsection', 'h3': r'\mySmallsection', 'h4': r'\mySmallsection'},
}

class Parser:
    def __init__(self, lines, kind, first_h1_action):
        self.lines = lines
        self.n = len(lines)
        self.kind = kind
        self.i = 0
        self.first_h1_seen = (first_h1_action == 'none')

    def parse(self):
        head = HEAD_MAP[self.kind]
        out = []
        while self.i < self.n:
            line = self.lines[self.i]
            if line.strip() == '':
                self.i += 1
                continue

            m = IMG_RE.match(line)
            if m:
                self.i += 1
                path = norm_img_path(m.group(2))
                cap = m.group(1).strip()
                cap_tex = inline(cap) if cap else ''
                out.append(r'\myGraphic{0.9}{' + path + '}{' + cap_tex + '}')
                out.append('')
                continue

            m = re.match(r'^(#{1,6})\s+(.*)$', line)
            if m:
                lvl = len(m.group(1))
                title = inline(m.group(2).strip())
                self.i += 1
                if lvl == 1:
                    if head['consume_h1'] and not self.first_h1_seen:
                        self.first_h1_seen = True
                        continue
                    out.append(r'\section{' + title + '}')
                elif lvl == 2:
                    out.append(head['h2'] + '{' + title + '}')
                elif lvl == 3:
                    out.append(head['h3'] + '{' + title + '}')
                else:
                    out.append(head['h4'] + '{' + title + '}')
                out.append('')
                continue

            if re.match(r'^\s*```', line):
                fence = line.strip()
                lang = fence[3:].strip()
                self.i += 1
                buf = []
                while self.i < self.n and not re.match(r'^\s*```\s*$', self.lines[self.i]):
                    buf.append(self.lines[self.i])
                    self.i += 1
                if self.i < self.n:
                    self.i += 1
                L = LANGMAT.get(lang.lower(), lang.lower() or 'text')
                if not L:
                    L = 'text'
                out.append(r'\begin{codebox}[' + L + ']')
                # 先去掉整块共同的行首空格（minted autogobble 也是这么做的），
                # 再从第 0 列展开制表符：原始 md 里大量用 TAB 缩进，直接排 TAB 会出乱码
                body = '\n'.join(buf)
                blines = body.split('\n')
                inds = [len(l) - len(l.lstrip(' ')) for l in blines if l.strip()]
                common = min(inds) if inds else 0
                if common:
                    blines = [l[common:] if l.strip() else '' for l in blines]
                out.append('\n'.join(blines).expandtabs(4))
                out.append(r'\end{codebox}')
                out.append('')
                continue

            if line.lstrip().startswith('>'):
                buf = []
                while self.i < self.n and self.lines[self.i].lstrip().startswith('>'):
                    buf.append(re.sub(r'^\s*>\s?', '', self.lines[self.i]))
                    self.i += 1
                raw0 = buf[0].strip() if buf else ''
                s = raw0.replace('*', '').strip()
                box = 'myQuote'
                if re.match(r'^(Note|Tip|提示|注意|信息)', s, re.I):
                    box = 'myInfoBox'
                elif re.match(r'^(Warning|警告)', s, re.I):
                    box = 'myWarnBox'
                out.append(r'\begin{' + box + '}')
                out.append(paragraph_latex([b for b in buf if b.strip() != '']))
                out.append(r'\end{' + box + '}')
                out.append('')
                continue

            if re.match(r'^\s*\|', line) and self.i + 1 < self.n and is_separator(self.lines[self.i + 1]):
                header = split_row(line)
                self.i += 2
                rows = []
                while self.i < self.n and re.match(r'^\s*\|', self.lines[self.i]) and self.lines[self.i].strip() != '':
                    rows.append(split_row(self.lines[self.i]))
                    self.i += 1
                ncol = len(header)
                # 列宽：短列用 l（内容自适应），长列用 X（等分剩余宽度）
                allrows = [header] + rows
                widths = []
                for c in range(ncol):
                    w = 0
                    for r in allrows:
                        if c < len(r):
                            w = max(w, display_width(r[c]))
                    widths.append(w)
                spec = ''.join('l' if w <= 24 else 'X' for w in widths)
                if 'X' not in spec:
                    spec = spec[:-1] + 'X'
                out.append(r'\begin{table}[htbp]\centering')
                out.append(r'\begin{tabularx}{\textwidth}{' + spec + '}')
                out.append(r'\toprule')
                out.append(' & '.join(inline(c) for c in header) + r' \\')
                out.append(r'\midrule')
                for r in rows:
                    r = r + [''] * (ncol - len(r))
                    out.append(' & '.join(inline(c) for c in r[:ncol]) + r' \\')
                out.append(r'\bottomrule')
                out.append(r'\end{tabularx}')
                out.append(r'\end{table}')
                out.append('')
                continue

            if is_list_line(line):
                out.extend(self.parse_list())
                out.append('')
                continue

            # 普通段落
            buf = []
            while self.i < self.n and self.lines[self.i].strip() != '' and not is_special(self.lines[self.i]):
                buf.append(self.lines[self.i])
                self.i += 1
            if buf:
                out.append(paragraph_latex(buf))
                out.append('')
        return out

    def parse_list(self):
        out = []
        base = None
        items = []
        while self.i < self.n:
            line = self.lines[self.i]
            if line.strip() == '':
                j = self.i + 1
                while j < self.n and self.lines[j].strip() == '':
                    j += 1
                if j < self.n and is_list_line(self.lines[j]) and (base is None or indent_of(self.lines[j]) >= base):
                    self.i = j
                    continue
                else:
                    break
            mm = list_match(line)
            if not mm:
                break
            ind, marker, cont = mm
            if base is None:
                base = ind
            if ind < base:
                break
            if ind > base:
                items[-1]['body'].append(line)
                self.i += 1
                continue
            items.append({'marker': marker, 'body': [cont]})
            self.i += 1
            while self.i < self.n:
                bl = self.lines[self.i]
                if bl.strip() == '':
                    j = self.i + 1
                    while j < self.n and self.lines[j].strip() == '':
                        j += 1
                    if j < self.n and (indent_of(self.lines[j]) > base or (is_list_line(self.lines[j]) and indent_of(self.lines[j]) > base)):
                        items[-1]['body'].append(bl)
                        self.i += 1
                        continue
                    else:
                        break
                bm = list_match(bl)
                if bm and bm[0] > base:
                    items[-1]['body'].append(bl)
                    self.i += 1
                    continue
                if bm and bm[0] <= base:
                    break
                # 非列表、非空行：indent>base 属于条目体；<=base 视为条目续行
                items[-1]['body'].append(bl)
                self.i += 1
        if not items:
            return []
        is_enum = bool(re.match(r'\d+[.)]', items[0]['marker']))
        env = 'enumerate' if is_enum else 'itemize'
        out.append(f'\\begin{{{env}}}')
        for it in items:
            body = [b for b in it['body'] if b.strip() != '']
            if body:
                body_tex = parse_blocks(body, self.kind, 'none')
                if body_tex and not body_tex[0].startswith('\\begin'):
                    out.append('\\item ' + body_tex[0])
                    out.extend(body_tex[1:])
                else:
                    out.append('\\item')
                    out.extend(body_tex)
            else:
                out.append('\\item')
        out.append(f'\\end{{{env}}}')
        return out

def parse_blocks(lines, kind, first_h1_action):
    return Parser(lines, kind, first_h1_action).parse()

# ---- 文件级处理 ----------------------------------------------------------
def read_file(path):
    with open(path, encoding='utf-8') as f:
        return f.read().splitlines()

def extract_first_h1(text):
    for line in text.splitlines():
        m = re.match(r'^#\s+(.*)$', line)
        if m:
            return m.group(1).strip()
    return None

def strip_chapter_prefix(title):
    m = re.match(r'^第\s*(\d+)\s*章\s*(.*)$', title)
    if m:
        return int(m.group(1)), m.group(2).strip()
    return None, title

def process_file(path, kind):
    text = open(path, encoding='utf-8').read()
    title = extract_first_h1(text)
    lines = text.splitlines()
    latex = parse_blocks(lines, kind, 'consume' if HEAD_MAP[kind]['consume_h1'] else 'emit')
    return title, '\n'.join(latex)

# 前言/关于本书/各章梗概
FRONT_FILES = [
    ("preface/preface-chinese.md", "front/preface"),
    ("preface/about-this-book-chinese.md", "front/about"),
    ("preface/chapters-summary-chinese.md", "front/chapters-summary"),
]

# 个别前言页内容比版心多出一两行，会把孤行挤到下一页；用 \enlargethispage 就地撑高版心
FRONT_EXTRA = {
    "front/chapters-summary": r"\enlargethispage{\baselineskip}",
}

def get_chapter_files(ch):
    d = os.path.join(SRC, f"chapter{ch}")
    intro = None
    recipes = []
    for f in sorted(os.listdir(d)):
        if not f.endswith('.md'):
            continue
        m = re.match(rf'chapter{ch}-(\d+)-chinese\.md', f)
        if not m:
            continue
        k = int(m.group(1))
        if k == 0:
            intro = f
        else:
            recipes.append((k, f))
    recipes.sort()
    return intro, recipes

def build_front():
    pages = []
    for rel, outrel in FRONT_FILES:
        path = os.path.join(SRC, rel)
        title, latex = process_file(path, 'front')
        if title is None:
            title = outrel.split('/')[-1]
        outpath = os.path.join(CONTENT, outrel + '.tex')
        extra = FRONT_EXTRA.get(outrel)
        if extra:
            latex = extra + '\n' + latex
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(latex + '\n')
        pages.append((title, outrel))
        print(f"  front  -> {outrel}.tex  (title={title})")
    return pages

def build_chapters(chapters):
    chapter_titles = {}
    for ch in chapters:
        intro, recipes = get_chapter_files(ch)
        if intro is None:
            print(f"  !! chapter{ch} 缺少导言文件")
            continue
        intro_text = open(os.path.join(SRC, f"chapter{ch}", intro), encoding='utf-8').read()
        num, ch_title = strip_chapter_prefix(extract_first_h1(intro_text) or f"第{ch}章")
        if num is None:
            num = ch
        chapter_titles[ch] = ch_title
        # 导言 body（去掉首个 # 行）
        intro_lines = intro_text.splitlines()
        intro_latex = parse_blocks(intro_lines, 'chapter_intro', 'consume')
        parts = [r'% chapterintro']
        parts.append('% ' + '=' * 30)
        parts.append(f'% 第{ch}章 导言：{intro}')
        parts.extend(intro_latex)
        parts.append('')
        for k, f in recipes:
            rpath = os.path.join(SRC, f"chapter{ch}", f)
            rtext = open(rpath, encoding='utf-8').read()
            rlatex = parse_blocks(rtext.splitlines(), 'recipe', 'emit')
            parts.append(f'% --- recipe {k}: {f} ---')
            parts.extend(rlatex)
            parts.append('')
        outpath = os.path.join(MAIN_D, f"chapter{ch}.tex")
        with open(outpath, 'w', encoding='utf-8') as fo:
            fo.write('\n'.join(parts) + '\n')
        print(f"  chapter {ch} -> chapter{ch}.tex  (title={ch_title}, recipes={len(recipes)})")
    return chapter_titles

def build_index(front_pages, chapter_titles, chapters):
    L = []
    L.append(r'\myFrontNoToc{content/front/00-cover}')   # 封面图（整页出血）
    L.append(r'\myFrontNoToc{content/front/00-title}')   # 文字扉页
    L.append('')
    L.append(r'\newpage')
    L.append(r'\thispagestyle{empty}')
    L.append(r'\tableofcontents')
    L.append(r'\newpage')
    L.append('')
    for title, fp in front_pages:
        L.append(r'\myFront{' + title + '}{content/' + fp + '}')
    L.append('')
    for ch in chapters:
        t = chapter_titles.get(ch, f"第{ch}章")
        L.append(r'\myChapter{' + str(ch) + '}{' + t + '}{content/main/chapter' + str(ch) + '}')
    L.append('')
    with open(os.path.join(BOOK_D, 'index.tex'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print("  index.tex written")

def build_cover():
    """封面页：原书封面 cover.jpg 整页出血铺满。

    成品页 531.36×628.83bp（宽高比 0.845），原图 1422×1751（0.812），
    等比放大到版心宽后高度多出约 25.6bp —— 用 overlay + clip 居中裁掉
    上下各约 12.8bp（约占图高 2%，不触及橙色作者条与 Packt 标识）。
    """
    tex = r'''% book/content/front/00-cover.tex —— 封面（原书封面整页出血，改图请替换 images/cover.jpg）
\thispagestyle{empty}
\begin{tikzpicture}[remember picture, overlay]
  \begin{scope}
    % 裁剪区 = 整页，超出的部分被切掉，保证四边无白边
    \clip (current page.south west) rectangle (current page.north east);
    \node[anchor=center, inner sep=0pt] at (current page.center)
      {\includegraphics[width=\paperwidth]{images/cover.jpg}};
  \end{scope}
\end{tikzpicture}%
\clearpage
'''
    with open(os.path.join(CONTENT, 'front', '00-cover.tex'), 'w', encoding='utf-8') as f:
        f.write(tex)
    print("  cover 00-cover.tex written")

def build_title():
    tex = r'''% book/content/front/00-title.tex —— 封面（Manning 风格，需两遍编译）
\thispagestyle{empty}
\begingroup
\centering
\vspace*{1.6cm}
{\sffamily\fontsize{34bp}{40bp}\selectfont\bfseries\color{chapterblue} C++17 STL Cookbook\par}
\vspace{10bp}
{\fontsize{16bp}{22bp}\selectfont C++17 STL 库实战手册\par}
\vspace{2bp}
{\fontsize{12bp}{17bp}\selectfont 中文翻译版\par}

\vspace{36bp}
{\fontsize{14bp}{20bp}\selectfont Jacek Galowicz\quad 著\par}
\vspace{6bp}
{\fontsize{14bp}{20bp}\selectfont 陈晓伟\quad 译\par}

\vfill
{%
  \color{chapterblue}\rule{0.62\textwidth}{1.4bp}\par
}
\vspace{10bp}
{\fontsize{11bp}{15bp}\selectfont 基于 Manning 风格 \LaTeX{} 模版排版\par}
\endgroup
'''
    with open(os.path.join(CONTENT, 'front', '00-title.tex'), 'w', encoding='utf-8') as f:
        f.write(tex)
    print("  cover 00-title.tex written")

def patch_ccs():
    src = os.path.join("D:/Ego/trans/C++ Initialization Story/latex_source/book/ccs.tex")
    dst = os.path.join(BOOK_D, 'ccs.tex')
    t = open(src, encoding='utf-8').read()
    t = t.replace(
        "  pdftitle={C++ 初始化全解},\n"
        "  pdfauthor={Bartłomiej Filipek},\n"
        "  pdfsubject={C++ Initialization Story 中文版：遍历所有初始化选项与相关 C++ 领域},\n"
        "  pdfkeywords={C++, 初始化, 构造函数, 拷贝, 移动, 聚合, 指定初始化器, NSDMI},",
        "  pdftitle={C++17 STL Cookbook 中文版},\n"
        "  pdfauthor={Jacek Galowicz / 陈晓伟},\n"
        "  pdfsubject={C++17 STL Cookbook 中文翻译版：使用标准库编写更优秀的 C++17 代码},\n"
        "  pdfkeywords={C++, STL, C++17, 标准库, 容器, 算法, 迭代器, Lambda, 并发, 文件系统},",
    )
    # —— 本书插图均无图注：让 \myGraphic 的第三参数为空时跳过图注行，避免多余空行
    cap_new = (
        "  \\nopagebreak\n"
        "  \\tl_if_blank:nF {#3}\n"
        "   {\n"
        "    \\vspace{3bp}\\noindent\n"
        "    {\\fontsize{8bp}{10.5bp}\\selectfont\n"
        "     \\ifmyGraphicCapBold\\bfseries\\fi\n"
        "     \\ifmyGraphicCapCenter\n"
        "       \\parbox{\\textwidth}{\\centering #3}%\n"
        "     \\else\n"
        "       \\hspace*{-\\myGraphicCapHang}\\parbox{\\dimexpr\\textwidth+\\myGraphicCapHang\\relax}{#3}%\n"
        "     \\fi}\\par\n"
        "   }\n"
        "  \\medskip"
    )
    cap_re = re.compile(
        r'  \\nopagebreak\\vspace\{3bp\}\\noindent\n'
        r'  \{\\fontsize\{8bp\}\{10\.5bp\}\\selectfont\n'
        r'.*?\\par\n'
        r'  \\medskip', re.S)
    t, ncap = cap_re.subn(lambda m: cap_new, t, count=1)
    if ncap == 0:
        print("  !! 警告：\\myGraphic 空图注补丁未匹配")

    # —— 章标记必须在 \chapter*（其内部 \clearpage）之后写，
    #    否则上一页溢出的一两行会被打上下一章的页眉（模板原写法有此瑕疵）
    old_chap = (
        "  \\chapmark{第~#1~章\\quad \\l__my_toctitle_tl}%  \\chapter* 不触发 \\chaptermark，必须自己写标记\n"
        "  \\chapter*{#2}\n"
    )
    new_chap = (
        "  \\chapter*{#2}\n"
        "  \\chapmark{第~#1~章\\quad \\l__my_toctitle_tl}%  \\chapter* 不触发 \\chaptermark，必须自己写标记\n"
    )
    if old_chap in t:
        t = t.replace(old_chap, new_chap)
    else:
        print("  !! 警告：\\myChapter 页眉标记顺序补丁未匹配")
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(t)
    print("  ccs.tex copied + metadata patched")

MINIMAL_BAT = r'''@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ============================================================================
REM  One-click build  (Windows / TeX Live 2026 + latexminted)
REM
REM    build.bat        3 passes of xelatex, then delete the *.minted cache
REM    build.bat keep   3 passes of xelatex, keep the cache (faster rebuilds)
REM
REM  NOTE: latexminted caches every highlighted code listing as
REM        <hash>.highlight.minted (~1000 files for this book). Keeping them
REM        makes a rebuild take ~2 min/pass instead of ~20 min for pass 1.
REM ============================================================================
set TEXBIN=D:\ProgramData\texlive\2026\bin\windows
set PYTHON=D:\anaconda3
set "PATH=%PYTHON%;%TEXBIN%;%PATH%"
set "PYTHONPATH="
for %%A in ("%~dp0.") do set "TEXMF_OUTPUT_DIRECTORY=%%~fA"
set "TEXMFOUTPUT=%TEXMF_OUTPUT_DIRECTORY%"
cd /d "%~dp0."

xelatex -shell-escape -interaction=nonstopmode -synctex=1 main.tex
if errorlevel 1 goto :err
xelatex -shell-escape -interaction=nonstopmode -synctex=1 main.tex
if errorlevel 1 goto :err
xelatex -shell-escape -interaction=nonstopmode -synctex=1 main.tex
if errorlevel 1 goto :err

echo.
echo Build finished. Output: main.pdf

REM ---------------------------------------------------------------------------
REM  Clean the minted cache (skip with: build.bat keep)
REM ---------------------------------------------------------------------------
if /i "%~1"=="keep" (
    echo minted cache kept.
    goto :done
)

set N=0
if exist "*.minted" (
    for %%F in ("*.minted") do (
        del /q "%%~fF" >nul 2>&1
        if not exist "%%~fF" set /a N+=1
    )
)
if exist "main.listing" del /q "main.listing" >nul 2>&1
echo Cleaned !N! minted cache file^(s^).
goto :done

:err
echo.
echo Build FAILED. See main.log
echo minted cache kept for debugging.
pause

:done
endlocal
'''

def build_main_and_bat():
    main_tex = r'''% ============================================================
%  main.tex —— C++17 STL Cookbook 中文版编译入口
%  编译：xelatex -shell-escape -interaction=nonstopmode main.tex（两遍）
% ============================================================
\input{book/ccs.tex}

\begin{document}
\subfile{book/index.tex}
\end{document}
'''
    with open(os.path.join(DST, 'main.tex'), 'w', encoding='utf-8') as f:
        f.write(main_tex)

    # build.bat 是手工维护的构建脚本：已存在就不覆盖，缺失时写一份骨架
    bpath = os.path.join(DST, 'build.bat')
    if not os.path.exists(bpath):
        data = MINIMAL_BAT.replace('\n', '\r\n').encode('ascii')
        with open(bpath, 'wb') as f:
            f.write(data)
        print("  build.bat written (minimal)")
    else:
        print("  build.bat kept (hand-maintained)")

def main():
    only = None
    for a in sys.argv[1:]:
        if a.startswith('--chapter'):
            only = int(a.split('=')[1]) if '=' in a else int(sys.argv[sys.argv.index(a) + 1])
    os.makedirs(FRONT_D, exist_ok=True)
    os.makedirs(MAIN_D, exist_ok=True)
    os.makedirs(BOOK_D, exist_ok=True)

    patch_ccs()
    build_main_and_bat()
    build_cover()
    build_title()
    front_pages = build_front()

    if only is not None:
        chapters = [only]
    else:
        chapters = list(range(1, 11))
    chapter_titles = build_chapters(chapters)
    build_index(front_pages, chapter_titles, chapters)
    print("DONE.")

if __name__ == '__main__':
    main()
