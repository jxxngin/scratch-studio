# -*- coding: utf-8 -*-
"""해적선 대포 합친 교안(버전 2 폴더)의 unit.json과 강사용 안내서를 만든다.

실행: python tools/04-pirate-cannon-v2/build_unit.py
원본: project/lv1/04-pirate-cannon/unit.json (버전 1), docs/teacher-guides/lv1-04-pirate-cannon.md
결과: project/lv1/04-pirate-cannon-v2/unit.json, docs/teacher-guides/lv1-04-pirate-cannon-v2.md

버전 1의 분량, 글, 확장 미션은 그대로 두고 아래만 바꾼다 (README "합치기 계획").
- 만들기 스텝: 맨 위에 목표, 그 아래 미리보기 GIF, 안내, 맨 아래 해 보기(버전 1의 "확인", "도전", "해 보기" 문단)
- 탐색 스텝: 제목 앞에 "탐색:" (작품에 남지 않는 활동, 채점 없음. s16, s17만 복구 확인)
- 꾸미기 스텝: 제목 앞에 "꾸미기(선택):"
- 퀴즈: 기획서 6장 형식(kind, key, question)으로. 스텝마다 2~3문항, 해설은 남기고 힌트는 뺀다
  (뺀 문항과 힌트는 강사용 안내서로)
- 포수 시험 자리에 완성 확인 스텝 (기록표는 그대로)
- 블록 이름은 버전 1처럼 코드 표기, 스텝 키도 버전 1 그대로

버전 1을 고친 뒤에는 이 스크립트를 다시 돌려 합친 교안에 반영한다.
버전 1을 합친 교안으로 바꾸고 나면 이 스크립트는 지운다.
"""
import copy, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "project", "lv1", "04-pirate-cannon", "unit.json")
OUT = os.path.join(ROOT, "project", "lv1", "04-pirate-cannon-v2", "unit.json")
GUIDE_SRC = os.path.join(ROOT, "docs", "teacher-guides", "lv1-04-pirate-cannon.md")
GUIDE_OUT = os.path.join(ROOT, "docs", "teacher-guides", "lv1-04-pirate-cannon-v2.md")

v1 = json.load(open(SRC, encoding="utf-8"))
unit = copy.deepcopy(v1)
S = {s["key"]: s for s in unit["steps"]}

def L(ko, en): return {"ko": ko, "en": en}
def text(ko, en): return {"type": "text", "value": L(ko, en)}

# ---------------------------------------------------------------- 채점 도우미
ANGLE = L("각도", "angle")
HITS = L("명중", "hits")
FLAG = [{"do": "greenFlag"}, {"do": "wait", "ms": 300}]
FIRE = [{"do": "keyPress", "key": " ", "durationMs": 50}]
def press(key, n):
    a = []
    for _ in range(n):
        a += [{"do": "keyPress", "key": key, "durationMs": 50}, {"do": "wait", "ms": 120}]
    return a
def wait(ms): return [{"do": "wait", "ms": ms}]
HIT1 = FLAG + press("ArrowUp", 9) + FIRE + wait(1800)
HIT2 = HIT1 + press("ArrowDown", 3) + FIRE + wait(2200)
HIT3 = HIT2 + press("ArrowDown", 3) + FIRE
def var_is(name, v): return {"target": "variable", "name": name, "op": "eq", "value": v}
def spr(s, p, op, v, tol=None):
    e = {"target": "sprite", "sprite": s, "property": p, "op": op, "value": v}
    if tol is not None: e["tolerance"] = tol
    return e
def dyn(actions, expect, timeout):
    return {"type": "dynamic", "actions": actions, "expect": expect, "timeoutMs": timeout}

