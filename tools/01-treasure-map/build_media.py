# -*- coding: utf-8 -*-
"""보물 지도 탐험 교안의 시작 프로젝트(starter.sb3)와 그림·미리보기 GIF(media/)를 만든다.

실행: python tools/01-treasure-map/build_media.py
필요: Pillow, 맑은 고딕(C:/Windows/Fonts/malgun.ttf)

- starter.sb3: 배경 '보물 지도'(격자와 좌표 숫자, 네 귀퉁이의 배·동굴·야자수·해골 바위), 스프라이트 '보물'(X 표시), '탐험가'
- media/: 이야기 그림(story-*.png), 좌표 설명 그림(stage-xy.png), 오늘 만들 게임(s03-preview.gif), 만들기 스텝의 미리보기 GIF
- 교안(unit.json)은 건드리지 않는다. 무대 모습이나 보물 자리를 바꾸면 unit.json의 좌표와 채점 규칙도 함께 고친다.

좌표 기준(스크래치 무대): 탐험가 출발(배) (-180, -120), 방향키 한 번에 10
보물 자리 1~5: (-60, -60), (-120, 60), (60, 120), (120, 0), (0, -120)
귀퉁이 표시: 배 (-180, -120), 동굴 (-180, 120), 야자수 (180, 120), 해골 바위 (180, -120)
"""
import hashlib, io, json, os, zipfile
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "project", "lv1", "01-treasure-map")
MEDIA = os.path.join(OUT, "media")
os.makedirs(MEDIA, exist_ok=True)

FONT = "C:/Windows/Fonts/malgun.ttf"
FONT_B = "C:/Windows/Fonts/malgunbd.ttf"
def font(size, bold=False): return ImageFont.truetype(FONT_B if bold else FONT, size)

START = (-180, -120)
SPOTS = [(-60, -60), (-120, 60), (60, 120), (120, 0), (0, -120)]
LANDMARKS = {"배": (-180, -120), "동굴": (-180, 120), "야자수": (180, 120), "해골 바위": (180, -120)}
STEP = 10

# ---------------------------------------------------------------- 지도 (k배 크기로 그린다)
PAPER = (244, 228, 188)
SEA = (126, 190, 214)
SAND = (236, 211, 150)
GRASS = (160, 196, 110)
INK = (110, 72, 38)

ISLAND = [(-215, -55), (-150, -78), (-122, -110), (-118, -160), (-20, -164), (90, -160), (170, -165), (220, -140),
          (226, -50), (218, 40), (226, 140), (170, 166), (60, 160), (-50, 166), (-150, 160), (-222, 146), (-226, 60), (-218, 0)]

class K:
    """스크래치 좌표 → 그림 좌표 (k배)."""
    def __init__(self, k): self.k = k
    def p(self, x, y): return ((240 + x) * self.k, (180 - y) * self.k)
    def s(self, v): return v * self.k

def draw_ship(d, c):
    x, y = c.p(*LANDMARKS["배"])
    s = c.s
    d.polygon([(x - s(22), y + s(2)), (x + s(22), y + s(2)), (x + s(14), y + s(14)), (x - s(14), y + s(14))], fill=(120, 72, 36), outline=INK)
    d.line([(x, y + s(2)), (x, y - s(24))], fill=INK, width=max(1, int(s(2))))
    d.polygon([(x + s(1), y - s(22)), (x + s(18), y - s(6)), (x + s(1), y - s(4))], fill=(250, 250, 245), outline=INK)
    d.polygon([(x - s(1), y - s(20)), (x - s(14), y - s(5)), (x - s(1), y - s(5))], fill=(250, 250, 245), outline=INK)

def draw_cave(d, c):
    x, y = c.p(*LANDMARKS["동굴"])
    s = c.s
    d.polygon([(x - s(26), y + s(14)), (x - s(18), y - s(10)), (x - s(4), y - s(20)), (x + s(14), y - s(16)), (x + s(26), y + s(14))], fill=(150, 140, 128), outline=(90, 84, 76))
    d.chord([x - s(11), y - s(6), x + s(11), y + s(26)], 180, 360, fill=(40, 34, 30))

