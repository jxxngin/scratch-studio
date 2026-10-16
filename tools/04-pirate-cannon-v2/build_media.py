# -*- coding: utf-8 -*-
"""해적선 대포 합친 교안(버전 2 폴더)의 시작 프로젝트와 media/를 만든다.

실행: python tools/04-pirate-cannon-v2/build_media.py
필요: Pillow, 맑은 고딕(C:/Windows/Fonts/malgun.ttf). build_unit.py를 먼저 돌린다.

- starter.sb3: 버전 1의 시작 프로젝트를 그대로 복사한다.
- 그림과 사진: unit.json이 쓰는 것 중 GIF가 아닌 것은 버전 1의 media/에서 복사한다.
- media/s<번호>-<내용>.gif: 만들기 스텝마다 그 스텝까지 완성한 작품이 움직이는 모습

좌표 기준(스크래치 무대): 대포 회전축 (-170, -70), 과녁 1번 (-36, 64) 45도, 2번 (90, 80) 60도, 3번 (207, 31) 75도
"""
import json, math, os, shutil
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
V1 = os.path.join(ROOT, "project", "lv1", "04-pirate-cannon")
OUT = os.path.join(ROOT, "project", "lv1", "04-pirate-cannon-v2")
MEDIA = os.path.join(OUT, "media")

unit = json.load(open(os.path.join(OUT, "unit.json"), encoding="utf-8"))
srcs = set()
for s in unit["steps"]:
    srcs.update(b["src"] for b in s.get("content", []) if b["type"] == "image")
    srcs.update(q["image"] for q in s.get("questions", []) if "image" in q)

shutil.rmtree(MEDIA, ignore_errors=True)
os.makedirs(MEDIA)
shutil.copyfile(os.path.join(V1, "starter.sb3"), os.path.join(OUT, "starter.sb3"))
for src in sorted(srcs):
    if not src.endswith(".gif"):
        shutil.copyfile(os.path.join(V1, src), os.path.join(OUT, src))

# ---------------------------------------------------------------- 그리기
FONT = "C:/Windows/Fonts/malgun.ttf"
FONT_B = "C:/Windows/Fonts/malgunbd.ttf"
def font(size, bold=False): return ImageFont.truetype(FONT_B if bold else FONT, size)

P = (-170, -70)
TARGETS = [(-36, 64), (90, 80), (207, 31)]
def scr(x, y): return (240 + x, 180 - y)
PX, PY = scr(*P)

def unit_vec(d):
    a = math.radians(d)
    return math.sin(a), -math.cos(a)

def draw_stage(d):
    for yy in range(0, 280):
        t = yy / 280
        c = tuple(int(a + (b - a) * t) for a, b in zip((111, 183, 232), (207, 234, 248)))
        d.line([(0, yy), (480, yy)], fill=c)
    d.polygon([(330, 282), (360, 258), (395, 262), (430, 250), (470, 282)], fill=(122, 154, 90))
    d.rectangle([0, 280, 480, 360], fill=(35, 105, 160))
    for cx, cy, rx, ry in [(200, 40, 34, 12), (222, 32, 22, 12), (400, 70, 30, 10), (420, 62, 18, 10), (330, 200, 26, 9)]:
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(245, 250, 253))
    d.line([(14, 262), (14, 150)], fill=(90, 58, 30), width=5)
    d.polygon([(17, 154), (38, 159), (17, 168)], fill=(34, 34, 34))
    d.polygon([(4, 262), (150, 262), (134, 300), (18, 300)], fill=(138, 90, 43), outline=(90, 58, 30))
    d.rectangle([58, 250, 82, 262], fill=(74, 48, 24))
    for a in range(0, 106, 6):
        x1, y1 = unit_vec(a)
        x2, y2 = unit_vec(a + 3)
        d.line([(PX + 70 * x1, PY + 70 * y1), (PX + 70 * x2, PY + 70 * y2)], fill="white", width=2)
    for a in range(0, 106, 15):
        ux, uy = unit_vec(a)
        d.line([(PX + 62 * ux, PY + 62 * uy), (PX + 74 * ux, PY + 74 * uy)], fill="white", width=2)
        if a <= 90:
            d.text((PX + 86 * ux, PY + 86 * uy), str(a), fill="white", font=font(11, True), anchor="mm")

def draw_cannon(d, ang):
    ux, uy = unit_vec(ang)
    vx, vy = -uy, ux
    def rect(a, b, w):
        return [(PX + ux * a + vx * w, PY + uy * a + vy * w), (PX + ux * b + vx * w, PY + uy * b + vy * w),
                (PX + ux * b - vx * w, PY + uy * b - vy * w), (PX + ux * a - vx * w, PY + uy * a - vy * w)]
    d.polygon(rect(-2, 48, 7), fill=(58, 58, 58))
    d.polygon(rect(44, 52, 9), fill=(34, 34, 34))
    d.ellipse([PX - 8, PY - 8, PX + 8, PY + 8], fill=(43, 43, 43))