# ---------------------------------------------------------------- 만들기 스텝: 목표와 GIF
MAKE = {
    "s05-cannon-dance": (
        ["대포를 클릭하면 0 → 45 → 90 → 180 → 90 순서로 돌고, 마지막에 오른쪽(90)을 봐요."],
        ["Click the cannon: it turns 0 → 45 → 90 → 180 → 90 and ends facing right (90)."],
        "s05-dance.gif", "대포를 클릭하면 위, 오른쪽 위, 오른쪽, 아래를 차례로 봤다가 오른쪽으로 돌아온다",
        "Clicking the cannon turns it up, up-right, right and down, then back to right"),
    "s06-angle-variable": (
        ["무대 왼쪽 위에 `각도 0`이 보여요."],
        ["`angle 0` shows at the top left of the stage."],
        "s06-angle-var.gif", "무대 왼쪽 위에 각도 0 표시가 나타난다",
        "An angle 0 display appears at the top left of the stage"),
    "s08-ready": (
        ["깃발을 누르면 대포가 오른쪽(90)을 보고 `각도`가 90이 돼요."],
        ["Click the flag: the cannon faces right (90) and `angle` becomes 90."],
        "s08-ready.gif", "위를 보던 대포가 깃발을 누르자 오른쪽을 보고 각도가 90이 된다",
        "The cannon facing up turns right on the flag, and angle becomes 90"),
    "s09-up": (
        ["위쪽 화살표를 누를 때마다 대포가 5도씩 위로 들리고 `각도`가 5씩 줄어요."],
        ["Each up-arrow press lifts the cannon 5 degrees and `angle` goes down by 5."],
        "s09-up.gif", "위쪽 화살표를 누를 때마다 대포가 조금씩 위로 들린다",
        "The cannon tilts up a little with each up-arrow press"),
    "s10-down": (
        ["아래쪽 화살표를 누를 때마다 대포가 5도씩 아래로 내려가고 `각도`가 5씩 늘어요."],
        ["Each down-arrow press lowers the cannon 5 degrees and `angle` goes up by 5."],
        "s10-down.gif", "아래쪽 화살표를 누를 때마다 대포가 조금씩 아래로 내려간다",
        "The cannon tilts down a little with each down-arrow press"),
    "s11-say-angle": (
        ["화살표를 누를 때마다 대포가 지금 각도를 말해요."],
        ["Each arrow press makes the cannon say its angle."],
        "s11-say.gif", "화살표를 누를 때마다 대포가 85, 80처럼 지금 각도를 말한다",
        "The cannon says its angle, like 85 or 80, with each arrow press"),
    "s12-ball-ready": (
        ["깃발을 누르면 포탄이 숨어요.",
         "스페이스를 누르면 포탄이 대포 자리에 나타나 대포와 같은 쪽을 봐요."],
        ["Click the flag: the cannonball hides.",
         "Press space: the cannonball appears at the cannon, facing the same way."],
        "s12-load.gif", "깃발을 누르면 포탄이 사라지고, 스페이스를 누르면 대포 위에 다시 나타난다",
        "The cannonball disappears on the flag and reappears on the cannon on space"),
    "s13-fly": (
        ["스페이스를 누르면 포탄이 대포가 보는 쪽으로 날아가다 사라져요."],
        ["Press space: the cannonball flies where the cannon points, then disappears."],
        "s13-fly.gif", "포탄이 대포가 보는 쪽으로 곧게 날아가다 사라진다",
        "The cannonball flies straight where the cannon points, then disappears"),
    "s18-target-ready": (
        ["깃발을 누르면 과녁이 첫 자리(x: -36, y: 64)로 가고 `명중`이 0이 돼요."],
        ["Click the flag: the target goes to its first spot (x: -36, y: 64) and `hits` becomes 0."],
        "s18-target-ready.gif", "다른 곳에 옮겨 둔 과녁이 깃발을 누르자 첫 자리로 돌아오고 명중이 0이 된다",
        "A target dragged away jumps back on the flag, and hits becomes 0"),
    "s18b-if-say": (
        ["45로 쏘면 포탄이 과녁을 지날 때 \"명중!\"이라고 말해요."],
        ["Fire at 45: the cannonball says \"Hit!\" as it passes the target."],
        "s18b-say.gif", "45도로 쏜 포탄이 과녁에 닿는 순간 명중이라고 말하며 지나간다",
        "A shot at 45 says Hit! the moment it touches the target and flies on"),
    "s19-hit": (
        ["맞히면 포탄이 바로 사라지고 `명중`이 1 올라가요.", "빗나가면 `명중`은 그대로예요."],
        ["On a hit, the cannonball vanishes and `hits` goes up by 1.", "On a miss, `hits` stays the same."],
        "s19-hit.gif", "45도로 쏜 포탄이 과녁에 닿자마자 사라지고 명중이 1이 된다",
        "A shot at 45 vanishes the moment it touches the target, and hits becomes 1"),
    "s20-next-spot": (
        ["첫 과녁을 맞히면 과녁이 두 번째 자리(x: 90, y: 80)로 가요."],
        ["After the first hit, the target moves to spot 2 (x: 90, y: 80)."],
        "s20-spot2.gif", "첫 과녁을 맞히자 과녁이 오른쪽 위의 두 번째 자리로 옮겨 간다",
        "After the first hit, the target jumps to the second spot"),
    "s22-three-targets": (
        ["과녁 3개를 차례로 맞히면 과녁이 말을 하고 사라져요."],
        ["Hit all three targets in turn and the target speaks, then disappears."],
        "s22-win.gif", "두 번째와 세 번째 과녁을 맞히자 과녁이 다 맞혔다고 말하고 사라진다",
        "After the second and third hits, the target says you hit them all and disappears"),
}
TRY_KO = ("**확인", "**도전", "**해 보기")
TRY_EN = ("**Check", "**Challenge", "**Try")

