# -*- coding: utf-8 -*-
"""보물 지도 탐험의 채점 규칙을 시험할 작품(tests/*.sb3)을 만든다.

실행: python tools/01-treasure-map/verify/build_tests.py
- solution.sb3: 강사용 안내서 4장의 정답 코드 그대로
- core.sb3: 정답에서 꾸미기(출발 인사, 좌표 말하기, 찾았다!)만 뺀 것
- wrong-*.sb3: 일부러 틀린 작품. 해당 스텝에서 떨어져야 한다 (강사용 안내서 6장의 오개념 작품도 여기에 있다)
- robot-*.sb3: 심화 도전(자동 탐험 로봇)을 넣은 것
- mission-e.sb3: 확장 미션 E(보이지 않는 보물)를 넣은 것
시작 프로젝트(starter.sb3)의 그림과 스프라이트 이름을 그대로 쓰고, 스크립트만 넣는다.
"""
import copy, json, os, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
STARTER = os.path.join(ROOT, "project", "lv1", "01-treasure-map", "starter.sb3")
OUT = os.path.join(HERE, "tests")
os.makedirs(OUT, exist_ok=True)

SPOTS = [(-60, -60), (-120, 60), (60, 120), (120, 0), (0, -120)]
# 채점 경로: 배 (-180, -120)에서 보물 1~5까지 누르는 방향키와 횟수 (unit.json의 checks와 같음)
LEGS_KEYS = [[("ArrowRight", 12), ("ArrowUp", 6)], [("ArrowLeft", 6), ("ArrowUp", 12)], [("ArrowRight", 18), ("ArrowUp", 6)],
             [("ArrowRight", 6), ("ArrowDown", 12)], [("ArrowLeft", 12), ("ArrowDown", 12)]]


class Script:
    """스프라이트 하나의 블록을 만든다. 블록 하나는 (opcode, inputs, fields)."""

    def __init__(self):
        self.blocks = {}
        self.n = 0
        self.tops = 0

    def _id(self):
        self.n += 1
        return "b%d" % self.n

    def _block(self, opcode, parent, inputs=None, fields=None, shadow=False):
        bid = self._id()
        self.blocks[bid] = {"opcode": opcode, "next": None, "parent": parent, "inputs": {}, "fields": fields or {},
                            "shadow": shadow, "topLevel": False}
        for name, val in (inputs or {}).items():
            self.blocks[bid]["inputs"][name] = self._input(val, bid)
        return bid

    def _input(self, val, parent):
        kind = val[0]
        if kind == "num": return [1, [4, str(val[1])]]
        if kind == "text": return [1, [10, str(val[1])]]
        if kind == "rep":  # 둥근 블록을 숫자·글자 칸에 넣음
            rid = self._block(val[1], parent)
            return [3, rid, [10, ""]]
        if kind == "touching":  # <[이름] 에 닿았는가?>
            bid = self._block("sensing_touchingobject", parent)
            mid = self._block("sensing_touchingobjectmenu", bid, fields={"TOUCHINGOBJECTMENU": [val[1], None]}, shadow=True)
            self.blocks[bid]["inputs"]["TOUCHINGOBJECTMENU"] = [1, mid]
            return [2, bid]
        raise ValueError(kind)

    def stack(self, hat, body, hat_fields=None):
        top = self._block(hat, None, fields=hat_fields)
        self.blocks[top].update(topLevel=True, x=40, y=40 + 400 * self.tops)
        self.tops += 1
        prev = top
        for item in body:
            opcode, inputs = item[0], item[1]
            bid = self._block(opcode, prev, inputs, item[2] if len(item) > 2 else None)
            self.blocks[prev]["next"] = bid
            prev = bid
        return top


def gotoxy(x, y): return ("motion_gotoxy", {"X": ("num", x), "Y": ("num", y)})
def glide(s, x, y): return ("motion_glidesecstoxy", {"SECS": ("num", s), "X": ("num", x), "Y": ("num", y)})
def say_secs(msg, s): return ("looks_sayforsecs", {"MESSAGE": msg, "SECS": ("num", s)})
def wait_touch(name): return ("control_wait_until", {"CONDITION": ("touching", name)})
def key(name): return {"KEY_OPTION": [name, None]}