def draw_target(d, pos):
    tx, ty = scr(*pos)
    for r, c in [(22, (226, 59, 59)), (16, (255, 255, 255)), (10, (226, 59, 59)), (4, (255, 255, 255))]:
        d.ellipse([tx - r, ty - r, tx + r, ty + r], fill=c)

def draw_ball(d, pos):
    x, y = scr(*pos)
    d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(27, 27, 27), outline=(85, 85, 85))
    d.ellipse([x - 4.5, y - 4.5, x - 0.5, y - 0.5], fill=(119, 119, 119))

def draw_monitors(d, monitors):
    for i, (label, value) in enumerate(monitors):
        y = 6 + i * 28
        f = font(12, True)
        lw = d.textlength(label, font=f)
        vw = max(26, d.textlength(str(value), font=f) + 14)
        d.rounded_rectangle([6, y, 6 + lw + vw + 20, y + 24], radius=5, fill=(230, 240, 255), outline=(196, 205, 220))
        d.text((12, y + 12), label, fill=(87, 94, 117), font=f, anchor="lm")
        x0 = 6 + lw + 12
        d.rounded_rectangle([x0, y + 3, x0 + vw, y + 21], radius=5, fill=(255, 140, 26))
        d.text((x0 + vw / 2, y + 12), str(value), fill="white", font=f, anchor="mm")

def draw_say(d, pos, text, rise=40):
    """pos(스크래치 좌표)의 스프라이트 위에 말풍선을 그린다."""
    tx, ty = scr(*pos)
    f = font(13, True)
    w = d.textlength(text, font=f) + 20
    x0 = max(4, min(476 - w, tx - 10))
    y0 = ty - rise - 22
    d.rounded_rectangle([x0, y0, x0 + w, y0 + 30], radius=12, fill="white", outline=(160, 160, 160), width=2)
    d.polygon([(tx - 4, y0 + 29), (tx + 8, y0 + 29), (tx - 2, y0 + 40)], fill="white", outline=(160, 160, 160))
    d.line([(tx - 3, y0 + 29), (tx + 7, y0 + 29)], fill="white", width=3)
    d.text((x0 + w / 2, y0 + 15), text, fill=(40, 40, 40), font=f, anchor="mm")

def draw_key(d, text):
    f = font(14, True)
    w = d.textlength(text, font=f) + 24
    d.rounded_rectangle([470 - w, 318, 470, 350], radius=8, fill=(30, 41, 59))
    d.text((470 - w / 2, 334), text, fill="white", font=f, anchor="mm")

def draw_cursor(d, pos):
    x, y = scr(*pos)
    d.polygon([(x, y), (x, y + 18), (x + 5, y + 13), (x + 9, y + 21), (x + 12, y + 20), (x + 8, y + 12), (x + 14, y + 12)],
              fill="white", outline="black")

def frame(st):
    img = Image.new("RGB", (480, 360))
    d = ImageDraw.Draw(img)
    draw_stage(d)
    if st.get("target"): draw_target(d, st["target"])
    draw_cannon(d, st.get("angle", 90))
    if st.get("cannon_say"): draw_say(d, P, st["cannon_say"], rise=26)
    if st.get("ball"): draw_ball(d, st["ball"])
    if st.get("ball_say") and st.get("ball"): draw_say(d, st["ball"], st["ball_say"], rise=12)
    if st.get("say") and st.get("target"): draw_say(d, st["target"], st["say"])
    draw_monitors(d, st.get("monitors", []))
    if st.get("key"): draw_key(d, st["key"])
    if st.get("cursor"): draw_cursor(d, st["cursor"])
    return img

class Scene:
    def __init__(self, **st):
        self.st = dict(angle=90, target=TARGETS[0], ball=None, say=None, key=None, cursor=None,
                       cannon_say=None, ball_say=None, vars={})
        self.st.update(st)
        self.frames = []
    def snap(self, ms, **temp):
        st = dict(self.st)
        st.update(temp)
        st["monitors"] = list(st["vars"].items())
        self.frames.append((frame(st), ms))
    def set(self, **kw): self.st.update(kw)
    def var(self, name, value): self.st["vars"] = {**self.st["vars"], name: value}
    def press(self, key, n, delta, say=False):
        for _ in range(n):
            self.st["angle"] += delta
            if "각도" in self.st["vars"]: self.var("각도", self.st["angle"])
            if say: self.st["cannon_say"] = str(self.st["angle"])
            self.snap(260 if say else 220, key=key)
    def fire(self, on_hit="stop", end_hold=300):
        """포탄을 쏜다. on_hit: "stop"(명중을 올리고 사라짐), "say"(명중!이라고 말하며 지나감)"""
        ux, uy = unit_vec(self.st["angle"])
        self.snap(150, key="스페이스", ball=P)
        said = False
        for step in range(2, 41, 2):
            pos = (P[0] + ux * 10 * step, P[1] - uy * 10 * step)
            t = self.st["target"]
            touching = t and math.dist(pos, t) <= 27
            if touching and on_hit == "stop":
                self.snap(70, ball=pos)
                self.var("명중", self.st["vars"].get("명중", 0) + 1)
                self.snap(end_hold)
                return
            said = said or touching
            self.snap(90 if said and on_hit == "say" else 70, ball=pos, ball_say="명중!" if said else None)
        self.snap(end_hold)
    def save(self, name):
        imgs = [im.quantize(colors=256, method=Image.MEDIANCUT) for im, _ in self.frames]
        imgs[0].save(os.path.join(MEDIA, name), save_all=True, append_images=imgs[1:],
                     duration=[ms for _, ms in self.frames], loop=0, optimize=True, disposal=1)
        print("%s: %d frames, %.1fs" % (name, len(self.frames), sum(ms for _, ms in self.frames) / 1000))