def split_try(block):
    """text 블록을 안내 문단과 해 보기 문단으로 나눈다. 두 언어의 문단 수가 같아야 한다."""
    ko = block["value"]["ko"].split("\n\n")
    en = block["value"]["en"].split("\n\n")
    assert len(ko) == len(en), block["value"]["ko"][:30]
    guide, tried = ([], []), ([], [])
    for k, e in zip(ko, en):
        is_try = k.startswith(TRY_KO)
        assert is_try == e.startswith(TRY_EN), k[:30]
        dst = tried if is_try else guide
        dst[0].append(k)
        dst[1].append(e)
    return guide, tried

# s12: 포탄이 대포 위 레이어이므로 "대포에 가려 있다"는 설명을 쓰지 않는다
s12 = S["s12-ball-ready"]["content"][4]["value"]
assert s12["ko"].startswith("포탄은 `각도` 값을 읽어서")
s12["ko"] = (
    "포탄은 `각도` 값을 읽어서 대포와 같은 쪽을 봐요.\n\n"
    "`대포로 이동하기`의 '대포 자리'는 대포가 도는 중심(뒤쪽 둥근 부분)이에요. "
    "포탄은 대포보다 앞에 있어서 그 자리에 바로 보여요.\n\n"
    "**확인**: 각도를 바꾸고 스페이스를 누르세요. 포탄이 대포 뒤쪽 둥근 부분에 나타나나요? "
    "스프라이트 정보에서 포탄의 방향이 대포와 같은지도 보세요. (아직 날아가지 않아요)")
s12["en"] = (
    "The cannonball reads `angle` to face the same way as the cannon.\n\n"
    "\"Go to 대포\" moves it to the point the cannon turns around (the round back end). "
    "The cannonball is in front of the cannon, so you can see it there.\n\n"
    "**Check**: Change the angle and press space. Does the cannonball appear on the round back end "
    "of the cannon? In the sprite info, check that its direction matches the cannon's. "
    "(It doesn't fly yet.)")

for key, (goal_ko, goal_en, gif, alt_ko, alt_en) in MAKE.items():
    step = S[key]
    guide, tried = [], ([], [])
    for block in step["content"]:
        if block["type"] != "text":
            guide.append(block)
            continue
        (gk, ge), (tk, te) = split_try(block)
        if gk:
            guide.append(text("\n\n".join(gk), "\n\n".join(ge)))
        tried[0].extend(tk)
        tried[1].extend(te)
    content = [
        text("**목표**\n" + "\n".join("- " + g for g in goal_ko),
             "**Goal**\n" + "\n".join("- " + g for g in goal_en)),
        {"type": "image", "src": "media/" + gif, "alt": L(alt_ko, alt_en)},
    ] + guide
    if tried[0]:
        content.append(text("\n\n".join(tried[0]), "\n\n".join(tried[1])))
    step["content"] = content

# 말풍선 채점은 언어별 값으로 (영어 교안은 "Hit!"를 말하게 한다)
s18b = S["s18b-if-say"]["checks"][0]["expect"][0]
assert s18b["property"] == "sayText"
s18b["value"] = L("명중", "Hit")
# 목표 문장("말을 하고 사라져요")에 맞춰 사라지는 것까지 확인한다
S["s22-three-targets"]["checks"] = [
    dyn(HIT3 + wait(4200), [var_is(HITS, 3), spr("과녁", "visible", "eq", False)], 16000)]

# ---------------------------------------------------------------- 탐색, 꾸미기 스텝
EXPLORE = {
    "s04-direction": ("방향 블록 눌러 보기", "Click the direction block"),
    "s07-variable-play": ("변수 놀이터", "Variable playground"),
    "s16-range": ("사거리 바꾸기", "Change the range"),
    "s17-five-degrees": ("5도 차이는 얼마나 클까?", "How big is 5 degrees?"),
    "s18a-touching": ("닿았는지 손으로 확인하기", "Check touching by hand"),
}
for key, (ko, en) in EXPLORE.items():
    S[key]["title"] = L("탐색: " + ko, "Explore: " + en)