def explorer(start=True, hello=True, hello_first=False, my_xy=True, step=10, left=-10, up=10, down=-10, robot=None,
             right_goto=False, treasure_script=None, robot_spots=SPOTS, space_ship=False):
    s = Script()
    flag = []
    if hello and hello_first: flag.append(say_secs(("text", "보물을 찾으러 가자!"), 2))
    if start: flag.append(gotoxy(-180, -120))
    if hello and not hello_first: flag.append(say_secs(("text", "보물을 찾으러 가자!"), 2))
    s.stack("event_whenflagclicked", flag)
    if treasure_script:  # 오개념: 보물 스크립트를 탐험가에 만듦
        s.stack("event_whenflagclicked", treasure_script)
    if right_goto:  # 오개념: 바꾸기 대신 이동하기
        s.stack("event_whenkeypressed", [gotoxy(10, 0)], key("right arrow"))
    else:
        s.stack("event_whenkeypressed", [("motion_changexby", {"DX": ("num", step)})], key("right arrow"))
    s.stack("event_whenkeypressed", [("motion_changexby", {"DX": ("num", left)})], key("left arrow"))
    s.stack("event_whenkeypressed", [("motion_changeyby", {"DY": ("num", up)})], key("up arrow"))
    s.stack("event_whenkeypressed", [("motion_changeyby", {"DY": ("num", down)})], key("down arrow"))
    if my_xy:
        s.stack("event_whenkeypressed", [say_secs(("rep", "motion_xposition"), 1), say_secs(("rep", "motion_yposition"), 1)], key("space"))
    if robot:
        s.stack("event_whenkeypressed", [glide(robot, x, y) for x, y in robot_spots], key("a"))
    if space_ship:  # 오개념: 미션 C를 스페이스 키로 만들어 좌표 말하기와 겹침
        s.stack("event_whenkeypressed", [gotoxy(-180, -120)], key("space"))
    return s.blocks


def treasure_body(spots=SPOTS, wait=True, found=True, finish=True, fifth_wait=True, ghost=False, touch="탐험가"):
    """정답: 자리마다 이동 → 기다리기 → (네 번째까지) 찾았다! → 다섯 번째를 찾으면 곧바로 (타이머) 말하기"""
    body = [("looks_seteffectto", {"VALUE": ("num", 100)}, {"EFFECT": ["GHOST", None]})] if ghost else []
    for i, (x, y) in enumerate(spots):
        body.append(gotoxy(x, y))
        last = i == len(spots) - 1
        if wait and (fifth_wait or not last): body.append(wait_touch(touch))
        if wait and found and not last: body.append(say_secs(("text", "찾았다!"), 1))
    if finish: body.append(("looks_say", {"MESSAGE": ("rep", "sensing_timer")}))
    return body


def treasure(**kw):
    s = Script()
    s.stack("event_whenflagclicked", treasure_body(**kw))
    return s.blocks


VARIANTS = {
    "solution": (explorer(), treasure()),
    "core": (explorer(hello=False, my_xy=False), treasure(found=False)),
    "wrong-hello-first": (explorer(hello_first=True), treasure()),
    "wrong-no-start": (explorer(start=False), treasure()),
    "wrong-step20": (explorer(step=20, left=-20, up=20, down=-20), treasure()),
    "wrong-left-plus": (explorer(left=10), treasure()),
    "wrong-up-minus": (explorer(up=-10, down=10), treasure()),
    "wrong-no-wait": (explorer(), treasure(wait=False)),
    "wrong-swap34": (explorer(), treasure(spots=[SPOTS[0], SPOTS[1], SPOTS[3], SPOTS[2], SPOTS[4]])),
    "wrong-no-finish": (explorer(), treasure(finish=False)),
    "wrong-no-fifth-wait": (explorer(), treasure(fifth_wait=False)),
    "wrong-arrow-goto": (explorer(right_goto=True), treasure()),
    "wrong-script-in-explorer": (explorer(treasure_script=treasure_body(touch="보물")), {}),
    "robot-2s": (explorer(robot=2), treasure()),
    "robot-1s": (explorer(robot=1), treasure()),
    "mission-e": (explorer(), treasure(ghost=True)),
    "robot-swap34": (explorer(robot=2, robot_spots=[SPOTS[0], SPOTS[1], SPOTS[3], SPOTS[2], SPOTS[4]]), treasure()),
    "wrong-space-twice": (explorer(space_ship=True), treasure()),
}

if __name__ == "__main__":
    with zipfile.ZipFile(STARTER) as z:
        base = json.loads(z.read("project.json"))
        assets = {n: z.read(n) for n in z.namelist() if n != "project.json"}

    for name, (ex_blocks, tr_blocks) in VARIANTS.items():
        proj = copy.deepcopy(base)
        for t in proj["targets"]:
            if t["name"] == "탐험가": t["blocks"] = ex_blocks
            if t["name"] == "보물": t["blocks"] = tr_blocks
        path = os.path.join(OUT, name + ".sb3")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("project.json", json.dumps(proj, ensure_ascii=False))
            for n, data in assets.items(): z.writestr(n, data)
    for f in os.listdir(OUT):  # 없어진 작품의 파일은 지운다
        if f.endswith(".sb3") and f[:-4] not in VARIANTS: os.remove(os.path.join(OUT, f))
    print("tests:", ", ".join(VARIANTS))