CLICK = (-160, -64)

# s05 대포 체조: 클릭하면 0 → 45 → 90 → 180 → 90
s = Scene()
s.snap(700, cursor=CLICK)
for a in (0, 45, 90, 180):
    s.set(angle=a)
    s.snap(500, cursor=CLICK, key="클릭")
s.set(angle=90)
s.snap(1300)
s.save("s05-dance.gif")

# s06 변수 각도 만들기
s = Scene()
s.snap(900)
s.var("각도", 0)
s.snap(2000)
s.save("s06-angle-var.gif")

# s08 대포 준비: 위를 보던 대포가 깃발에 오른쪽, 각도 90
s = Scene(angle=0, vars={"각도": 0})
s.snap(1000)
s.set(angle=90)
s.var("각도", 90)
s.snap(1800, key="⚑ 깃발")
s.snap(600)
s.save("s08-ready.gif")

# s09 위쪽 화살표
s = Scene(vars={"각도": 90})
s.snap(800)
s.press("↑", 2, -5)
s.snap(1200)
s.save("s09-up.gif")

# s10 아래쪽 화살표
s = Scene(vars={"각도": 90})
s.snap(800)
s.press("↓", 2, 5)
s.snap(1200)
s.save("s10-down.gif")

# s11 대포가 각도를 말해요
s = Scene(vars={"각도": 90})
s.snap(700)
s.press("↑", 2, -5, say=True)
s.press("↓", 1, 5, say=True)
s.snap(1200)
s.save("s11-say.gif")

# s12 포탄 준비
s = Scene(vars={"각도": 90}, ball=(-170, -70))
s.snap(700)
s.set(ball=None)
s.snap(700, key="⚑ 깃발")
s.press("↑", 2, -5)
s.set(ball=P)
s.snap(1500, key="스페이스")
s.save("s12-load.gif")

# s13 포탄아 날아라
s = Scene(angle=80, vars={"각도": 80}, target=None)
s.snap(600)
s.fire(end_hold=900)
s.save("s13-fly.gif")

# s18 과녁 준비: 옮겨 둔 과녁이 깃발에 첫 자리로, 명중 0
s = Scene(vars={"각도": 90, "명중": 2})
s.snap(500)
for i in range(1, 9):
    pos = (-36 + 16 * i, 64 - 10 * i)
    s.set(target=pos)
    s.snap(90, cursor=(pos[0] + 4, pos[1] - 4))
s.snap(500)
s.set(target=TARGETS[0])
s.var("명중", 0)
s.snap(1600, key="⚑ 깃발")
s.save("s18-target-ready.gif")

# s18b 닿으면 명중! 말하기: 말하며 지나간다 (명중은 그대로)
s = Scene(angle=45, vars={"각도": 45, "명중": 0})
s.snap(600)
s.fire(on_hit="say", end_hold=900)
s.save("s18b-say.gif")

# s19 명중했는지 알아내기
s = Scene(angle=45, vars={"각도": 45, "명중": 0})
s.snap(600)
s.fire(end_hold=1500)
s.save("s19-hit.gif")

# s20 과녁아 다음 자리로
s = Scene(angle=45, vars={"각도": 45, "명중": 0})
s.snap(500)
s.fire(end_hold=250)
s.set(target=TARGETS[1])
s.snap(1500)
s.save("s20-spot2.gif")

# s22 과녁 3곳과 승리: 두 번째 자리부터
s = Scene(angle=60, target=TARGETS[1], vars={"각도": 60, "명중": 1})
s.snap(400)
s.fire(end_hold=200)
s.set(target=TARGETS[2])
s.snap(300)
s.press("↓", 3, 5)
s.fire(end_hold=100)
s.set(say="과녁 3개를 모두 맞혔어요!")
s.snap(1300)
s.set(say=None, target=None)
s.snap(600)
s.save("s22-win.gif")