s23 = S["s23-shots"]
s23["title"] = L("꾸미기(선택): 발사 수 세기", "Decorate (optional): count your shots")
v = s23["content"][0]["value"]
assert v["ko"].startswith("**선택 단계예요.**")
v["ko"] = v["ko"].replace("**선택 단계예요.**", "**꾸미기 단계예요.**", 1)
v["en"] = v["en"].replace("**This step is optional.**", "**This is a decorating step.**", 1)

# ---------------------------------------------------------------- 퀴즈
QUIZ_KEEP = {
    "q1-direction": ["q1-1", "q1-3", "q1-4"],
    "q3-aim": ["q3-1", "q3-2", "q3-4"],
    "q5-hit": ["q5-1", "q5-3", "q5-4"],
    "q6-wrap": ["q6-1", "q6-3", "q6-4"],
}
dropped = []
for key, keep in QUIZ_KEEP.items():
    step = S[key]
    qs = []
    for q in step["questions"]:
        if q["id"] not in keep:
            dropped.append((key, q))
            continue
        item = {"key": q["id"], "question": q["prompt"]}
        for f in ("image", "blocks"):
            if f in q: item[f] = q[f]
        item["options"] = q["options"]
        item["answer"] = q["answer"]
        item["explain"] = q["explain"]
        qs.append(item)
    assert 2 <= len(qs) <= 3, key
    S[key] = {"key": key, "kind": "quiz", "title": step["title"], "questions": qs}

# ---------------------------------------------------------------- 완성 확인 (포수 시험 자리)
s24 = S["s24-gunner-test"]
s24["title"] = L("완성 확인: 포수 시험", "Final check: gunner's test")
v1_s24 =[b for b in next(s for s in v1["steps"] if s["key"] == "s24-gunner-test")["content"]]
s24["content"] = [
    text("**목표**\n"
         "- 깃발을 누르면 대포는 오른쪽, `각도`는 90, `명중`은 0이고 과녁은 첫 자리에 있어요.\n"
         "- 화살표로 대포를 돌리고 스페이스로 쏴요.\n"
         "- 과녁 3개를 차례로 맞히면 과녁이 말을 하고 사라져요.",
         "**Goal**\n"
         "- On the flag, the cannon faces right, `angle` is 90, `hits` is 0 and the target is at spot 1.\n"
         "- Turn the cannon with the arrows and fire with space.\n"
         "- Hit all three targets in turn and the target speaks, then disappears."),
    text("꾸미기나 실험을 하다 바꾼 곳이 있으면 먼저 되돌려 놓아요. "
         "반복은 40번, 10걸음이고, 스페이스 스크립트 맨 아래에 `숨기기`가 있어야 해요.",
         "Undo anything you changed while decorating or experimenting. "
         "The repeat should be 40 times, 10 steps, with `hide` at the end of the space script."),
] + v1_s24
s24["checks"] = [
    dyn(HIT3 + wait(4200), [var_is(HITS, 3), spr("과녁", "visible", "eq", False)], 16000),
    dyn(HIT3 + wait(4200) + FLAG + wait(200),
        [var_is(ANGLE, 90), var_is(HITS, 0), spr("대포", "direction", "eq", 90),
         spr("포탄", "visible", "eq", False), spr("과녁", "visible", "eq", True),
         spr("과녁", "x", "eq", -36, 5), spr("과녁", "y", "eq", 64, 5)], 17000),
]