def draw_palm(d, c):
    x, y = c.p(*LANDMARKS["야자수"])
    s = c.s
    d.line([(x + s(2), y + s(16)), (x - s(2), y - s(8))], fill=(130, 88, 44), width=max(2, int(s(5))))
    for dx, dy in [(-18, -2), (18, -2), (-12, -16), (12, -16), (0, -20)]:
        d.line([(x - s(2), y - s(10)), (x + s(dx), y + s(dy) - s(4))], fill=(54, 140, 60), width=max(2, int(s(5))))
    d.ellipse([x - s(5), y - s(10), x + s(1), y - s(4)], fill=(120, 80, 40))

def draw_skull(d, c):
    x, y = c.p(*LANDMARKS["해골 바위"])
    s = c.s
    d.ellipse([x - s(20), y - s(16), x + s(20), y + s(14)], fill=(170, 164, 156), outline=(100, 96, 90))
    d.ellipse([x - s(11), y - s(8), x - s(3), y], fill=(40, 36, 34))
    d.ellipse([x + s(3), y - s(8), x + s(11), y], fill=(40, 36, 34))
    d.polygon([(x, y + s(1)), (x - s(3), y + s(6)), (x + s(3), y + s(6))], fill=(40, 36, 34))

def draw_map(d, c, labels=True):
    s = c.s
    d.rectangle([0, 0, s(480), s(360)], fill=PAPER)
    d.rectangle([s(6), s(6), s(474), s(354)], fill=SEA)
    for i in range(14):
        wx, wy = (37 * i * 7) % 440 + 20, (53 * i * 3) % 320 + 20
        d.arc([s(wx), s(wy), s(wx + 14), s(wy + 8)], 200, 340, fill=(96, 160, 190), width=max(1, int(s(1.5))))
    d.polygon([c.p(x, y) for x, y in ISLAND], fill=SAND, outline=(196, 160, 96))
    for cx, cy, rx, ry in [(-60, 40, 90, 50), (100, 60, 70, 40), (40, -90, 80, 35)]:
        x, y = c.p(cx, cy)
        d.ellipse([x - s(rx), y - s(ry), x + s(rx), y + s(ry)], fill=GRASS)
    # 격자: 60마다 한 줄, 가운데 두 줄(x=0, y=0)은 진하게
    for gx in range(-180, 181, 60):
        d.line([c.p(gx, 180), c.p(gx, -180)], fill=(150, 110, 70) if gx else INK, width=max(1, int(s(1 if gx else 2.5))))
    for gy in range(-120, 121, 60):
        d.line([c.p(-240, gy), c.p(240, gy)], fill=(150, 110, 70) if gy else INK, width=max(1, int(s(1 if gy else 2.5))))
    draw_ship(d, c); draw_cave(d, c); draw_palm(d, c); draw_skull(d, c)
    f = font(int(s(10)), True)
    for name, (lx, ly) in LANDMARKS.items():
        x, y = c.p(lx, ly)
        w = d.textlength(name, font=f)
        d.rounded_rectangle([x - w / 2 - s(4), y + s(20), x + w / 2 + s(4), y + s(34)], radius=s(4), fill=(255, 250, 235))
        d.text((x, y + s(27)), name, fill=INK, font=f, anchor="mm")
    if labels:
        f = font(int(s(10)), True)
        def tag(pos, text):
            x, y = pos
            w = d.textlength(text, font=f)
            d.rounded_rectangle([x - w / 2 - s(3), y - s(7), x + w / 2 + s(3), y + s(7)], radius=s(3), fill=(255, 250, 235))
            d.text((x, y), text, fill=INK, font=f, anchor="mm")
        for gx in range(-180, 181, 60):
            if gx: tag((c.p(gx, 0)[0], c.p(gx, 0)[1] + s(10)), str(gx))
        for gy in range(-120, 121, 60):
            if gy: tag((c.p(0, gy)[0] + s(16), c.p(0, gy)[1]), str(gy))
        tag((c.p(0, 0)[0] + s(10), c.p(0, 0)[1] + s(10)), "0")
        tag((c.p(228, 0)[0], c.p(228, 0)[1] - s(12)), "x")
        tag((c.p(0, 170)[0] + s(12), c.p(0, 170)[1]), "y")

