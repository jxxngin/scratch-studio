"""해적선 대포 단원의 시작 프로젝트(starter.sb3)와 교안 이미지(media/*.png)를 만든다.

좌표 기준(스크래치 무대): 대포 회전축 P = (-170, -70)
과녁 위치: 1번 (-36, 64) 방향 45 / 2번 (90, 80) 방향 60 / 3번 (207, 31) 방향 75
"""
import hashlib, io, json, math, os, sys, zipfile
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
MEDIA = os.path.join(OUT, "media")
os.makedirs(MEDIA, exist_ok=True)

P = (-170, -70)
TARGETS = [(-36, 64), (90, 80), (207, 31)]

def scr(x, y):
    """스크래치 좌표 → 무대 화면 좌표(480x360)"""
    return (240 + x, 180 - y)

PX, PY = scr(*P)  # (70, 250)

def dir_point(d, r, cx=PX, cy=PY):
    a = math.radians(d)
    return (cx + r * math.sin(a), cy - r * math.cos(a))

# ---------------------------------------------------------------- SVG 모양
def protractor_svg():
    parts = []
    # 반원 점선(0~105)
    pts = " ".join(f"{dir_point(d,70)[0]:.1f},{dir_point(d,70)[1]:.1f}" for d in range(0, 106, 3))
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#ffffff" stroke-width="2" stroke-dasharray="4 4" opacity="0.9"/>')
    for d in range(0, 106, 15):
        x1, y1 = dir_point(d, 62); x2, y2 = dir_point(d, 74)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ffffff" stroke-width="2"/>')
        if d <= 90:
            tx, ty = dir_point(d, 86)
            parts.append(f'<text x="{tx:.1f}" y="{ty+4:.1f}" font-family="Sans Serif" font-size="11" font-weight="bold" fill="#ffffff" text-anchor="middle">{d}</text>')
    for d in range(5, 106, 5):
        if d % 15:
            x1, y1 = dir_point(d, 66); x2, y2 = dir_point(d, 72)
            parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ffffff" stroke-width="1" opacity="0.8"/>')
    return "\n".join(parts)

BACKDROP = f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360" viewBox="0 0 480 360">
<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6fb7e8"/><stop offset="1" stop-color="#cfeaf8"/></linearGradient>
<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2f7fb8"/><stop offset="1" stop-color="#174f7a"/></linearGradient>
</defs>
<rect width="480" height="360" fill="url(#sky)"/>
<g fill="#ffffff" opacity="0.85">
<ellipse cx="200" cy="40" rx="34" ry="12"/><ellipse cx="222" cy="32" rx="22" ry="12"/>
<ellipse cx="400" cy="70" rx="30" ry="10"/><ellipse cx="420" cy="62" rx="18" ry="10"/>
<ellipse cx="330" cy="200" rx="26" ry="9"/>
</g>
<path d="M330 282 Q360 250 395 262 Q430 245 470 282 Z" fill="#7a9a5a"/>
<rect x="0" y="280" width="480" height="80" fill="url(#sea)"/>
<path d="M0 288 q12 -6 24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0 t24 0" fill="none" stroke="#9fd3f2" stroke-width="2"/>
<line x1="14" y1="262" x2="14" y2="150" stroke="#5a3a1e" stroke-width="5"/>
<path d="M17 154 L38 159 L17 168 Z" fill="#222222"/>
<path d="M4 262 L150 262 L134 300 L18 300 Z" fill="#8a5a2b" stroke="#5a3a1e" stroke-width="2"/>
<line x1="12" y1="276" x2="142" y2="276" stroke="#5a3a1e" stroke-width="2"/>
<circle cx="50" cy="285" r="4" fill="#3a2410"/><circle cx="80" cy="285" r="4" fill="#3a2410"/><circle cx="110" cy="285" r="4" fill="#3a2410"/>
<rect x="58" y="250" width="24" height="12" rx="2" fill="#4a3018"/>
<circle cx="70" cy="262" r="7" fill="#2b1a0b"/>
{protractor_svg()}
</svg>'''

CANNON = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="24" viewBox="0 0 64 24">
<rect x="8" y="5" width="50" height="14" rx="4" fill="#3a3a3a"/>
<rect x="54" y="3" width="8" height="18" rx="2" fill="#222222"/>
<circle cx="10" cy="12" r="8" fill="#2b2b2b"/>
<rect x="18" y="7" width="30" height="3" rx="1.5" fill="#6a6a6a"/>
</svg>'''

