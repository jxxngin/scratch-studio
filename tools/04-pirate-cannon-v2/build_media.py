"""해적선 대포 버전2의 시작 프로젝트와 교안 그림(media/)을 만든다.

실행: python tools/04-pirate-cannon-v2/build_media.py project/lv1/04-pirate-cannon-v2
필요: Pillow, 맑은 고딕(C:/Windows/Fonts/malgun.ttf)

- starter.sb3: 1판의 시작 프로젝트를 복사해 두 곳만 고친다.
  1) 스프라이트 이름 "목표" → "과녁" (교안의 "목표" 칸과 헷갈리지 않게)
  2) 포탄을 대포보다 위 레이어로 (대포 자리에 나타난 포탄이 대포 그림에 가려 보이지 않던 문제)
- media/s01-story.png: 1판의 이야기 그림을 그대로 쓴다.
- media/s<번호>-<내용>.gif: 스텝마다 그 스텝까지 완성한 작품이 움직이는 모습 (교안 틀의 미리보기 칸)

좌표 기준(스크래치 무대): 대포 회전축 (-170, -70), 과녁 1번 (-36, 64) 45도, 2번 (90, 80) 60도, 3번 (207, 31) 75도
"""
import json, math, os, shutil, sys, zipfile
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
V1 = os.path.join(ROOT, "project", "lv1", "04-pirate-cannon")
MEDIA = os.path.join(OUT, "media")
os.makedirs(MEDIA, exist_ok=True)