# ---------------------------------------------------------------- 스프라이트 (그림과 SVG를 같은 모양으로)
def draw_explorer(d, c, pos):
    x, y = c.p(*pos)
    s = c.s
    d.rectangle([x - s(8), y + s(8), x - s(2), y + s(20)], fill=(70, 60, 50))
    d.rectangle([x + s(2), y + s(8), x + s(8), y + s(20)], fill=(70, 60, 50))
    d.rounded_rectangle([x - s(10), y - s(6), x + s(10), y + s(12)], radius=s(4), fill=(46, 139, 87))
    d.ellipse([x - s(7), y - s(19), x + s(7), y - s(5)], fill=(255, 214, 170))
    d.ellipse([x - s(13), y - s(20), x + s(13), y - s(15)], fill=(139, 94, 60))
    d.rounded_rectangle([x - s(8), y - s(28), x + s(8), y - s(17)], radius=s(3), fill=(139, 94, 60))

EXPLORER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="48" viewBox="0 0 32 48">
<rect x="8" y="36" width="6" height="12" fill="#463c32"/>
<rect x="18" y="36" width="6" height="12" fill="#463c32"/>
<rect x="6" y="22" width="20" height="18" rx="4" fill="#2e8b57"/>
<circle cx="16" cy="16" r="7" fill="#ffd6aa"/>
<ellipse cx="16" cy="10.5" rx="13" ry="2.5" fill="#8b5e3c"/>
<rect x="8" y="0" width="16" height="11" rx="3" fill="#8b5e3c"/>
</svg>"""
EXPLORER_CENTER = (16, 28)

def draw_treasure(d, c, pos):
    x, y = c.p(*pos)
    s = c.s
    d.ellipse([x - s(20), y - s(8), x + s(20), y + s(12)], fill=(214, 178, 110))
    w = max(2, int(s(5)))
    d.line([(x - s(11), y - s(11)), (x + s(11), y + s(11))], fill=(200, 40, 40), width=w)
    d.line([(x - s(11), y + s(11)), (x + s(11), y - s(11))], fill=(200, 40, 40), width=w)

TREASURE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="40" height="28" viewBox="0 0 40 28">
<ellipse cx="20" cy="15" rx="20" ry="10" fill="#d6b26e"/>
<line x1="9" y1="2" x2="31" y2="24" stroke="#c82828" stroke-width="5" stroke-linecap="round"/>
<line x1="9" y1="24" x2="31" y2="2" stroke="#c82828" stroke-width="5" stroke-linecap="round"/>
</svg>"""
TREASURE_CENTER = (20, 13)

def touching(a, b):
    """미리보기 GIF용 어림 판정. 실제 엔진은 그림의 겹침으로 판정한다."""
    return abs(a[0] - b[0]) <= 26 and abs(a[1] - b[1]) <= 26

# ---------------------------------------------------------------- 무대 위 표시
def draw_monitors(d, monitors):
    for i, (label, value) in enumerate(monitors):
        y = 12 + i * 28
        f = font(12, True)
        lw = d.textlength(label, font=f)
        vw = max(30, d.textlength(str(value), font=f) + 14)
        d.rounded_rectangle([12, y, 12 + lw + vw + 20, y + 24], radius=5, fill=(230, 240, 255), outline=(196, 205, 220))
        d.text((18, y + 12), label, fill=(87, 94, 117), font=f, anchor="lm")
        x0 = 12 + lw + 12
        d.rounded_rectangle([x0, y + 3, x0 + vw, y + 21], radius=5, fill=(76, 151, 255) if "좌표" in label else (92, 177, 214))
        d.text((x0 + vw / 2, y + 12), str(value), fill="white", font=f, anchor="mm")