unit["steps"] = [S[s["key"]] for s in v1["steps"]]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    json.dump(unit, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("written", OUT, len(unit["steps"]), "steps")

# ---------------------------------------------------------------- 강사용 안내서
def kind_of(step):
    k = step["key"]
    if step.get("kind") == "quiz": return "퀴즈"
    if k in MAKE: return "만들기"
    if k in EXPLORE: return "탐색"
    if k in ("s14-sound", "s15-flash", "s21-boom", "s23-shots"): return "꾸미기(선택)"
    if k.startswith(("s01", "s02", "s03")): return "이야기"
    if k == "s24-gunner-test": return "완성 확인"
    return "확장 미션"

rows = ["| key | 제목 | 종류 | 자동 검사 | 미리보기 GIF |", "| --- | --- | --- | --- | --- |"]
for step in unit["steps"]:
    checks = step.get("checks", [])
    if step.get("kind") == "quiz":
        auto = "모든 문항 정답 (%d문항)" % len(step["questions"])
    elif not checks:
        auto = "없음"
    else:
        n_dyn = sum(c["type"] == "dynamic" for c in checks)
        auto = "동적 %d" % n_dyn + (", 정적 %d" % (len(checks) - n_dyn) if len(checks) > n_dyn else "")
    gif = MAKE[step["key"]][2] if step["key"] in MAKE else ""
    rows.append("| %s | %s | %s | %s | %s |" % (step["key"], step["title"]["ko"], kind_of(step), auto, gif))
steps_md = "\n".join(rows)

def opt(q, i): return q["options"][i]["ko"]
qrows = ["| 문항 | 화면 | 정답 | 해설(통과 후 화면에 나옴) | 힌트(말로 줄 때) |", "| --- | --- | --- | --- | --- |"]
for step in v1["steps"]:
    if step.get("type") != "quiz": continue
    for q in step["questions"]:
        shown = "남김" if q["id"] in QUIZ_KEEP[step["key"]] else "뺌"
        qrows.append("| %s | %s | %s | %s | %s |" % (
            q["id"], shown, opt(q, q["answer"]), q["explain"]["ko"], q.get("hint", {}).get("ko", "")))
quiz_md = "\n".join(qrows)

g = open(GUIDE_SRC, encoding="utf-8").read()
g = g.replace("`project/lv1/04-pirate-cannon/unit.json`", "`project/lv1/04-pirate-cannon-v2/unit.json`")
g = g.replace("# Lv.1-4 해적선 대포 · 교사용 자료", "# Lv.1-4 해적선 대포 · 교사용 자료 (합친 교안)", 1)
g = g.replace("(s07, q2-2)", "(s07, q1-3)").replace("(s12, q3-4, q6-4,", "(s12, q3-2, q6-4,")
sec2 = re.search(r"## 2\. 단계 구성\n.*?(?=\n## 3\.)", g, re.S)
g = g[:sec2.start()] + (
    "## 2. 단계 구성\n\n"
    "스텝 키는 버전 1과 같다. 만들기 스텝은 목표 → 미리보기 GIF → 안내 → 해 보기 순서이고, "
    "탐색 스텝(작품에 남지 않는 활동)과 꾸미기(선택) 스텝은 채점하지 않는다. "
    "s16, s17만 실험 뒤 복구했는지(반복 40번, 10걸음, 마지막 `숨기기`) 확인한다.\n\n"
    + steps_md + "\n\n"
    "자동 검사는 실행 결과를 보는 동적 검사를 먼저 쓰고, 정적 검사(블록 검사)는 새 블록이 나오는 스텝"
    "(s05, s06, s08, s12, s20)에만 둔다. s18만 예외로, 과녁이 처음부터 첫 자리에 있어 동적 검사로 "
    "구분되지 않으므로 깃발 아래의 이동 블록을 정적으로 확인한다.\n\n"
    "s24는 포수 시험 기록표를 그대로 두고 완성 확인을 더한 스텝이다. 게임 전체(과녁 3개를 맞히고 사라짐)와 "
    "깃발을 다시 눌렀을 때 처음 상태로 돌아오는지를 확인한다. 꾸미기나 실험에서 바꾼 것이 남아 있으면 "
    "여기서 걸린다.\n") + g[sec2.end():]
secq = re.search(r"### 퀴즈 정답과 의도\n.*?(?=\n## 7\.)", g, re.S)
g = g[:secq.start()] + (
    "### 퀴즈 정답과 의도\n\n"
    "퀴즈 스텝마다 2~3문항만 화면에 남겼다. 틀리면 통과/실패만 보여 주고 어느 문항이 틀렸는지, 힌트는 "
    "보여 주지 않는다. 통과하면 문항마다 해설이 나온다. 학생이 막히면 아래 힌트를 말로 주고, "
    "뺀 문항은 수업 중에 말로 묻는 질문으로 쓴다.\n\n"
    + quiz_md + "\n\n"
    "포수 도전(발수)과 설명 도전(이해)은 따로 확인한다. 적게 쏴서 맞힌 학생도 설명 도전 3개를 "
    "말로 할 수 있는지 본다.\n") + g[secq.end():]
with open(GUIDE_OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(g)
print("written", GUIDE_OUT)