# ---------------------------------------------------------------- 시작 프로젝트
with zipfile.ZipFile(os.path.join(V1, "starter.sb3")) as src, \
     zipfile.ZipFile(os.path.join(OUT, "starter.sb3"), "w", zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        data = src.read(item.filename)
        if item.filename == "project.json":
            p = json.loads(data)
            names = {t["name"]: t for t in p["targets"]}
            names["목표"]["name"] = "과녁"
            names["대포"]["layerOrder"], names["포탄"]["layerOrder"] = 2, 3
            data = json.dumps(p, ensure_ascii=False).encode("utf-8")
        dst.writestr(item.filename, data)

shutil.copyfile(os.path.join(V1, "media", "story-catapult-cannon.png"), os.path.join(MEDIA, "s01-story.png"))

# ---------------------------------------------------------------- 그리기
FONT = "C:/Windows/Fonts/malgun.ttf"
FONT_B = "C:/Windows/Fonts/malgunbd.ttf"
def font(size, bold=False): return ImageFont.truetype(FONT_B if bold else FONT, size)

P = (-170, -70)
TARGETS = [(-36, 64), (90, 80), (207, 31)]
def scr(x, y): return (240 + x, 180 - y)
PX, PY = scr(*P)

def unit(d):
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
    # 각도기
    for a in range(0, 106, 6):
        x1, y1 = unit(a); x2, y2 = unit(a + 3)
        d.line([(PX + 70 * x1, PY + 70 * y1), (PX + 70 * x2, PY + 70 * y2)], fill="white", width=2)
    for a in range(0, 106, 15):
        ux, uy = unit(a)
        d.line([(PX + 62 * ux, PY + 62 * uy), (PX + 74 * ux, PY + 74 * uy)], fill="white", width=2)
        if a <= 90:
            d.text((PX + 86 * ux, PY + 86 * uy), str(a), fill="white", font=font(11, True), anchor="mm")

def draw_cannon(d, ang):
    ux, uy = unit(ang); vx, vy = -uy, ux
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
        lw = d.textlength(label, font=font(12, True)); vw = max(26, d.textlength(str(value), font=font(12, True)) + 14)
        d.rounded_rectangle([6, y, 6 + lw + vw + 20, y + 24], radius=5, fill=(230, 240, 255), outline=(196, 205, 220))
        d.text((12, y + 12), label, fill=(87, 94, 117), font=font(12, True), anchor="lm")
        x0 = 6 + lw + 12
        d.rounded_rectangle([x0, y + 3, x0 + vw, y + 21], radius=5, fill=(255, 140, 26))
        d.text((x0 + vw / 2, y + 12), str(value), fill="white", font=font(12, True), anchor="mm")

def draw_say(d, pos, text):
    tx, ty = scr(*pos)
    f = font(13, True); w = d.textlength(text, font=f) + 20
    x0 = min(470 - w, tx - 10); y0 = ty - 62
    d.rounded_rectangle([x0, y0, x0 + w, y0 + 30], radius=12, fill="white", outline=(160, 160, 160), width=2)
    d.polygon([(tx - 4, y0 + 29), (tx + 8, y0 + 29), (tx - 2, y0 + 40)], fill="white", outline=(160, 160, 160))
    d.line([(tx - 3, y0 + 29), (tx + 7, y0 + 29)], fill="white", width=3)
    d.text((x0 + w / 2, y0 + 15), text, fill=(40, 40, 40), font=f, anchor="mm")

def draw_key(d, text):
    f = font(14, True); w = d.textlength(text, font=f) + 24
    d.rounded_rectangle([470 - w, 318, 470, 350], radius=8, fill=(30, 41, 59))
    d.text((470 - w / 2, 334), text, fill="white", font=f, anchor="mm")

def draw_cursor(d, pos):
    x, y = scr(*pos)
    d.polygon([(x, y), (x, y + 18), (x + 5, y + 13), (x + 9, y + 21), (x + 12, y + 20), (x + 8, y + 12), (x + 14, y + 12)],
              fill="white", outline="black")

def frame(st):
    img = Image.new("RGB", (480, 360)); d = ImageDraw.Draw(img)
    draw_stage(d)
    if st.get("target"): draw_target(d, st["target"])
    draw_cannon(d, st.get("angle", 90))
    if st.get("ball"): draw_ball(d, st["ball"])
    if st.get("say") and st.get("target"): draw_say(d, st["target"], st["say"])
    draw_monitors(d, st.get("monitors", []))
    if st.get("key"): draw_key(d, st["key"])
    if st.get("cursor"): draw_cursor(d, st["cursor"])
    return img

# ---------------------------------------------------------------- 장면 만들기
class Scene:
    def __init__(self, **st):
        self.st = dict(angle=90, target=TARGETS[0], ball=None, say=None, key=None, cursor=None, vars={})
        self.st.update(st)
        self.frames = []
    def snap(self, ms, **temp):
        st = dict(self.st); st.update(temp)
        st["monitors"] = list(st["vars"].items())
        self.frames.append((frame(st), ms))
    def set(self, **kw): self.st.update(kw)
    def var(self, name, value): self.st["vars"] = {**self.st["vars"], name: value}
    def press(self, key, n, delta):
        for _ in range(n):
            self.st["angle"] += delta
            if "각도" in self.st["vars"]: self.var("각도", self.st["angle"])
            self.snap(220, key=key)
    def fire(self, hit_var=True, move_to=None, end_hold=300):
        """포탄을 쏜다. 과녁에 닿으면 멈추고 명중을 올린다. 닿은 과녁 번호를 돌려준다."""
        ux, uy = unit(self.st["angle"])
        self.snap(150, key="스페이스", ball=P)
        for step in range(2, 41, 2):
            pos = (P[0] + ux * 10 * step, P[1] - uy * 10 * step)
            t = self.st["target"]
            if t and math.dist(pos, t) <= 27:
                self.snap(70, ball=pos)
                if hit_var: self.var("명중", self.st["vars"].get("명중", 0) + 1)
                self.snap(end_hold)
                return True
            self.snap(70, ball=pos)
        self.snap(end_hold)
        return False
    def save(self, name):
        imgs = [im.quantize(colors=256, method=Image.MEDIANCUT) for im, _ in self.frames]
        imgs[0].save(os.path.join(MEDIA, name), save_all=True, append_images=imgs[1:],
                     duration=[ms for _, ms in self.frames], loop=0, optimize=True, disposal=1)
        total = sum(ms for _, ms in self.frames)
        print(f"{name}: {len(self.frames)} frames, {total / 1000:.1f}s")

# s02 오늘 만들 것: 완성작 전체
s = Scene(vars={"각도": 90, "명중": 0}); s.snap(600)
s.press("↑", 9, -5); s.fire(); s.set(target=TARGETS[1]); s.snap(400)
s.press("↓", 3, 5); s.fire(); s.set(target=TARGETS[2]); s.snap(400)
s.press("↓", 3, 5); s.fire(end_hold=100)
s.set(say="승리! 3발 모두 명중!"); s.snap(1600); s.set(say=None, target=None); s.snap(900)
s.save("s02-preview.gif")

# s03 대포 돌리기: 클릭하면 45를 봤다가 0.5초 뒤 위(0)
s = Scene(); s.snap(700, cursor=(-160, -64))
s.set(angle=45); s.snap(500, cursor=(-160, -64), key="클릭")
s.set(angle=0); s.snap(1500); s.save("s03-turn.gif")

# s04 변수 각도 만들기: 무대에 [각도 0]이 나타남
s = Scene(); s.snap(900); s.var("각도", 0); s.snap(2000); s.save("s04-angle-var.gif")

# s05 대포 준비하기: 깃발을 누르면 오른쪽(90), 각도 90
s = Scene(angle=0, vars={"각도": 0}); s.snap(1000)
s.set(angle=90); s.var("각도", 90); s.snap(1800, key="⚑ 깃발"); s.snap(600); s.save("s05-ready.gif")

# s06 대포 들어 올리기
s = Scene(vars={"각도": 90}); s.snap(800); s.press("↑", 2, -5); s.snap(1200); s.save("s06-up.gif")

# s07 대포 내리기
s = Scene(angle=80, vars={"각도": 80}); s.snap(800); s.press("↓", 3, 5); s.snap(1200); s.save("s07-down.gif")

# s08 포탄 장전하기: 깃발에 숨고, 스페이스를 누르면 대포 자리에 나타남
s = Scene(vars={"각도": 90}, ball=(-170, -70)); s.snap(700)
s.set(ball=None); s.snap(700, key="⚑ 깃발")
s.press("↑", 2, -5); s.set(ball=P); s.snap(1500, key="스페이스"); s.save("s08-load.gif")

# s09 포탄 쏘기
s = Scene(angle=80, vars={"각도": 80}, target=None); s.snap(600); s.fire(end_hold=900); s.save("s09-fly.gif")

# s10 과녁 준비하기: 옮겨 둔 과녁이 깃발을 누르면 첫 자리로, 명중 0
s = Scene(vars={"각도": 90, "명중": 2}); s.snap(500)
for i in range(1, 9):
    pos = (-36 + 16 * i, 64 - 10 * i); s.set(target=pos); s.snap(90, cursor=(pos[0] + 4, pos[1] - 4))
s.snap(500)
s.set(target=TARGETS[0]); s.var("명중", 0); s.snap(1600, key="⚑ 깃발"); s.save("s10-target-ready.gif")

# s11 명중 알아내기: 맞히면 포탄이 사라지고 명중 1
s = Scene(angle=45, vars={"각도": 45, "명중": 0}); s.snap(600); s.fire(end_hold=1500); s.save("s11-hit.gif")

# s12 과녁 옮기기: 첫 과녁을 맞히면 두 번째 자리로
s = Scene(angle=45, vars={"각도": 45, "명중": 0}); s.snap(500); s.fire(end_hold=250)
s.set(target=TARGETS[1]); s.snap(1500); s.save("s12-spot2.gif")

# s13 세 번째 자리로 옮기기
s = Scene(angle=45, target=TARGETS[1], vars={"각도": 45, "명중": 1}); s.snap(500)
s.press("↓", 3, 5); s.fire(end_hold=250); s.set(target=TARGETS[2]); s.snap(1400); s.save("s13-spot3.gif")

# s14 승리 외치기
s = Scene(angle=60, target=TARGETS[2], vars={"각도": 60, "명중": 2}); s.snap(400)
s.press("↓", 3, 5); s.fire(end_hold=100)
s.set(say="승리! 3발 모두 명중!"); s.snap(1500); s.set(say=None, target=None); s.snap(700); s.save("s14-win.gif")