def draw_say(d, c, pos, text, rise=34):
    tx, ty = c.p(*pos)
    f = font(13, True)
    w = d.textlength(text, font=f) + 20
    x0 = max(4, min(476 - w, tx - 10))
    y0 = max(4, ty - rise - 22)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + 30], radius=12, fill="white", outline=(160, 160, 160), width=2)
    d.polygon([(tx - 4, y0 + 29), (tx + 8, y0 + 29), (tx - 2, y0 + 40)], fill="white", outline=(160, 160, 160))
    d.line([(tx - 3, y0 + 29), (tx + 7, y0 + 29)], fill="white", width=3)
    d.text((x0 + w / 2, y0 + 15), text, fill=(40, 40, 40), font=f, anchor="mm")

def draw_key(d, text):
    f = font(14, True)
    w = d.textlength(text, font=f) + 24
    d.rounded_rectangle([466 - w, 314, 466, 346], radius=8, fill=(30, 41, 59))
    d.text((466 - w / 2, 330), text, fill="white", font=f, anchor="mm")

C1 = K(1)
BASE = Image.new("RGB", (480, 360))
draw_map(ImageDraw.Draw(BASE), C1)

def frame(st):
    img = BASE.copy()
    d = ImageDraw.Draw(img)
    if st.get("treasure"): draw_treasure(d, C1, st["treasure"])
    if st.get("explorer"): draw_explorer(d, C1, st["explorer"])
    if st.get("explorer_say"): draw_say(d, C1, st["explorer"], st["explorer_say"])
    if st.get("treasure_say"): draw_say(d, C1, st["treasure"], st["treasure_say"], rise=44)
    mons = []
    if st.get("show_xy"): mons += [("탐험가: x 좌표", st["explorer"][0]), ("탐험가: y 좌표", st["explorer"][1])]
    if st.get("timer") is not None: mons.append(("타이머", "%.2f" % st["timer"]))
    draw_monitors(d, mons)
    if st.get("key"): draw_key(d, st["key"])
    return img

class Scene:
    def __init__(self, **st):
        self.st = dict(explorer=START, treasure=None, spot=None, key=None, show_xy=False, timer=None,
                       explorer_say=None, treasure_say=None)
        self.st.update(st)
        self.frames = []
    def snap(self, ms, **temp):
        st = dict(self.st); st.update(temp)
        self.frames.append((frame(st), ms))
        # GIF는 실제보다 빨리 돌아가므로, 타이머는 사람이 하는 속도(방향키 한 번에 약 0.25초)로 센다
        if self.st["timer"] is not None: self.st["timer"] += max(ms, 250) / 1000
    def set(self, **kw): self.st.update(kw)
    def walk(self, dx, dy, ms=60):
        """방향키를 n번 누른다. 보물 판정을 켜 두었으면(spot) 닿을 때 보물이 다음 자리로 옮겨 간다."""
        n = abs(dx or dy) // STEP
        key = "→" if dx > 0 else "←" if dx < 0 else "↑" if dy > 0 else "↓"
        for _ in range(n):
            ex, ey = self.st["explorer"]
            self.st["explorer"] = (ex + (STEP if dx > 0 else -STEP if dx < 0 else 0), ey + (STEP if dy > 0 else -STEP if dy < 0 else 0))
            self.snap(ms, key=key)
            self.check_found()
    def check_found(self):
        i = self.st["spot"]
        if i is None or i >= len(SPOTS) or not touching(self.st["explorer"], SPOTS[i]): return
        self.st["spot"] = i + 1
        # 다섯 번째 보물은 "찾았다!" 대신 곧바로 걸린 시간을 말한다
        if self.st.get("found_say") and i + 1 < len(SPOTS): self.snap(700, treasure_say="찾았다!")
        if i + 1 < len(SPOTS): self.st["treasure"] = SPOTS[i + 1]
    def go(self, i, ms=60):
        """i번 보물 자리까지 가로 먼저, 다음에 세로로 걷는다."""
        ex, ey = self.st["explorer"]
        tx, ty = SPOTS[i]
        self.walk(tx - ex, 0, ms)
        self.walk(0, ty - ey, ms)
    def save(self, name):
        imgs = [im.quantize(colors=256, method=Image.MEDIANCUT) for im, _ in self.frames]
        imgs[0].save(os.path.join(MEDIA, name), save_all=True, append_images=imgs[1:],
                     duration=[ms for _, ms in self.frames], loop=0, optimize=True, disposal=1)
        print("%s: %d frames, %.1fs" % (name, len(self.frames), sum(ms for _, ms in self.frames) / 1000))