BALL = '''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18">
<circle cx="9" cy="9" r="7" fill="#1b1b1b" stroke="#555555" stroke-width="1"/>
<circle cx="6.5" cy="6.5" r="2" fill="#777777"/>
</svg>'''

TARGET = '''<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
<circle cx="24" cy="24" r="22" fill="#e23b3b" stroke="#8a1f1f" stroke-width="2"/>
<circle cx="24" cy="24" r="16" fill="#ffffff"/>
<circle cx="24" cy="24" r="10" fill="#e23b3b"/>
<circle cx="24" cy="24" r="4" fill="#ffffff"/>
</svg>'''

CANNON_FIRE = CANNON.replace('width="64"', 'width="92"').replace('viewBox="0 0 64 24"', 'viewBox="0 0 92 24"').replace('</svg>', '''<path d="M62 12 L76 1 L73 9 L90 6 L76 13 L89 20 L73 16 L76 23 Z" fill="#ffb21f" stroke="#e8590c" stroke-width="1.5"/>
<circle cx="70" cy="12" r="4" fill="#fff3bf"/>
</svg>''')

BOOM = '''<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 60 60">
<path d="M30 2 L36 20 L55 12 L43 28 L58 38 L39 39 L42 58 L30 44 L18 58 L21 39 L2 38 L17 28 L5 12 L24 20 Z" fill="#ffb21f" stroke="#e8590c" stroke-width="2"/>
<circle cx="30" cy="31" r="9" fill="#fff3bf"/>
</svg>'''

def asset(svg):
    data = svg.encode("utf-8")
    md5 = hashlib.md5(data).hexdigest()
    return md5, data

assets = {}
def costume(name, svg, cx, cy):
    md5, data = asset(svg)
    assets[md5 + ".svg"] = data
    return {"name": name, "bitmapResolution": 1, "dataFormat": "svg",
            "assetId": md5, "md5ext": md5 + ".svg",
            "rotationCenterX": cx, "rotationCenterY": cy}

