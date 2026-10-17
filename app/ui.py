# tkinter 화면. Figma "Compact · KO/EN"(780x600), "Log · KO/EN" 프레임을 따른다.
import ctypes
import queue
import re
import threading
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime

from i18n import LANGS, STRINGS, default_lang

# Figma "Tokens" 컬렉션과 같은 이름/값
C = {
    'bg': '#F5F6F8', 'surface': '#FFFFFF', 'border': '#E4E7EC',
    'text': '#101828', 'text-muted': '#667085',
    'primary': '#2563EB', 'primary-soft': '#EFF4FF',
    'success': '#12B76A', 'success-soft': '#ECFDF3',
    'warning': '#DC6803', 'warning-soft': '#FFFAEB',
    'danger': '#D92D20', 'danger-soft': '#FEF3F2',
    'on-primary': '#FFFFFF', 'log-bg': '#0F172A', 'log-text': '#CBD5E1',
}

WIDTH, HEIGHT = 780, 600

# 화면 배율(DPI). Tk() 를 만든 뒤 setup() 에서 정한다
SCALE = 1.0
F = {}


def px(n):
    return max(1, round(n * SCALE))


def blend(fg, bg, alpha):
    a = [int(fg[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(bg[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x * alpha + y * (1 - alpha)):02X}' for x, y in zip(a, b))


def darken(color):
    return blend(color, '#000000', 0.96)


def setup(root):
    global SCALE
    SCALE = root.winfo_fpixels('1i') / 96
    families = set(tkfont.families(root))
    sans = next((f for f in ('Noto Sans KR', '맑은 고딕', 'Malgun Gothic', 'Segoe UI') if f in families), 'TkDefaultFont')
    medium = f'{sans} Medium' if f'{sans} Medium' in families else sans
    mono = next((f for f in ('JetBrains Mono', 'Cascadia Mono', 'Consolas') if f in families), 'TkFixedFont')
    sizes = {
        'title': (sans, 16, 'bold'), 'subtitle': (sans, 12, 'normal'), 'small': (sans, 12, 'normal'),
        'hero': (sans, 18, 'bold'), 'h2': (sans, 15, 'bold'), 'dialog': (sans, 19, 'bold'),
        'body': (sans, 13, 'normal'), 'value': (medium, 13, 'normal' if medium != sans else 'bold'),
        'button': (medium, 14, 'normal'), 'segment': (sans, 13, 'normal'), 'segment-on': (medium, 13, 'normal'),
        'badge': (medium, 12, 'normal'), 'text': (sans, 14, 'normal'), 'mono': (mono, 12, 'normal'),
    }
    for name, (family, size, weight) in sizes.items():
        F[name] = tkfont.Font(root, family=family, size=-px(size), weight=weight)


# Galaxy Connect 로그 한 줄을 "HH:MM:SS  메시지" 로 줄인다
# 원본 형식: "2026-10-17 12:18:49.9426 [INFO] [P:.. | T:..] [File.cs::Method (56)] \t메시지"
def short_log(line):
    m = re.match(r'^\S+ (\d\d:\d\d:\d\d)', line)
    message = line[line.rfind('\t') + 1:] if '\t' in line else re.sub(r'^.*\]\s+', '', line)
    return f'{m.group(1)}  {message.strip()[:120]}' if m else line


def is_samsung(v):
    return 'samsung' in (v or '').lower()


def hero_state(status, error):
    if error:
        return 'error'
    if not status:
        return None
    if not status.get('GalaxyConnect'):
        return 'notInstalled'
    if (status.get('Detection') or {}).get('IsSamsungDevice'):
        return 'ready'
    if is_samsung((status.get('AppSees') or {}).get('Manufacturer')):
        return 'launch'
    return 'notApplied'


def rounded_rect(c, w, h, r, fill, outline):
    x2, y2, d = w - 1, h - 1, 2 * r
    corners = ((0, 0, 90), (x2 - d, 0, 0), (x2 - d, y2 - d, 270), (0, y2 - d, 180))
    for x, y, start in corners:
        c.create_arc(x, y, x + d, y + d, start=start, extent=90, fill=fill, outline=fill)
    c.create_rectangle(r, 0, x2 - r, y2, fill=fill, outline=fill)
    c.create_rectangle(0, r, x2, y2 - r, fill=fill, outline=fill)
    if outline != fill:
        for x, y, start in corners:
            c.create_arc(x, y, x + d, y + d, start=start, extent=90, style='arc', outline=outline)
        for line in ((r, 0, x2 - r, 0), (r, y2, x2 - r, y2), (0, r, 0, y2 - r), (x2, r, x2, y2 - r)):
            c.create_line(*line, fill=outline)


class Box(tk.Frame):
    """둥근 모서리 상자. 내용은 self.inner 에 넣는다. 모서리가 보이도록 pad 는 반지름의 절반 이상으로 준다."""

    def __init__(self, parent, fill, radius, pad=(0, 0), border=None):
        super().__init__(parent, bg=parent['bg'])
        self.fill, self.border, self.radius = fill, border, px(radius)
        self.canvas = tk.Canvas(self, bg=parent['bg'], highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.inner = tk.Frame(self, bg=fill)
        self.inner.pack(fill='both', expand=True, padx=px(pad[0]), pady=px(pad[1]))
        self.bind('<Configure>', lambda e: self.draw())

    def draw(self):
        self.canvas.delete('all')
        w, h = self.winfo_width(), self.winfo_height()
        rounded_rect(self.canvas, w, h, min(self.radius, w // 2, h // 2), self.fill, self.border or self.fill)

    def recolor(self, fill, border=None):
        self.fill, self.border = fill, border
        self.inner['bg'] = fill
        self.draw()


class Icon(tk.Canvas):
    """앱 아이콘(24x24 기준 SVG 경로를 선으로 옮긴 것)."""

    def __init__(self, parent, name, size):
        super().__init__(parent, width=px(size), height=px(size), bg=parent['bg'], highlightthickness=0, bd=0)
        k = px(size) / 24
        line = lambda pts, color, w: self.create_line(*[v * k for v in pts], fill=color, width=w * k, capstyle='round', joinstyle='round')
        if name == 'link':
            blue, w = C['primary'], 2.2
            self.create_arc(2 * k, 7 * k, 12 * k, 17 * k, start=90, extent=180, style='arc', outline=blue, width=w * k)
            self.create_arc(12 * k, 7 * k, 22 * k, 17 * k, start=-90, extent=180, style='arc', outline=blue, width=w * k)
            for pts in ((7, 7, 9, 7), (7, 17, 9, 17), (15, 7, 17, 7), (15, 17, 17, 17), (8, 12, 16, 12)):
                line(pts, blue, w)
        elif name == 'check':
            line((20, 6, 9, 17, 4, 12), C['success'], 2.4)
        elif name == 'play':
            line((7, 5, 7, 19, 18, 12, 7, 5), C['primary'], 2)
        elif name == 'warning':
            line((12, 3.5, 22, 20.5, 2, 20.5, 12, 3.5), C['warning'], 2)
            line((12, 9, 12, 13), C['warning'], 2)
            line((12, 17, 12, 17.1), C['warning'], 2)


class Button(Box):
    """Figma: Button / Type=Primary|Secondary|Danger"""
    STYLES = {
        'primary': ('primary', 'on-primary', None),
        'secondary': ('surface', 'text', 'border'),
        'danger': ('danger-soft', 'danger', None),
    }

    def __init__(self, parent, text, command, kind='secondary', disabled=False):
        fill, fg, border = (C[k] if k else None for k in self.STYLES[kind])
        self.colors, self.page = (fill, fg, border), parent['bg']
        super().__init__(parent, fill, 10, pad=(18, 8), border=border)
        self.command, self.disabled, self.hover = command, disabled, False
        self.label = tk.Label(self.inner, text=text, bg=fill, fg=fg, font=F['button'])
        self.label.pack(expand=True)
        for w in (self.canvas, self.inner, self.label):
            w.bind('<Button-1>', self.click)
            w.bind('<Enter>', lambda e: self.set_hover(True))
            w.bind('<Leave>', lambda e: self.set_hover(False))
        self.style()

    def click(self, _event):
        # 화면을 다시 그리면 이 버튼이 지워지므로 이벤트 처리가 끝난 뒤 실행한다
        if not self.disabled:
            self.after_idle(self.command)

    def set_hover(self, on):
        self.hover = on
        self.style()

    def set_disabled(self, disabled):
        self.disabled = disabled
        self.style()

    def style(self):
        fill, fg, border = self.colors
        if self.disabled:
            fill, fg = blend(fill, self.page, 0.55), blend(fg, self.page, 0.55)
            border = border and blend(border, self.page, 0.55)
        elif self.hover:
            fill = darken(fill)
        self.label.config(bg=fill, fg=fg)
        cursor = 'arrow' if self.disabled else 'hand2'
        for w in (self.canvas, self.inner, self.label):
            w['cursor'] = cursor
        self.recolor(fill, border)


class Badge(Box):
    """Figma: Badge / Tone=Success|Warning|Neutral"""
    TONES = {'success': ('success-soft', 'success'), 'warning': ('warning-soft', 'warning'), 'neutral': ('bg', 'text-muted')}

    def __init__(self, parent, tone, text):
        fill, fg = (C[k] for k in self.TONES[tone])
        super().__init__(parent, fill, 999, pad=(10, 2))
        dot = tk.Canvas(self.inner, width=px(6), height=px(6), bg=fill, highlightthickness=0, bd=0)
        dot.create_oval(0, 0, px(6) - 1, px(6) - 1, fill=fg, outline=fg)
        dot.pack(side='left', padx=(0, px(6)))
        tk.Label(self.inner, text=text, bg=fill, fg=fg, font=F['badge']).pack(side='left')


def label(parent, text, font, fg='text', **kw):
    return tk.Label(parent, text=text, font=F[font], fg=C[fg], bg=parent['bg'], **kw)


def wrap_label(parent, text, font, fg='text', width=200):
    """부모 폭에 맞춰 줄바꿈하는 글자. 처음 요청 폭이 창을 넓히지 않도록 작게 시작한다."""
    l = label(parent, text, font, fg, justify='left', anchor='w', wraplength=px(width))
    l.bind('<Configure>', lambda e: l.config(wraplength=e.width))
    return l


def info_row(parent, name, value):
    """Figma: InfoRow. value 는 글자 또는 Badge 를 만드는 함수."""
    row = tk.Frame(parent, bg=parent['bg'], height=px(44))
    row.pack_propagate(False)
    row.pack(fill='x')
    tk.Frame(row, bg=C['border'], height=1).pack(side='bottom', fill='x')
    label(row, name, 'body', 'text-muted').pack(side='left', padx=(px(4), 0))
    if callable(value):
        value(row).pack(side='right', padx=(0, px(4)))
    else:
        label(row, value, 'value').pack(side='right', padx=(0, px(4)))


class Dialog(tk.Toplevel):
    def __init__(self, root, title, width, on_close):
        super().__init__(root, bg=C['surface'])
        self.withdraw()
        self.title(title)
        self.transient(root)
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', on_close)
        self.body = tk.Frame(self, bg=C['surface'], width=px(width))
        self.body.pack(fill='both', expand=True, padx=px(24), pady=px(24))
        # 내용이 좁아도 디자인 폭을 지킨다
        tk.Frame(self.body, bg=C['surface'], width=px(width - 48), height=0).pack()

    def show(self):
        # 내용을 다 넣은 뒤 부모 창 가운데에 띄우고 다른 창을 막는다
        self.update_idletasks()
        root = self.master
        x = root.winfo_rootx() + (root.winfo_width() - self.winfo_reqwidth()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f'+{max(x, 0)}+{max(y, 0)}')
        self.deiconify()
        self.grab_set()
        self.focus_set()

    def actions(self):
        row = tk.Frame(self.body, bg=C['surface'])
        row.pack(fill='x', pady=(px(16), 0))
        return row


class ConsentDialog(Dialog):
    def __init__(self, root, s, on_accept, on_quit):
        c = s['consent']
        super().__init__(root, c['title'], 520, on_quit)
        text_w = 520 - 48
        ring = Box(self.body, C['warning-soft'], 22, pad=(10, 10))
        Icon(ring.inner, 'warning', 24).pack()
        ring.pack(anchor='w')
        label(self.body, c['title'], 'dialog').pack(anchor='w', pady=(px(16), px(12)))
        for i, point in enumerate(c['points']):
            row = tk.Frame(self.body, bg=C['surface'])
            row.pack(fill='x', pady=(0, px(10)))
            key = i == 1
            label(row, '•', 'value', 'danger' if key else 'text-muted').pack(side='left', anchor='n', padx=(0, px(10)))
            label(row, point, 'value' if key else 'text', 'text' if key else 'text-muted',
                  justify='left', wraplength=px(text_w - 24)).pack(side='left', anchor='w')
        self.agreed = False
        agree = Box(self.body, C['primary-soft'], 10, pad=(14, 10))
        agree.pack(fill='x', pady=(px(6), 0))
        # Tk 의 Checkbutton 표시는 화면 배율을 따르지 않아 직접 그린다
        self.check = tk.Canvas(agree.inner, width=px(18), height=px(18), bg=C['primary-soft'], highlightthickness=0, bd=0)
        self.check.pack(side='left', padx=(0, px(10)))
        text = label(agree.inner, c['agree'], 'value')
        text.pack(side='left')
        for w in (agree.canvas, agree.inner, self.check, text):
            w['cursor'] = 'hand2'
            w.bind('<Button-1>', lambda e: self.toggle())
        row = self.actions()
        self.start = Button(row, c['start'], on_accept, 'primary', disabled=True)
        self.start.pack(side='right')
        Button(row, c['quit'], on_quit).pack(side='right', padx=(0, px(8)))
        self.draw_check()
        self.show()

    def toggle(self):
        self.agreed = not self.agreed
        self.draw_check()
        self.start.set_disabled(not self.agreed)

    def draw_check(self):
        c, n = self.check, px(18)
        c.delete('all')
        rounded_rect(c, n, n, px(4), C['primary'] if self.agreed else C['surface'], C['primary'] if self.agreed else C['text-muted'])
        if self.agreed:
            k = n / 24
            c.create_line(19 * k, 7 * k, 10 * k, 17 * k, 5 * k, 12 * k, fill=C['on-primary'], width=2.6 * k, capstyle='round', joinstyle='round')


class ConfirmDialog(Dialog):
    def __init__(self, root, s, action, on_cancel, on_ok):
        title, body = s['confirm'][action]
        super().__init__(root, title, 480, on_cancel)
        label(self.body, title, 'dialog').pack(anchor='w', pady=(0, px(12)))
        label(self.body, body, 'text', 'text-muted', justify='left', wraplength=px(480 - 48)).pack(anchor='w')
        row = self.actions()
        Button(row, s['confirm']['ok'], on_ok, 'danger' if action == 'restore' else 'primary').pack(side='right')
        Button(row, s['confirm']['cancel'], on_cancel).pack(side='right', padx=(0, px(8)))
        self.show()


class LogDialog(Dialog):
    """Figma: Log · KO/EN. 작업이 실행되는 동안 열어 두면 줄이 계속 추가된다."""

    def __init__(self, root, s, lines, on_close):
        super().__init__(root, s['log'], 640, on_close)
        self.empty = s['log_empty']
        label(self.body, s['log'], 'dialog').pack(anchor='w', pady=(0, px(14)))
        frame = tk.Frame(self.body, bg=C['surface'], width=px(640 - 48), height=px(300))
        frame.pack_propagate(False)
        frame.pack()
        panel = Box(frame, C['log-bg'], 12, pad=(8, 8))
        panel.pack(fill='both', expand=True)
        self.text = tk.Text(panel.inner, bg=C['log-bg'], fg=C['log-text'], font=F['mono'], bd=0, highlightthickness=0,
                            wrap='char', padx=px(8), pady=px(8), spacing3=px(4), cursor='arrow')
        self.text.pack(fill='both', expand=True)
        row = self.actions()
        Button(row, s['close'], on_close).pack(side='right')
        self.set_lines(lines)
        self.show()

    def set_lines(self, lines):
        self.text.config(state='normal')
        self.text.delete('1.0', 'end')
        self.text.insert('1.0', '\n'.join(lines) if lines else self.empty)
        self.text.config(state='disabled')
        self.text.see('end')


class App:
    def __init__(self, root, backend):
        self.root, self.backend = root, backend
        self.settings = backend.read_settings()
        self.status = self.error = self.checked_at = None
        self.loading = False
        self.busy = self.result = None
        self.action_log = []
        self.dialog = self.log_dialog = None
        self.frame = None
        self.events = queue.Queue()
        self.pump()
        self.render()
        if not self.settings.get('consented'):
            self.dialog = ConsentDialog(root, self.s, self.accept, root.destroy)
        self.refresh()

    @property
    def lang(self):
        return self.settings.get('lang') or default_lang()

    @property
    def s(self):
        return STRINGS[self.lang]

    # --- 백그라운드 작업. 결과는 큐를 거쳐 Tk 스레드에서 처리한다 ---
    def background(self, work, done):
        def run():
            try:
                result = (work(), None)
            except Exception as e:  # 화면에 오류로 보여 준다
                result = (None, e)
            self.events.put(lambda: done(*result))
        threading.Thread(target=run, daemon=True).start()

    def pump(self):
        while True:
            try:
                self.events.get_nowait()()
            except queue.Empty:
                break
        self.root.after(50, self.pump)

    # --- 동작 ---
    def update_settings(self, patch):
        self.settings = self.backend.write_settings(patch)
        self.render()

    def accept(self):
        self.close_dialog()
        self.update_settings({'consented': True, 'consentedAt': datetime.now().astimezone().isoformat()})

    def close_dialog(self):
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None

    def refresh(self):
        self.loading = True
        self.render()

        def done(status, error):
            if error:
                self.error = str(error)
            else:
                self.status, self.error = status, None
            self.checked_at = datetime.now()
            self.loading = False
            self.render()
        self.background(self.backend.get_status, done)

    def confirm(self, action):
        self.dialog = ConfirmDialog(self.root, self.s, action, self.close_dialog, lambda: self.run(action))

    def run(self, action):
        self.close_dialog()
        self.busy, self.result = action, None
        self.action_log = []
        self.update_log()
        self.render()

        def on_line(line):
            self.events.put(lambda: self.add_log(line))

        def done(r, error):
            self.busy = None
            # 작업이 끝났을 때 ERROR 줄이 있었는지도 본다
            failed = error or not r['ok'] or any(l.startswith('ERROR') for l in self.action_log)
            self.result = 'cancelled' if r and r['cancelled'] else 'failed' if failed else 'ok'
            if error:
                self.add_log(f'ERROR: {error}')
            self.refresh()
        self.background(lambda: self.backend.run_action(action, on_line), done)

    def add_log(self, line):
        self.action_log.append(line)
        self.update_log()

    def log_lines(self):
        return self.action_log or [short_log(l) for l in (self.status or {}).get('Log') or []]

    def update_log(self):
        if self.log_dialog:
            self.log_dialog.set_lines(self.log_lines())

    def open_log(self):
        self.log_dialog = LogDialog(self.root, self.s, self.log_lines(), self.close_log)

    def close_log(self):
        self.log_dialog.destroy()
        self.log_dialog = None

    # --- 화면. 상태가 바뀔 때마다 통째로 다시 그린다 ---
    def render(self):
        if self.frame:
            self.frame.destroy()
        s = self.s
        self.frame = page = tk.Frame(self.root, bg=C['bg'])
        page.pack(fill='both', expand=True)
        self.header(page, s)
        footer = tk.Frame(page, bg=C['bg'])
        footer.pack(side='bottom', fill='x', padx=px(20), pady=(0, px(14)))
        label(footer, s['footer'], 'small', 'text-muted').pack(side='left')
        label(footer, f'v{self.backend.VERSION}', 'small', 'text-muted').pack(side='right')

        body = tk.Frame(page, bg=C['bg'])
        body.pack(fill='both', expand=True, padx=px(16), pady=(px(16), px(12)))
        self.hero(body, s)
        cards = tk.Frame(body, bg=C['bg'])
        cards.pack(fill='x', pady=(px(12), 0))
        cards.columnconfigure(0, weight=1, uniform='card')
        cards.columnconfigure(1, weight=1, uniform='card')
        self.status_card(cards, s).grid(row=0, column=0, sticky='nsew', padx=(0, px(6)))
        self.actions_card(cards, s).grid(row=0, column=1, sticky='nsew', padx=(px(6), 0))

    def header(self, page, s):
        header = tk.Frame(page, bg=C['surface'])
        header.pack(fill='x')
        tk.Frame(page, bg=C['border'], height=1).pack(fill='x')
        inner = tk.Frame(header, bg=C['surface'])
        inner.pack(fill='x', padx=px(20), pady=px(14))
        logo = Box(inner, C['primary-soft'], 10, pad=(8, 8))
        Icon(logo.inner, 'link', 20).pack()
        logo.pack(side='left')
        titles = tk.Frame(inner, bg=C['surface'])
        titles.pack(side='left', fill='x', expand=True, padx=px(12))
        label(titles, 'Galaxy Connect for ARM64', 'title').pack(anchor='w')
        label(titles, s['subtitle'], 'subtitle', 'text-muted').pack(anchor='w')
        seg = Box(inner, C['bg'], 10, pad=(3, 3))
        seg.pack(side='right')
        for code, name in LANGS:
            on = code == self.lang
            item = Box(seg.inner, C['surface'] if on else C['bg'], 8, pad=(12, 4))
            item.pack(side='left', padx=(0, px(2)) if code == LANGS[0][0] else 0)
            l = label(item.inner, name, 'segment-on' if on else 'segment', 'text' if on else 'text-muted')
            l.pack()
            if not on:
                for w in (item.canvas, item.inner, l):
                    w['cursor'] = 'hand2'
                    w.bind('<Button-1>', lambda e, c=code: self.root.after_idle(self.update_settings, {'lang': c}))

    def hero(self, body, s):
        state = hero_state(self.status, self.error)
        card = Box(body, C['surface'], 16, pad=(18, 14), border=C['border'])
        card.pack(fill='x')
        if not state:
            label(card.inner, s['loading'], 'body', 'text-muted').pack(anchor='w', pady=px(12))
            return
        title, desc = s['states'][state]
        tone = {'ready': ('success-soft', 'check'), 'launch': ('primary-soft', 'play')}.get(state, ('warning-soft', 'warning'))
        ring = Box(card.inner, C[tone[0]], 22, pad=(10, 10))
        Icon(ring.inner, tone[1], 24).pack()
        ring.pack(side='left')
        if self.checked_at:
            label(card.inner, s['last_checked'](self.checked_at), 'small', 'text-muted').pack(side='right', padx=(px(16), 0))
        text = tk.Frame(card.inner, bg=C['surface'])
        text.pack(side='left', fill='x', expand=True, padx=(px(16), 0))
        label(text, title, 'hero').pack(anchor='w')
        # 오류 문구가 길어도 카드가 두 줄 남짓에서 끝나게 자른다
        message = (self.error or '')[:160] if state == 'error' else desc
        wrap_label(text, message, 'body', 'text-muted').pack(fill='x')

    def card_head(self, card, title, button):
        head = tk.Frame(card.inner, bg=C['surface'])
        head.pack(fill='x', pady=(0, px(6)))
        label(head, title, 'h2').pack(side='left')
        button(head).pack(side='right')

    def status_card(self, parent, s):
        card = Box(parent, C['surface'], 16, pad=(18, 14), border=C['border'])
        self.card_head(card, s['status'], lambda p: Button(p, s['refresh'], self.refresh, disabled=self.loading or bool(self.busy)))
        st = self.status
        if not st:
            return card
        detection = st.get('Detection')
        if not detection:
            badge = lambda p: Badge(p, 'neutral', s['none'])
        elif detection.get('IsSamsungDevice'):
            badge = lambda p: Badge(p, 'success', s['badge_detected'])
        else:
            badge = lambda p: Badge(p, 'warning', s['badge_not_detected'])
        info_row(card.inner, s['rows']['detection'], badge)
        info_row(card.inner, s['rows']['gc'], st.get('GalaxyConnect') or s['not_installed'])
        info_row(card.inner, s['rows']['mc'], st.get('MultiControl') or s['not_installed'])
        info_row(card.inner, s['rows']['service'], s['service'].get(st.get('Service')) or st.get('Service') or s['none'])
        return card

    def actions_card(self, parent, s):
        card = Box(parent, C['surface'], 16, pad=(18, 14), border=C['border'])
        self.card_head(card, s['actions'], lambda p: Button(p, s['view_log'], self.open_log))
        wrap_label(card.inner, s['actions_body'], 'body', 'text-muted').pack(fill='x', pady=(px(6), px(12)))
        buttons = tk.Frame(card.inner, bg=C['surface'])
        buttons.pack(fill='x')
        busy = bool(self.busy)
        Button(buttons, s['running'] if self.busy == 'apply' else s['apply'], lambda: self.confirm('apply'), 'primary', disabled=busy) \
            .pack(side='left', fill='x', expand=True)
        Button(buttons, s['backup'], lambda: self.run('backup'), disabled=busy).pack(side='left', padx=(px(8), 0))
        Button(buttons, s['running'] if self.busy == 'restore' else s['restore'], lambda: self.confirm('restore'), 'danger', disabled=busy) \
            .pack(side='left', padx=(px(8), 0))
        note = Box(card.inner, C['warning-soft'], 10, pad=(12, 10))
        note.pack(fill='x', pady=(px(12), 0))
        Icon(note.inner, 'warning', 16).pack(side='left', anchor='n', pady=(px(2), 0))
        wrap_label(note.inner, s['note'], 'small', 'warning').pack(side='left', fill='x', expand=True, padx=(px(8), 0))
        if self.result:
            ok = self.result == 'ok'
            toast = Box(card.inner, C['success-soft' if ok else 'danger-soft'], 10, pad=(12, 8))
            toast.pack(fill='x', pady=(px(12), 0))
            label(toast.inner, s['done'][self.result], 'body', 'success' if ok else 'danger').pack(anchor='w')
        return card


def run(backend):
    # 고해상도 화면에서 흐리게 보이지 않게 한다 (배율은 setup 에서 직접 계산)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    setup(root)
    root.title(backend.APP_NAME)
    root.configure(bg=C['bg'])
    root.geometry(f'{px(WIDTH)}x{px(HEIGHT)}')
    root.minsize(px(WIDTH), px(HEIGHT))
    App(root, backend)
    root.mainloop()