# ---------------------------------------------------------------- 미리보기 GIF
# s03 오늘 만들 게임: 완성작 전체 (출발 → 보물 5곳 → 걸린 시간)
s = Scene(explorer=(150, -40), treasure=(120, -60))
s.snap(600)
s.set(explorer=START, treasure=SPOTS[0], spot=0, timer=0.0, explorer_say="보물을 찾으러 가자!", found_say=True)
s.snap(1200, key="⚑ 깃발")
s.set(explorer_say=None)
for i in range(5): s.go(i, ms=50)
# 보물이 말한 시간은 그대로이고, 무대의 타이머는 계속 흐른다
s.set(treasure_say="%.2f" % s.st["timer"])
for _ in range(9): s.snap(300)
s.save("s03-preview.gif")

# s06 깃발을 누르면 배에서 출발
s = Scene(explorer=(0, 0))
s.snap(1000)
s.set(explorer=START)
s.snap(1800, key="⚑ 깃발")
s.snap(500)
s.save("s06-start.gif")

# s09 오른쪽·왼쪽 화살표 (좌표 표시를 켠 모습)
s = Scene(show_xy=True)
s.snap(700)
s.walk(40, 0, ms=220); s.walk(-20, 0, ms=220)
s.snap(1000)
s.save("s09-arrows-x.gif")

# s10 위쪽·아래쪽 화살표
s = Scene(show_xy=True)
s.snap(700)
s.walk(0, 40, ms=220); s.walk(0, -20, ms=220)
s.snap(1000)
s.save("s10-arrows-y.gif")

# s13 보물이 첫 자리에 숨어요
s = Scene(explorer=(40, -20), treasure=(120, -60))
s.snap(1000)
s.set(explorer=START, treasure=SPOTS[0])
s.snap(1800, key="⚑ 깃발")
s.snap(500)
s.save("s13-spot1.gif")

# s15 탐험가가 닿으면 두 번째 자리로
s = Scene(treasure=SPOTS[0], spot=0)
s.snap(600)
s.go(0, ms=90)
s.snap(1500)
s.save("s15-next.gif")

# s16 세 번째 자리: 두 번째 보물을 찾으면 세 번째 자리로
s = Scene(explorer=SPOTS[0], treasure=SPOTS[1], spot=1)
s.snap(600)
s.go(1, ms=80)
s.snap(1500)
s.save("s16-third.gif")

# s17 네 번째, 다섯 번째 자리: 세 번째와 네 번째를 찾고 다섯 번째 자리로
s = Scene(explorer=SPOTS[1], treasure=SPOTS[2], spot=2)
s.snap(600)
for i in (2, 3): s.go(i, ms=60)
s.snap(1500)
s.save("s17-last.gif")

# s20 걸린 시간 말하기: 마지막 보물을 찾으면 곧바로 시간을 말한다 (s18의 '찾았다!'까지 한 모습)
s = Scene(explorer=SPOTS[3], treasure=SPOTS[4], spot=4, timer=24.0, found_say=True)
s.snap(500)
s.go(4, ms=70)
# 보물이 말한 시간은 그대로이고, 무대의 타이머는 계속 흐른다
s.set(treasure_say="%.2f" % s.st["timer"])
for _ in range(9): s.snap(300)
s.save("s20-time.gif")

# ---------------------------------------------------------------- 설명 그림
def arrow(d, a, b, color, width=4):
    d.line([a, b], fill=color, width=width)
    import math
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for da in (2.6, -2.6):
        d.line([b, (b[0] + 12 * math.cos(ang + da), b[1] + 12 * math.sin(ang + da))], fill=color, width=width)

def label(d, pos, text, color=(30, 41, 59), size=13):
    f = font(size, True)
    w = d.textlength(text, font=f)
    x, y = pos
    d.rounded_rectangle([x - w / 2 - 6, y - 11, x + w / 2 + 6, y + 11], radius=6, fill="white", outline=color, width=2)
    d.text((x, y), text, fill=color, font=f, anchor="mm")