def sound_wav(name, seconds=0.45, rate=22050):
    """대포 '펑' 소리: 잡음이 빠르게 줄어드는 소리를 직접 만든다(외부 음원 사용 안 함)."""
    import random, struct, wave
    random.seed(4)
    n = int(seconds * rate)
    buf = io.BytesIO()
    w = wave.open(buf, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
    low = 0.0
    frames = bytearray()
    for i in range(n):
        t = i / rate
        low = low * 0.92 + random.uniform(-1, 1) * 0.08   # 낮은 소리만 남기는 간단한 필터
        env = math.exp(-t * 9)
        v = int(max(-1, min(1, low * 6 * env)) * 30000)
        frames += struct.pack("<h", v)
    w.writeframes(bytes(frames)); w.close()
    data = buf.getvalue()
    md5 = hashlib.md5(data).hexdigest()
    assets[md5 + ".wav"] = data
    return {"name": name, "assetId": md5, "dataFormat": "wav", "format": "", "rate": rate,
            "sampleCount": n, "md5ext": md5 + ".wav"}

def sprite(name, cost, layer, x, y, direction=90, visible=True, sounds=()):
    costumes = cost if isinstance(cost, list) else [cost]
    return {"isStage": False, "name": name, "variables": {}, "lists": {}, "broadcasts": {},
            "blocks": {}, "comments": {}, "currentCostume": 0, "costumes": costumes,
            "sounds": list(sounds), "volume": 100, "layerOrder": layer, "visible": visible,
            "x": x, "y": y, "size": 100, "direction": direction, "draggable": False,
            "rotationStyle": "all around"}

project = {
    "targets": [
        {"isStage": True, "name": "Stage", "variables": {}, "lists": {}, "broadcasts": {},
         "blocks": {}, "comments": {}, "currentCostume": 0,
         "costumes": [costume("바다", BACKDROP, 240, 180)], "sounds": [], "volume": 100,
         "layerOrder": 0, "tempo": 60, "videoTransparency": 50, "videoState": "on",
         "textToSpeechLanguage": None},
        sprite("목표", [costume("과녁", TARGET, 24, 24), costume("펑", BOOM, 30, 30)], 1, TARGETS[0][0], TARGETS[0][1]),
        sprite("포탄", costume("포탄", BALL, 9, 9), 2, P[0], P[1], visible=False, sounds=[sound_wav("발사")]),
        sprite("대포", [costume("대포", CANNON, 10, 12), costume("불꽃", CANNON_FIRE, 10, 12)], 3, P[0], P[1], direction=90),
    ],
    "monitors": [], "extensions": [],
    "meta": {"semver": "3.0.0", "vm": "0.2.0", "agent": "dlab scratch-content builder"},
}

with zipfile.ZipFile(os.path.join(OUT, "starter.sb3"), "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("project.json", json.dumps(project, ensure_ascii=False))
    for name, data in assets.items():
        z.writestr(name, data)

# ---------------------------------------------------------------- PNG 그림 (PIL)
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def font(size):
    for idx in range(10):
        f = ImageFont.truetype(FONT, size, index=idx)
        if "KR" in " ".join(f.getname()):
            return f
    return ImageFont.truetype(FONT, size)

S = 2  # 2배 크기로 그린다

def draw_stage(img_d, with_targets=(0,), labels=False, f=None):
    d = img_d
    # 하늘, 바다
    for yy in range(0, 280 * S):
        t = yy / (280 * S)
        c = tuple(int(a + (b - a) * t) for a, b in zip((111, 183, 232), (207, 234, 248)))
        d.line([(0, yy), (480 * S, yy)], fill=c)
    d.polygon([(330*S, 282*S), (360*S, 258*S), (395*S, 262*S), (430*S, 250*S), (470*S, 282*S)], fill=(122, 154, 90))
    d.rectangle([0, 280 * S, 480 * S, 360 * S], fill=(35, 105, 160))
    for cx, cy, rx, ry in [(200,40,34,12),(222,32,22,12),(400,70,30,10),(420,62,18,10),(330,200,26,9)]:
        d.ellipse([(cx-rx)*S, (cy-ry)*S, (cx+rx)*S, (cy+ry)*S], fill=(245, 250, 253))
    # 배
    d.line([(14*S, 262*S), (14*S, 150*S)], fill=(90, 58, 30), width=5*S)
    d.polygon([(17*S,154*S),(38*S,159*S),(17*S,168*S)], fill=(34,34,34))
    d.polygon([(4*S,262*S),(150*S,262*S),(134*S,300*S),(18*S,300*S)], fill=(138,90,43), outline=(90,58,30))
    d.rectangle([58*S,250*S,82*S,262*S], fill=(74,48,24))
    d.ellipse([(70-7)*S,(262-7)*S,(70+7)*S,(262+7)*S], fill=(43,26,11))
    # 각도기
    pts = [tuple(v*S for v in dir_point(a, 70)) for a in range(0, 106, 3)]
    for i in range(0, len(pts)-1, 2):
        d.line([pts[i], pts[i+1]], fill="white", width=2*S)
    for a in range(0, 106, 15):
        p1 = tuple(v*S for v in dir_point(a, 62)); p2 = tuple(v*S for v in dir_point(a, 74))
        d.line([p1, p2], fill="white", width=2*S)
        if a <= 90:
            tx, ty = dir_point(a, 86)
            d.text((tx*S, ty*S), str(a), fill="white", font=font(11*S), anchor="mm")
    # 대포 (방향 90)
    d.rounded_rectangle([(PX-2)*S, (PY-7)*S, (PX+48)*S, (PY+7)*S], radius=4*S, fill=(58,58,58))
    d.rectangle([(PX+44)*S, (PY-9)*S, (PX+52)*S, (PY+9)*S], fill=(34,34,34))
    d.ellipse([(PX-8)*S, (PY-8)*S, (PX+8)*S, (PY+8)*S], fill=(43,43,43))
    # 과녁
    for i in with_targets:
        tx, ty = scr(*TARGETS[i])
        for r, c in [(22,(226,59,59)),(16,(255,255,255)),(10,(226,59,59)),(4,(255,255,255))]:
            d.ellipse([(tx-r)*S,(ty-r)*S,(tx+r)*S,(ty+r)*S], fill=c)
        if labels:
            d.ellipse([(tx+14)*S,(ty-30)*S,(tx+32)*S,(ty-12)*S], fill=(47,111,214))
            d.text(((tx+23)*S,(ty-21)*S), str(i+1), fill="white", font=font(11*S), anchor="mm")

# 1) 시작 무대
img = Image.new("RGB", (480*S, 360*S)); draw_stage(ImageDraw.Draw(img))
img.save(os.path.join(MEDIA, "stage-start.png"))

# 2) 과녁 세 곳
img = Image.new("RGB", (480*S, 360*S)); draw_stage(ImageDraw.Draw(img), with_targets=(0,1,2), labels=True)
img.save(os.path.join(MEDIA, "targets.png"))

# 3) 스크래치의 방향
W, H = 560, 560
img = Image.new("RGB", (W*S//1, H*S//1), "white"); d = ImageDraw.Draw(img)
cx, cy = W//2*S, H//2*S + 10*S
d.ellipse([cx-170*S, cy-170*S, cx+170*S, cy+170*S], outline=(200,210,225), width=3*S)
def arrow(dd, color, r=150, w=6):
    a = math.radians(dd); ex = cx + r*S*math.sin(a); ey = cy - r*S*math.cos(a)
    d.line([(cx, cy), (ex, ey)], fill=color, width=w*S)
    for s in (-1, 1):
        b = a + math.pi + s*0.45
        d.line([(ex, ey), (ex + 18*S*math.sin(b), ey - 18*S*math.cos(b))], fill=color, width=w*S)
    return ex, ey
for dd, lab in [(0,"0"),(90,"90"),(180,"180"),(-90,"-90")]:
    ex, ey = arrow(dd, (60,60,60))
    a = math.radians(dd)
    d.text((cx + 195*S*math.sin(a), cy - 195*S*math.cos(a)), lab, fill=(30,30,30), font=font(26*S), anchor="mm")
ex, ey = arrow(45, (47,111,214), r=130, w=5)
d.text((cx + 158*S*math.sin(math.radians(45)), cy - 158*S*math.cos(math.radians(45))), "45", fill=(47,111,214), font=font(24*S), anchor="mm")
d.ellipse([cx-10*S, cy-10*S, cx+10*S, cy+10*S], fill=(226,59,59))
d.text((W//2*S, 22*S), "위 0 · 오른쪽 90 · 아래 180 · 왼쪽 -90", fill=(30,30,30), font=font(20*S), anchor="mm")
img.save(os.path.join(MEDIA, "direction.png"))

# 4) 1도 차이 → 거리가 멀면 크게 벌어진다 (5도 차이를 과장 없이 그림)
W, H = 760, 420
img = Image.new("RGB", (W*S, H*S), "white"); d = ImageDraw.Draw(img)
ox, oy = 60*S, 360*S
L = 640
def ray(dd, color):
    a = math.radians(dd); ex = ox + L*S*math.sin(a); ey = oy - L*S*math.cos(a)
    d.line([(ox, oy), (ex, ey)], fill=color, width=4*S)
ray(60, (47,111,214)); ray(65, (226,120,40))
for dist in (160, 600):
    p1 = (ox + dist*S*math.sin(math.radians(60)), oy - dist*S*math.cos(math.radians(60)))
    p2 = (ox + dist*S*math.sin(math.radians(65)), oy - dist*S*math.cos(math.radians(65)))
    d.line([p1, p2], fill=(226,59,59), width=4*S)
    gap = dist * 2 * math.sin(math.radians(2.5))
    msg = f"{dist}걸음 앞: 약 {gap:.0f}걸음 차이"
    if dist < 300:
        tx, ty, anc = max(p1[0], p2[0]) + 16*S, (p1[1]+p2[1])/2 + 40*S, "lm"
    else:
        tx, ty, anc = min(p1[0], p2[0]) - 30*S, (p1[1]+p2[1])/2 + 50*S, "rm"
    box = d.textbbox((tx, ty), msg, font=font(20*S), anchor=anc)
    d.rectangle([box[0]-6*S, box[1]-4*S, box[2]+6*S, box[3]+4*S], fill="white")
    d.text((tx, ty), msg, fill=(226,59,59), font=font(20*S), anchor=anc)
d.ellipse([ox-10*S, oy-10*S, ox+10*S, oy+10*S], fill=(43,43,43))
d.text((ox, oy + 30*S), "대포", fill=(30,30,30), font=font(20*S), anchor="mm")
d.text((W*S - 20*S, H*S - 26*S), "파랑 60도 · 주황 65도", fill=(30,30,30), font=font(20*S), anchor="rm")
img.save(os.path.join(MEDIA, "angle-gap.png"))

print("ok", sorted(os.listdir(MEDIA)), len(assets), "assets")

# ---------------------------------------------------------------- 이야기 그림 (직접 그린 삽화)
SKY = (220, 238, 250); SEA = (46, 110, 160); WOOD = (138, 90, 43); DARK = (43, 43, 43)
BRONZE = (176, 122, 54); RED = (226, 59, 59); BLUE = (47, 111, 214); INK = (30, 30, 30)

def canvas(w, h, bg=SKY):
    img = Image.new("RGB", (w*S, h*S), bg)
    return img, ImageDraw.Draw(img)

def arc_path(d, x0, y0, x1, peak, color, width=3, dash=True, steps=40):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 - 4 * peak * t * (1 - t)
        pts.append((x*S, y*S))
    for i in range(len(pts) - 1):
        if not dash or i % 2 == 0:
            d.line([pts[i], pts[i+1]], fill=color, width=width*S)

# 1) 투석기와 대포
img, d = canvas(760, 340)
d.rectangle([0, 280*S, 760*S, 340*S], fill=(150, 190, 110))
# 투석기(왼쪽 위 칸)
d.polygon([(40*S,280*S),(70*S,200*S),(100*S,280*S)], outline=WOOD, width=6*S)
d.line([(70*S,205*S),(30*S,150*S)], fill=WOOD, width=7*S)
d.line([(70*S,205*S),(110*S,240*S)], fill=WOOD, width=7*S)
d.rectangle([100*S,235*S,122*S,258*S], fill=(90,58,30))
d.ellipse([22*S,138*S,40*S,156*S], fill=(120,120,120))
arc_path(d, 32, 147, 300, 70, (120,120,120))
d.text((70*S, 305*S), "투석기", fill=INK, font=font(22*S), anchor="mm")
d.text((300*S, 255*S), "수백 걸음", fill=INK, font=font(18*S), anchor="mm")
# 대포(오른쪽)
d.rectangle([390*S, 255*S, 450*S, 272*S], fill=WOOD)
d.ellipse([395*S,262*S,417*S,284*S], fill=(70,45,20)); d.ellipse([425*S,262*S,447*S,284*S], fill=(70,45,20))
d.polygon([(400*S,262*S),(410*S,250*S),(470*S,222*S),(476*S,236*S),(418*S,266*S)], fill=DARK)
arc_path(d, 474, 228, 745, 150, DARK)
d.text((430*S, 305*S), "대포", fill=INK, font=font(22*S), anchor="mm")
d.text((640*S, 255*S), "훨씬 멀리!", fill=RED, font=font(20*S), anchor="mm")
img.save(os.path.join(MEDIA, "story-catapult-cannon.png"))

# 2) 천자총통과 대장군전
img, d = canvas(760, 300, (247, 241, 228))
d.rectangle([60*S, 210*S, 250*S, 228*S], fill=WOOD)
d.ellipse([70*S,218*S,104*S,252*S], fill=(90,58,30)); d.ellipse([200*S,218*S,234*S,252*S], fill=(90,58,30))
d.rounded_rectangle([70*S, 160*S, 270*S, 208*S], radius=18*S, fill=BRONZE, outline=(120,80,30), width=3*S)
for x in (110, 150, 190, 230):
    d.rectangle([x*S, 156*S, (x+10)*S, 212*S], fill=(150,100,40))
d.ellipse([258*S,166*S,282*S,202*S], fill=(60,40,20))
# 대장군전 (큰 화살)
d.rectangle([330*S, 178*S, 620*S, 188*S], fill=(150,110,60))
d.polygon([(620*S,170*S),(660*S,183*S),(620*S,196*S)], fill=(90,90,90))
for dx in (0, 22):
    d.polygon([((340+dx)*S,183*S),((330+dx)*S,160*S),((360+dx)*S,183*S)], fill=(200,200,200))
    d.polygon([((340+dx)*S,183*S),((330+dx)*S,206*S),((360+dx)*S,183*S)], fill=(200,200,200))
d.text((170*S, 120*S), "천자총통", fill=INK, font=font(24*S), anchor="mm")
d.text((490*S, 140*S), "대장군전: 사람 키보다 긴 쇠촉 화살", fill=INK, font=font(20*S), anchor="mm")
d.text((380*S, 275*S), "기록: 약 900보(걸음)를 날아갔다", fill=RED, font=font(22*S), anchor="mm")
img.save(os.path.join(MEDIA, "story-cheonja.png"))

# 3) 포수의 각도 자
img, d = canvas(760, 380, (247, 241, 228))
cx, cy = 170, 300
ang = math.radians(30)  # 대포 앙각
L = 300
ex, ey = cx + L*math.cos(ang), cy - L*math.sin(ang)
d.line([(cx*S, cy*S), (ex*S, ey*S)], fill=DARK, width=40*S)
d.ellipse([(cx-30)*S,(cy-30)*S,(cx+30)*S,(cy+30)*S], fill=(70,45,20))
# 'ㄱ'자 자: 긴 팔을 포구에 꽂고 짧은 팔이 아래로
mx, my = ex - 40*math.cos(ang), ey + 40*math.sin(ang)
arm_end = (mx + 150*math.cos(ang), my - 150*math.sin(ang))
d.line([(mx*S, my*S), (arm_end[0]*S, arm_end[1]*S)], fill=BRONZE, width=8*S)
qx, qy = arm_end
# 사분원 눈금판
r = 90
d.pieslice([(qx-r)*S,(qy-r)*S,(qx+r)*S,(qy+r)*S], start=90-30, end=180-30, fill=(235,210,160), outline=BRONZE, width=3*S)
for k in range(0, 91, 15):
    a = math.radians(90 + k - 30)
    d.line([((qx + (r-14)*math.cos(a))*S, (qy + (r-14)*math.sin(a))*S), ((qx + r*math.cos(a))*S, (qy + r*math.sin(a))*S)], fill=BRONZE, width=2*S)
# 추와 실(늘 아래로)
d.line([(qx*S, qy*S), (qx*S, (qy+r+30)*S)], fill=INK, width=2*S)
d.ellipse([(qx-8)*S,(qy+r+28)*S,(qx+8)*S,(qy+r+44)*S], fill=RED)
d.text((qx*S + 30*S, (qy+r+36)*S), "추는 늘 아래를 가리켜요", fill=INK, font=font(18*S), anchor="lm")
d.text((380*S, 34*S), "포수의 각도 자: 실과 추가 가리키는 눈금 = 대포의 각도", fill=INK, font=font(20*S), anchor="mm")
img.save(os.path.join(MEDIA, "story-quadrant.png"))

# 4) 타르탈리아의 45도
img, d = canvas(760, 360)
d.rectangle([0, 300*S, 760*S, 360*S], fill=(150, 190, 110))
ox, oy = 60, 300
def traj(theta, color, label, dy=24, dx=0, anc="mm"):
    g = 1.0; v = 24.0
    th = math.radians(theta)
    pts = []
    t = 0
    while True:
        x = v*math.cos(th)*t; y = v*math.sin(th)*t - 0.5*g*t*t
        if y < 0 and t > 0: break
        pts.append(((ox + x)*S, (oy - y)*S)); t += 0.2
    d.line(pts, fill=color, width=4*S)
    last = pts[-1]
    d.ellipse([last[0]-7*S, last[1]-7*S, last[0]+7*S, last[1]+7*S], fill=color)
    if label:
        d.text((last[0] + dx*S, last[1] + dy*S), label, fill=color, font=font(18*S), anchor=anc)
traj(30, (90,150,90), "30도와 60도는 같은 곳에!", dy=30, dx=10, anc="rm"); traj(60, (230,130,40), ""); traj(45, RED, "45도", dy=20)
d.ellipse([(ox-10)*S,(oy-10)*S,(ox+10)*S,(oy+10)*S], fill=DARK)
d.text((380*S, 30*S), "포탄이 가장 멀리 가는 각도는?", fill=INK, font=font(22*S), anchor="mm")
img.save(os.path.join(MEDIA, "story-45.png"))

# 5) 해적선의 대포 구멍
img, d = canvas(760, 330)
d.rectangle([0, 250*S, 760*S, 330*S], fill=SEA)
d.polygon([(90*S,170*S),(670*S,170*S),(620*S,262*S),(140*S,262*S)], fill=WOOD, outline=(90,58,30), width=3*S)
d.line([(110*S,200*S),(650*S,200*S)], fill=(90,58,30), width=3*S)
for x in range(160, 620, 52):
    d.rectangle([x*S, 212*S, (x+22)*S, 232*S], fill=DARK)
for mx_ in (250, 420, 560):
    d.line([(mx_*S,170*S),(mx_*S,30*S)], fill=(90,58,30), width=6*S)
    d.polygon([(mx_*S-60*S,50*S),(mx_*S+60*S,50*S),(mx_*S+50*S,140*S),(mx_*S-50*S,140*S)], fill=(242,234,216), outline=(200,190,170))
d.polygon([(253*S,30*S),(300*S,40*S),(253*S,52*S)], fill=DARK)
d.text((380*S, 300*S), "배 옆구리의 네모 구멍 하나하나가 대포 자리", fill="white", font=font(20*S), anchor="mm")
img.save(os.path.join(MEDIA, "story-pirate-ship.png"))

# 6) 퀴즈 그림: 위를 보는 대포
img, d = canvas(360, 300)
cx, cy = 180, 250
d.rounded_rectangle([(cx-7)*S, (cy-120)*S, (cx+7)*S, cy*S], radius=4*S, fill=DARK)
d.rectangle([(cx-9)*S, (cy-128)*S, (cx+9)*S, (cy-118)*S], fill=(20,20,20))
d.ellipse([(cx-12)*S,(cy-12)*S,(cx+12)*S,(cy+12)*S], fill=(43,43,43))
d.text((cx*S, 30*S), "대포가 이렇게 보고 있어요", fill=INK, font=font(20*S), anchor="mm")
img.save(os.path.join(MEDIA, "quiz-cannon-up.png"))

print("story images ok", sorted(os.listdir(MEDIA)))