# stage-xy: 무대는 좌표 지도 (가운데가 0, 왼쪽·아래는 음수, 야자수 예시)
img = BASE.copy()
d = ImageDraw.Draw(img)
o = C1.p(0, 0)
blue, red = (37, 99, 235), (220, 38, 38)
arrow(d, C1.p(40, 24), C1.p(150, 24), blue)
label(d, C1.p(95, 44), "x가 커져요", blue)
arrow(d, C1.p(-40, 24), C1.p(-150, 24), red)
label(d, C1.p(-95, 44), "x가 작아져요 (음수)", red)
arrow(d, C1.p(-24, 40), C1.p(-24, 135), blue)
label(d, C1.p(-85, 140), "y가 커져요", blue)
arrow(d, C1.p(-24, -40), C1.p(-24, -135), red)
label(d, C1.p(-85, -150), "y가 작아져요 (음수)", red)
d.ellipse([o[0] - 6, o[1] - 6, o[0] + 6, o[1] + 6], fill=(30, 41, 59))
label(d, C1.p(62, -38), "(0, 0) 가운데")
p = C1.p(180, 120)
for xx in range(int(o[0]) + 8, int(p[0]), 14): d.line([(xx, o[1]), (xx + 7, o[1])], fill=(234, 88, 12), width=3)
for yy in range(int(p[1]) + 16, int(o[1]), 14): d.line([(p[0], yy), (p[0], yy + 7)], fill=(234, 88, 12), width=3)
label(d, (p[0] - 70, p[1] + 2), "야자수 (180, 120)", (234, 88, 12))
img.save(os.path.join(MEDIA, "stage-xy.png"))

# story-fly: 천장 타일 위의 파리 (어림해 보기 답: 왼쪽 벽에서 5칸, 아래 벽에서 3칸)
img = Image.new("RGB", (480, 320), (250, 247, 240))
d = ImageDraw.Draw(img)
X0, Y0, T, COLS, ROWS = 60, 30, 48, 8, 5
for r in range(ROWS):
    for q in range(COLS):
        d.rectangle([X0 + q * T, Y0 + r * T, X0 + (q + 1) * T, Y0 + (r + 1) * T],
                    fill=(236, 230, 214) if (r + q) % 2 else (244, 239, 226), outline=(196, 186, 160), width=2)
d.rectangle([X0, Y0, X0 + COLS * T, Y0 + ROWS * T], outline=(120, 100, 70), width=4)
fx, fy = X0 + 4.5 * T, Y0 + (ROWS - 2.5) * T
d.ellipse([fx - 9, fy - 5, fx + 9, fy + 7], fill=(40, 40, 40))
d.ellipse([fx - 15, fy - 13, fx - 1, fy - 1], fill=(200, 220, 240), outline=(120, 140, 160))
d.ellipse([fx + 1, fy - 13, fx + 15, fy - 1], fill=(200, 220, 240), outline=(120, 140, 160))
d.ellipse([fx - 4, fy - 9, fx + 4, fy - 2], fill=(160, 30, 30))
cx, cy = X0, Y0 + ROWS * T
d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(234, 88, 12))
label(d, (cx + 34, cy + 22), "모서리", (234, 88, 12))
label(d, (X0 + COLS * T / 2, Y0 + ROWS * T + 22), "가로 →", (37, 99, 235))
label(d, (X0 - 30, Y0 + ROWS * T / 2), "세로 ↑", (37, 99, 235))
img.save(os.path.join(MEDIA, "story-fly.png"))

# story-map: 보물 지도 쪽지 (보물 자리를 숫자 두 개로 적는다)
img = Image.new("RGB", (480, 300), (250, 247, 240))
d = ImageDraw.Draw(img)
d.rounded_rectangle([40, 20, 440, 280], radius=10, fill=(244, 228, 188), outline=(150, 110, 70), width=4)
d.text((240, 56), "해적의 쪽지", fill=INK, font=font(24, True), anchor="mm")
for i, (x, y) in enumerate(SPOTS):
    d.text((100, 100 + i * 34), "보물 %d" % (i + 1), fill=INK, font=font(18, True), anchor="lm")
    d.text((240, 100 + i * 34), "x: %d   y: %d" % (x, y), fill=(60, 40, 20), font=font(18), anchor="lm")
img.save(os.path.join(MEDIA, "story-map.png"))

# story-seats: 영화관 좌석표 (어림해 보기 답: C열 5번)
img = Image.new("RGB", (480, 300), (250, 247, 240))
d = ImageDraw.Draw(img)
d.rounded_rectangle([90, 18, 420, 40], radius=6, fill=(203, 213, 225))
d.text((255, 29), "스크린", fill=(51, 65, 85), font=font(13, True), anchor="mm")
ROWS = "ABCDE"
for r, row in enumerate(ROWS):
    y = 70 + r * 40
    d.text((62, y + 14), row, fill=(51, 65, 85), font=font(16, True), anchor="mm")
    for q in range(8):
        x = 90 + q * 42
        mark = (row == "C" and q == 4)
        d.rounded_rectangle([x, y, x + 32, y + 28], radius=6, fill=(234, 88, 12) if mark else (147, 197, 253),
                            outline=(194, 65, 12) if mark else (96, 165, 250), width=2)
for q in range(8):
    d.text((106 + q * 42, 284), str(q + 1), fill=(51, 65, 85), font=font(14, True), anchor="mm")
img.save(os.path.join(MEDIA, "story-seats.png"))

# ---------------------------------------------------------------- 시작 프로젝트
C2 = K(2)
backdrop = Image.new("RGB", (960, 720))
draw_map(ImageDraw.Draw(backdrop), C2)
buf = io.BytesIO()
backdrop.save(buf, format="PNG", optimize=True)
assets = {}
def asset(data, ext):
    if isinstance(data, str): data = data.encode("utf-8")
    md5 = hashlib.md5(data).hexdigest()
    assets["%s.%s" % (md5, ext)] = data
    return md5
bg = asset(buf.getvalue(), "png")
ex = asset(EXPLORER_SVG, "svg")
tr = asset(TREASURE_SVG, "svg")

def sprite(name, costume_name, md5, center, x, y, layer):
    return {"isStage": False, "name": name, "variables": {}, "lists": {}, "broadcasts": {}, "blocks": {}, "comments": {},
            "currentCostume": 0,
            "costumes": [{"name": costume_name, "bitmapResolution": 1, "dataFormat": "svg", "assetId": md5,
                          "md5ext": md5 + ".svg", "rotationCenterX": center[0], "rotationCenterY": center[1]}],
            "sounds": [], "volume": 100, "layerOrder": layer, "visible": True, "x": x, "y": y, "size": 100,
            "direction": 90, "draggable": False, "rotationStyle": "all around"}

project = {
    "targets": [
        {"isStage": True, "name": "Stage", "variables": {}, "lists": {}, "broadcasts": {}, "blocks": {}, "comments": {},
         "currentCostume": 0,
         "costumes": [{"name": "보물 지도", "bitmapResolution": 2, "dataFormat": "png", "assetId": bg, "md5ext": bg + ".png",
                       "rotationCenterX": 480, "rotationCenterY": 360}],
         "sounds": [], "volume": 100, "layerOrder": 0, "tempo": 60, "videoTransparency": 50, "videoState": "on",
         "textToSpeechLanguage": None},
        sprite("보물", "보물", tr, TREASURE_CENTER, 120, -60, 1),
        sprite("탐험가", "탐험가", ex, EXPLORER_CENTER, 0, 0, 2),
    ],
    "monitors": [], "extensions": [],
    "meta": {"semver": "3.0.0", "vm": "0.2.0", "agent": "dlab scratch-content builder"},
}
with zipfile.ZipFile(os.path.join(OUT, "starter.sb3"), "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("project.json", json.dumps(project, ensure_ascii=False))
    for name, data in assets.items(): z.writestr(name, data)
print("starter.sb3:", ", ".join(sorted(assets)))
