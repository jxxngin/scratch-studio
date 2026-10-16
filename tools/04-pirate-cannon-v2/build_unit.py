"""해적선 대포 버전2의 unit.json을 만든다. 「스크래치 학생용 교안 틀」(docs/scratch-lesson-template.md) 기준.

실행: python tools/04-pirate-cannon-v2/build_unit.py project/lv1/04-pirate-cannon-v2

단원 흐름: 이야기 → 이야기 퀴즈 → 오늘 만들 것 → 만들기 12개 → 코드 퀴즈 → 완성 확인 → 확장 미션 (→ 제출은 사이트가 붙임)
만들기 스텝의 칸: 제목 → 목표 → 미리보기 GIF → 안내(text + blocks) → 해 보기

기획서·교안 틀과 다르게 쓴 것 (dev 메모)
- 코드 퀴즈 문항에 blocks(scratchblocks 코드)를 넣었다. 기획서 6장의 문항 필드(key, question, options, answer)에는 없지만,
  교안 틀의 코드 퀴즈는 "코드를 읽고 결과를 고르는" 문항이라 코드를 보여 줄 칸이 필요하다.
- 스프라이트를 @first 대신 이름(대포, 포탄, 과녁)으로 가리켰다. 스프라이트가 셋이라 @first로는 구분할 수 없다.
- s10은 동적 검사만으로는 구분이 안 돼(과녁이 처음부터 첫 자리에 있음) 정적 검사(underHat)를 함께 썼다.
"""
import json, os, sys

OUT = sys.argv[1]

ANGLE = {"ko": "각도", "en": "angle"}
HITS = {"ko": "명중", "en": "hits"}
SPACE = " "  # KeyboardEvent.key

def L(ko, en): return {"ko": ko, "en": en}
def text(ko, en): return {"type": "text", "value": L(ko, en)}
def blocks(ko, en): return {"type": "blocks", "value": L(ko, en)}
def image(src, ko, en): return {"type": "image", "src": src, "alt": L(ko, en)}
def goal(ko_items, en_items):
    return text("**목표**\n" + "\n".join("- " + s for s in ko_items), "**Goal**\n" + "\n".join("- " + s for s in en_items))

# ---------------------------------------------------------------- 채점 도우미
def press(key, n=1):
    a = []
    for _ in range(n): a += [{"do": "keyPress", "key": key, "durationMs": 50}, {"do": "wait", "ms": 120}]
    return a
def wait(ms): return [{"do": "wait", "ms": ms}]
FLAG = [{"do": "greenFlag"}, {"do": "wait", "ms": 300}]
FIRE = [{"do": "keyPress", "key": SPACE, "durationMs": 50}]
HIT1 = FLAG + press("ArrowUp", 9) + FIRE + wait(1800)          # 45도로 1번 과녁
HIT2 = HIT1 + press("ArrowDown", 3) + FIRE + wait(2200)        # 60도로 2번 과녁
HIT3 = HIT2 + press("ArrowDown", 3) + FIRE                     # 75도로 3번 과녁 (발사 직후)
def var_is(name, v): return {"target": "variable", "name": name, "op": "eq", "value": v}
def spr(s, p, op, v, tol=None):
    e = {"target": "sprite", "sprite": s, "property": p, "op": op, "value": v}
    if tol is not None: e["tolerance"] = tol
    return e
def dyn(actions, expect, timeout): return {"type": "dynamic", "actions": actions, "expect": expect, "timeoutMs": timeout}
def st(rule, **kw): return {"type": "static", "rule": rule, **kw}
def q(key, question, options, answer, code=None):
    item = {"key": key, "question": question, "options": options, "answer": answer}
    if code: item["blocks"] = L(*code)
    return item
def opts(*pairs): return [L(ko, en) for ko, en in pairs]

steps = []

# ---------------------------------------------------------------- 1 이야기
steps.append({"key": "s01-story", "title": L("1도의 차이", "Just one degree"), "content": [
    text("옛날 포수들은 화약 대포로 투석기보다 훨씬 멀리 쐈어요. 그런데 멀리 쏠수록 과녁을 맞히기가 어려워졌어요. 왜 그랬을까요?",
         "Long ago, gunners used gunpowder cannons to shoot much farther than catapults. But the farther they shot, the harder it was to hit. Why?"),
    text("대포가 1도만 틀어져도 1000걸음 앞에서는 17걸음이나 빗나갔거든요. 그래서 포수들은 각도를 재고, 쏘기 전에 각도를 어림하는 연습을 했어요.",
         "Just 1 degree off missed by 17 steps at 1000 steps away. So gunners measured angles and practiced estimating them before firing."),
    text("오늘은 우리가 해적선 포수가 돼요. 다음에서 완성작을 봐요.", "Today you're a pirate gunner. See the finished game next."),
    image("media/s01-story.png", "투석기의 돌보다 대포의 포탄이 훨씬 멀리 날아가는 그림", "A cannonball flies much farther than a catapult's rock"),
]})

# ---------------------------------------------------------------- 2 이야기 퀴즈
steps.append({"key": "q1-story", "kind": "quiz", "questions": [
    q("q1-1", L("대포가 1도만 틀어져도, 과녁이 멀수록 어떻게 될까요?", "If a cannon is off by just 1 degree, what happens as the target gets farther?"),
      opts(("빗나가지 않아요", "It doesn't miss"), ("조금 덜 빗나가요", "It misses by less"),
           ("더 크게 빗나가요", "It misses by more"), ("똑같이 빗나가요", "It misses by the same amount")), 2),
    q("q1-2", L("포수들은 쏘기 전에 무엇을 연습했나요?", "What did gunners practice before firing?"),
      opts(("각도를 어림하는 것", "Estimating the angle"), ("대포를 크게 만드는 것", "Making cannons bigger"),
           ("화약을 줄이는 것", "Using less gunpowder"), ("눈을 감고 쏘는 것", "Firing with eyes closed")), 0),
]})

# ---------------------------------------------------------------- 3 오늘 만들 것
steps.append({"key": "s02-goal", "title": L("오늘 만들 것", "What we'll make"), "content": [
    image("media/s02-preview.gif", "대포를 돌려 쏜 포탄이 과녁 3곳을 차례로 맞히고 과녁이 승리를 외친다",
          "The cannon turns and fires, hits three targets in turn, and the target cheers"),
    text("**꼭 만들 것**\n- 화살표 키로 대포의 각도 바꾸기\n- 스페이스 키로 포탄 쏘기\n- 과녁을 맞히면 명중 세기\n- 과녁 3곳을 차례로 맞히면 승리",
         "**Must-haves**\n- Change the cannon's angle with the arrow keys\n- Fire a cannonball with the space key\n- Count hits\n- Hit three targets in turn to win"),
    text("하나씩 만들어 봐요.", "Let's build it one piece at a time."),
]})

# ---------------------------------------------------------------- 5 만들기
steps.append({"key": "s03-turn", "title": L("대포 돌리기", "Turn the cannon"), "content": [
    goal(["대포를 클릭하면 45를 봤다가 0.5초 뒤 위(0)를 봐요."],
         ["Click the cannon: it faces 45, then up (0) half a second later."]),
    image("media/s03-turn.gif", "대포를 클릭하면 오른쪽 위를 봤다가 위를 본다", "Clicking the cannon turns it up-right, then straight up"),
    text("**방향**: 스프라이트가 보는 쪽을 나타내는 숫자예요. 위가 0, 오른쪽이 90이에요. 대포 옆 각도기의 숫자가 바로 방향이에요.",
         "**Direction**: a number for the way a sprite faces. Up is 0 and right is 90. The protractor next to the cannon shows directions."),
    text("대포 스프라이트를 골라요. **[동작]**(파란색) 꾸러미의 [90 도 방향 보기]를 꺼내 숫자를 바꿔요. [0.5 초 기다리기]는 **[제어]**(주황색) 꾸러미에 있어요.",
         "Pick the 대포 (cannon) sprite. Take [point in direction 90] from **[Motion]** (blue) and change the number. [wait 0.5 seconds] is in **[Control]** (orange)."),
    blocks("이 스프라이트를 클릭했을 때\n(45) 도 방향 보기\n(0.5) 초 기다리기\n(0) 도 방향 보기",
           "when this sprite clicked\npoint in direction (45)\nwait (0.5) seconds\npoint in direction (0)"),
    text("대포를 클릭해 보세요. 0을 180으로 바꾸면 어디를 볼까요?", "Click the cannon. If you change 0 to 180, where will it face?"),
], "checks": [
    st("hasBlock", opcode="motion_pointindirection", sprite="대포"),
    dyn([{"do": "clickSprite", "sprite": "대포"}] + wait(250), [spr("대포", "direction", "eq", 45)], 3000),
    dyn([{"do": "clickSprite", "sprite": "대포"}] + wait(1000), [spr("대포", "direction", "eq", 0)], 3000),
]})

steps.append({"key": "s04-angle-var", "title": L("변수 각도 만들기", "Make the angle variable"), "content": [
    goal(["무대 왼쪽 위에 [각도 0]이 보여요."], ["[angle 0] shows at the top left of the stage."]),
    image("media/s04-angle-var.gif", "무대 왼쪽 위에 각도 0 표시가 나타난다", "An angle 0 display appears at the top left of the stage"),
    text("**변수**: 값을 담아 두는, 이름 붙은 상자예요. 대포가 보는 각도를 담을 변수를 만들어요.",
         "**Variable**: a named box that holds a value. Make one to hold the cannon's angle."),
    text("**[변수]**(주황색) 꾸러미에서 [변수 만들기]를 눌러요. 이름은 각도로 적고 [모든 스프라이트에서 사용]을 골라요. 그래야 포탄도 이 상자를 볼 수 있어요.",
         "In **[Variables]** (orange), click [Make a Variable]. Name it angle and choose [For all sprites]. Then the cannonball can read this box too."),
    text("무대 왼쪽 위를 보세요. [각도 0]이 보이나요?", "Look at the top left of the stage. Do you see [angle 0]?"),
], "checks": [
    st("variableExists", kind="variable", name=ANGLE),
]})

steps.append({"key": "s05-ready", "title": L("대포 준비하기", "Get the cannon ready"), "content": [
    goal(["깃발을 누르면 대포가 오른쪽(90)을 보고, 무대의 각도가 90이 돼요."],
         ["Click the green flag: the cannon faces right (90) and angle becomes 90."]),
    image("media/s05-ready.gif", "위를 보던 대포가 깃발을 누르자 오른쪽을 보고 각도가 90이 된다",
          "The cannon facing up turns right when the flag is clicked, and angle becomes 90"),
    text("[변수] 꾸러미의 [각도 을(를) 90 로 정하기]를 깃발 블록 아래에 붙여요. 그 아래에 [90 도 방향 보기]를 붙이고, 숫자 칸에 둥근 [각도] 블록을 끼워요. 이제 대포는 각도 상자에 든 숫자 쪽을 봐요.",
         "Snap [set angle to 90] from [Variables] under the flag block. Add [point in direction 90] below it and drop the round [angle] block into its number slot. Now the cannon faces the number in the angle box."),
    blocks("@greenFlag 클릭했을 때\n[각도 v] 을\\(를\\) (90) 로 정하기\n(각도) 도 방향 보기",
           "when green flag clicked\nset [angle v] to (90)\npoint in direction (angle)"),
    text("대포를 클릭해 위를 보게 한 뒤 깃발을 눌러 보세요. 대포가 다시 오른쪽을 보나요?",
         "Click the cannon so it faces up, then click the flag. Does it face right again?"),
], "checks": [
    st("underHat", hat="event_whenflagclicked", opcode="data_setvariableto"),
    dyn([{"do": "clickSprite", "sprite": "대포"}] + wait(1000) + FLAG,
        [var_is(ANGLE, 90), spr("대포", "direction", "eq", 90)], 4000),
]})

steps.append({"key": "s06-up", "title": L("대포 들어 올리기", "Lift the cannon"), "content": [
    goal(["위쪽 화살표를 누를 때마다 대포가 5도씩 위로 들려요."], ["Each press of the up arrow lifts the cannon 5 degrees."]),
    image("media/s06-up.gif", "위쪽 화살표를 누를 때마다 대포가 조금씩 위로 들린다", "The cannon tilts up a little with each up-arrow press"),
    text("[각도 을(를) -5 만큼 바꾸기]는 상자에 든 숫자를 5 줄여요. 각도기를 보면 위로 갈수록 숫자가 작아지지요. 숫자를 바꾼 다음에는 [(각도) 도 방향 보기]로 대포를 돌려요.",
         "[change angle by -5] makes the number in the box 5 smaller. On the protractor, numbers get smaller going up. After changing the number, turn the cannon with [point in direction (angle)]."),
    blocks("[위쪽 화살표 v] 키를 눌렀을 때\n[각도 v] 을\\(를\\) (-5) 만큼 바꾸기\n(각도) 도 방향 보기",
           "when [up arrow v] key pressed\nchange [angle v] by (-5)\npoint in direction (angle)"),
    text("깃발을 누르고 위쪽 화살표를 두 번 눌러 보세요. 각도가 80이 되나요?", "Click the flag and press the up arrow twice. Is angle 80?"),
], "checks": [
    st("hasBlock", opcode="data_changevariableby", sprite="대포"),
    dyn(FLAG + press("ArrowUp", 2) + wait(200), [var_is(ANGLE, 80), spr("대포", "direction", "eq", 80)], 4000),
]})

steps.append({"key": "s07-down", "title": L("대포 내리기", "Lower the cannon"), "content": [
    goal(["아래쪽 화살표를 누를 때마다 대포가 5도씩 아래로 내려가요."], ["Each press of the down arrow lowers the cannon 5 degrees."]),
    image("media/s07-down.gif", "아래쪽 화살표를 누를 때마다 대포가 조금씩 아래로 내려간다", "The cannon tilts down a little with each down-arrow press"),
    text("위쪽 화살표 스크립트를 오른쪽 클릭해 [복사하기]를 눌러요. 어떤 키를 골라야 할까요? 숫자는 얼마로 바꿔야 할까요?",
         "Right-click the up-arrow script and choose [Duplicate]. Which key should it use? What number should it change by?"),
    text("깃발을 누르고 아래쪽 화살표를 한 번 눌러 보세요. 각도가 95가 되나요?", "Click the flag and press the down arrow once. Is angle 95?"),
], "checks": [
    dyn(FLAG + press("ArrowDown", 1) + wait(200), [var_is(ANGLE, 95), spr("대포", "direction", "eq", 95)], 4000),
]})

steps.append({"key": "s08-load", "title": L("포탄 장전하기", "Load the cannonball"), "content": [
    goal(["깃발을 누르면 포탄이 숨어요.", "스페이스 키를 누르면 포탄이 대포 자리에 나타나 대포와 같은 쪽을 봐요."],
         ["Click the flag: the cannonball hides.", "Press space: the cannonball appears at the cannon, facing the same way."]),
    image("media/s08-load.gif", "깃발을 누르면 포탄이 사라지고, 스페이스 키를 누르면 대포 위에 다시 나타난다",
          "The cannonball disappears on the flag and reappears on the cannon when space is pressed"),
    text("포탄 스프라이트를 골라요. **[형태]**(보라색) 꾸러미의 [숨기기]를 깃발 블록 아래에 붙여요.",
         "Pick the 포탄 (cannonball) sprite. Snap [hide] from **[Looks]** (purple) under the flag block."),
    blocks("@greenFlag 클릭했을 때\n숨기기", "when green flag clicked\nhide"),
    text("[동작] 꾸러미의 [대포 (으)로 이동하기]로 포탄을 대포 자리에 보내요. 방향 칸에 [각도]를 넣으면 포탄이 대포와 같은 쪽을 봐요.",
         "Use [go to 대포] from [Motion] to send the cannonball to the cannon. Put [angle] in the direction slot so it faces the same way as the cannon."),
    blocks("[스페이스 v] 키를 눌렀을 때\n[대포 v] \\(으\\)로 이동하기\n(각도) 도 방향 보기\n보이기",
           "when [space v] key pressed\ngo to [대포 v]\npoint in direction (angle)\nshow"),
    text("깃발을 누르고 스페이스 키를 눌러 보세요. 포탄이 대포 위에 나타나나요?", "Click the flag, then press space. Does the cannonball appear on the cannon?"),
], "checks": [
    dyn(FLAG + wait(200), [spr("포탄", "visible", "eq", False)], 3000),
    dyn(FLAG + press("ArrowUp", 2) + FIRE + wait(150),
        [spr("포탄", "visible", "eq", True), spr("포탄", "direction", "eq", 80), spr("포탄", "x", "eq", -170, 10)], 4000),
]})

steps.append({"key": "s09-fly", "title": L("포탄 쏘기", "Fire the cannonball"), "content": [
    goal(["스페이스 키를 누르면 포탄이 대포가 보는 쪽으로 날아가다 사라져요."], ["Press space: the cannonball flies where the cannon points, then disappears."]),
    image("media/s09-fly.gif", "포탄이 대포가 보는 쪽으로 곧게 날아가다 사라진다", "The cannonball flies straight where the cannon points, then disappears"),
    text("포탄이 10걸음씩 40번 움직이게 해요. [제어] 꾸러미의 어떤 블록으로 [10 만큼 움직이기]를 감싸야 할까요? 다 날아간 뒤에는 무엇을 붙여야 사라질까요?",
         "Make the cannonball move 10 steps, 40 times. Which [Control] block should wrap [move 10 steps]? What goes after it so the cannonball disappears?"),
    text("60도로 한 번, 65도로 한 번 쏴 보세요. 대포 바로 앞과 무대 끝에서 두 길은 얼마나 벌어지나요?",
         "Fire once at 60 and once at 65. How far apart are the two paths near the cannon and at the edge of the stage?"),
], "checks": [
    dyn(FLAG + press("ArrowUp", 2) + FIRE + wait(300), [spr("포탄", "x", "gt", -150), spr("포탄", "direction", "eq", 80)], 4000),
    dyn(FLAG + FIRE + wait(2500), [spr("포탄", "visible", "eq", False)], 5000),
]})

steps.append({"key": "s10-target-ready", "title": L("과녁 준비하기", "Get the target ready"), "content": [
    goal(["깃발을 누르면 과녁이 첫 자리(x: -36, y: 64)로 가고, 무대의 명중이 0이 돼요."],
         ["Click the flag: the target goes to its first spot (x: -36, y: 64) and hits becomes 0."]),
    image("media/s10-target-ready.gif", "다른 곳에 옮겨 둔 과녁이 깃발을 누르자 첫 자리로 돌아오고 명중이 0이 된다",
          "A target dragged away jumps back to its first spot when the flag is clicked, and hits becomes 0"),
    text("맞힌 수를 셀 변수 명중을 만들어요. 각도처럼 [모든 스프라이트에서 사용]을 골라요.",
         "Make a variable hits to count hits. Choose [For all sprites], like angle."),
    text("과녁 스프라이트에 깃발 스크립트를 만들어요. [명중 을(를) 0 로 정하기], [x: -36 y: 64 (으)로 이동하기], [보이기]를 차례로 붙여요. 각 블록은 어느 꾸러미에 있을까요?",
         "Build a flag script on the 과녁 (target) sprite. Snap [set hits to 0], [go to x: -36 y: 64] and [show] in order. Which category is each block in?"),
    text("과녁을 마우스로 옮긴 뒤 깃발을 눌러 보세요. 과녁이 첫 자리로 돌아오나요?", "Drag the target away, then click the flag. Does it go back to its first spot?"),
], "checks": [
    st("underHat", hat="event_whenflagclicked", opcode="motion_gotoxy"),
    dyn(FLAG, [var_is(HITS, 0), spr("과녁", "visible", "eq", True), spr("과녁", "x", "eq", -36, 5), spr("과녁", "y", "eq", 64, 5)], 3000),
]})

steps.append({"key": "s11-hit", "title": L("명중 알아내기", "Detect a hit"), "content": [
    goal(["과녁을 맞히면 포탄이 바로 사라지고 명중이 1 올라가요.", "빗나가면 명중은 그대로예요."],
         ["On a hit, the cannonball vanishes and hits goes up by 1.", "On a miss, hits stays the same."]),
    image("media/s11-hit.gif", "45도로 쏜 포탄이 과녁에 닿자마자 사라지고 명중이 1이 된다",
          "A shot at 45 vanishes the moment it touches the target, and hits becomes 1"),
    text("포탄은 날아가는 동안 과녁에 닿았는지 계속 확인해야 해요. [만약 ~(이)라면]을 반복 블록 안, [10 만큼 움직이기] 아래에 넣어요.",
         "The cannonball must keep checking for the target while it flies. Put [if ~ then] inside the repeat, under [move 10 steps]."),
    blocks("만약 <[과녁 v] 에 닿았는가?> \\(이\\)라면\n[명중 v] 을\\(를\\) (1) 만큼 바꾸기\n숨기기\n멈추기 [이 스크립트 v]\nend",
           "if <touching [과녁 v]?> then\nchange [hits v] by (1)\nhide\nstop [this script v]\nend"),
    text("[멈추기 이 스크립트]는 [제어] 꾸러미에 있어요. 맞힌 포탄이 더 날아가지 않게 멈춰요.",
         "[stop this script] is in [Control]. It stops the cannonball from flying on after a hit."),
    text("대포를 45도로 맞추고 쏴 보세요. 명중이 1이 되나요?", "Aim at 45 and fire. Does hits become 1?"),
], "checks": [
    dyn(HIT1, [var_is(HITS, 1), spr("포탄", "visible", "eq", False)], 6000),
    dyn(FLAG + FIRE + wait(2500), [var_is(HITS, 0)], 5000),
]})

steps.append({"key": "s12-spot2", "title": L("과녁 옮기기", "Move the target"), "content": [
    goal(["첫 과녁을 맞히면 과녁이 두 번째 자리(x: 90, y: 80)로 가요."], ["After the first hit, the target moves to spot 2 (x: 90, y: 80)."]),
    image("media/s12-spot2.gif", "첫 과녁을 맞히자 과녁이 오른쪽 위의 두 번째 자리로 옮겨 간다",
          "After the first hit, the target jumps to the second spot up and to the right"),
    text("과녁의 깃발 스크립트 아래에 이어 붙여요. [~까지 기다리기]는 조건이 맞을 때까지 그 자리에서 기다리는 블록이에요. [제어] 꾸러미에 있고, [=]는 **[연산]**(초록색) 꾸러미에 있어요.",
         "Attach these below the target's flag script. [wait until] waits right there until its condition is true. It's in [Control], and [=] is in **[Operators]** (green)."),
    blocks("<(명중) = (1)> 까지 기다리기\nx: (90) y: (80) \\(으\\)로 이동하기",
           "wait until <(hits) = (1)>\ngo to x: (90) y: (80)"),
    text("45도로 쏴서 첫 과녁을 맞혀 보세요. 과녁이 옮겨 가나요?", "Hit the first target at 45. Does the target move?"),
], "checks": [
    dyn(HIT1, [spr("과녁", "x", "eq", 90, 5), spr("과녁", "y", "eq", 80, 5)], 6000),
]})

steps.append({"key": "s13-spot3", "title": L("세 번째 자리로 옮기기", "Move to spot 3"), "content": [
    goal(["명중이 2가 되면 과녁이 세 번째 자리(x: 207, y: 31)로 가요."], ["When hits reaches 2, the target moves to spot 3 (x: 207, y: 31)."]),
    image("media/s13-spot3.gif", "두 번째 과녁을 맞히자 과녁이 오른쪽 끝의 세 번째 자리로 옮겨 간다",
          "After the second hit, the target jumps to the third spot at the far right"),
    text("앞에서 붙인 두 블록을 복사해 그 아래에 붙여요. 명중이 몇이 될 때까지 기다려야 할까요? x와 y는 얼마로 바꿔야 할까요?",
         "Duplicate the two blocks you just added and attach the copy below them. What should hits equal before it moves? What are the new x and y?"),
    text("두 과녁을 차례로 맞혀 보세요. 두 번째 과녁은 몇 도쯤일까요? 쏘기 전에 각도기로 먼저 어림해요.",
         "Hit both targets in turn. About what angle is the second target? Estimate with the protractor before you fire."),
], "checks": [
    dyn(HIT2, [spr("과녁", "x", "eq", 207, 5), spr("과녁", "y", "eq", 31, 5)], 9000),
]})

steps.append({"key": "s14-win", "title": L("승리 외치기", "Cheer for the win"), "content": [
    goal(["명중이 3이 되면 과녁이 \"승리!\"가 들어간 말을 2초 동안 하고 사라져요."],
         ["When hits reaches 3, the target says something with \"승리!\" for 2 seconds, then disappears."]),
    image("media/s14-win.gif", "세 번째 과녁을 맞히자 과녁이 승리를 외치고 사라진다", "After the third hit, the target cheers and disappears"),
    text("명중이 3이 될 때까지 기다리는 블록을 이어 붙여요. 그 아래에 [형태] 꾸러미의 [안녕! 을(를) 2 초 동안 말하기]와 [숨기기]를 붙여요. 말은 \"승리! 3발 모두 명중!\"으로 바꿔요.",
         "Attach a block that waits until hits is 3. Below it, snap [say Hello! for 2 seconds] and [hide] from [Looks]. Change the words to \"승리! 3발 모두 명중!\"."),
    text("깃발을 누르고 과녁 3개를 모두 맞혀 보세요. 세 번째 과녁은 몇 도일까요?", "Click the flag and hit all three targets. What angle is the third target?"),
], "checks": [
    dyn(HIT3 + wait(1800), [spr("과녁", "sayText", "contains", "승리")], 14000),
    dyn(HIT3 + wait(4200), [var_is(HITS, 3), spr("과녁", "visible", "eq", False)], 16000),
]})

# ---------------------------------------------------------------- 6 코드 퀴즈
steps.append({"key": "q2-code", "kind": "quiz", "questions": [
    q("q2-1", L("위쪽 화살표를 누르면 대포가 위로 5도 들리게 하려면 ?에 무엇을 넣어야 할까요?",
                "To lift the cannon 5 degrees with the up arrow, what goes in the ?"),
      opts(("90", "90"), ("0", "0"), ("5", "5"), ("-5", "-5")), 3,
      ("[위쪽 화살표 v] 키를 눌렀을 때\n[각도 v] 을\\(를\\) (?) 만큼 바꾸기\n(각도) 도 방향 보기",
       "when [up arrow v] key pressed\nchange [angle v] by (?)\npoint in direction (angle)")),
    q("q2-2", L("이 블록들을 위에서부터 차례로 누르면 각도는 얼마가 될까요?", "If you click these from top to bottom, what is angle?"),
      opts(("80", "80"), ("75", "75"), ("85", "85"), ("105", "105")), 1,
      ("[각도 v] 을\\(를\\) (90) 로 정하기\n[각도 v] 을\\(를\\) (-5) 만큼 바꾸기\n[각도 v] 을\\(를\\) (-5) 만큼 바꾸기\n[각도 v] 을\\(를\\) (-5) 만큼 바꾸기",
       "set [angle v] to (90)\nchange [angle v] by (-5)\nchange [angle v] by (-5)\nchange [angle v] by (-5)")),
    q("q2-3", L("만약 블록을 반복 밖으로 옮겼어요. 과녁을 정확히 겨눠 쏘면 어떻게 될까요?",
                "The if block was moved outside the repeat. What happens if you aim right at the target and fire?"),
      opts(("포탄이 날아가지 않아요", "The cannonball doesn't fly"), ("명중이 40 올라가요", "hits goes up by 40"),
           ("포탄이 과녁을 지나쳐 명중이 오르지 않아요", "It flies past the target and hits doesn't go up"),
           ("평소처럼 명중이 1 올라가요", "hits goes up by 1 as usual")), 2,
      ("(40) 번 반복하기\n(10) 만큼 움직이기\nend\n만약 <[과녁 v] 에 닿았는가?> \\(이\\)라면\n[명중 v] 을\\(를\\) (1) 만큼 바꾸기\nend",
       "repeat (40)\nmove (10) steps\nend\nif <touching [과녁 v]?> then\nchange [hits v] by (1)\nend")),
    q("q2-4", L("과녁이 세 번째 자리로 가기 전에 기다리는 조건이에요. ?에 들어갈 숫자는 무엇일까요?",
                "This is the wait before the target moves to spot 3. What number goes in the ?"),
      opts(("2", "2"), ("1", "1"), ("3", "3"), ("0", "0")), 0,
      ("<(명중) = (1)> 까지 기다리기\nx: (90) y: (80) \\(으\\)로 이동하기\n<(명중) = (?)> 까지 기다리기\nx: (207) y: (31) \\(으\\)로 이동하기",
       "wait until <(hits) = (1)>\ngo to x: (90) y: (80)\nwait until <(hits) = (?)>\ngo to x: (207) y: (31)")),
    q("q2-5", L("아래쪽 화살표를 여러 번 누르면 어떻게 될까요?", "What happens if you press the down arrow many times?"),
      opts(("대포가 계속 내려가요", "The cannon keeps going down"),
           ("각도 숫자만 바뀌고 대포는 늘 95를 봐요", "Only angle changes; the cannon always faces 95"),
           ("각도 숫자도 바뀌지 않아요", "angle doesn't change either"), ("대포가 위로 올라가요", "The cannon goes up")), 1,
      ("[아래쪽 화살표 v] 키를 눌렀을 때\n[각도 v] 을\\(를\\) (5) 만큼 바꾸기\n(95) 도 방향 보기",
       "when [down arrow v] key pressed\nchange [angle v] by (5)\npoint in direction (95)")),
]})

# ---------------------------------------------------------------- 7 완성 확인
steps.append({"key": "s15-final", "title": L("처음부터 끝까지 해 보기", "Play from start to finish"), "content": [
    goal(["깃발을 누르면 대포는 오른쪽을 보고, 각도는 90, 명중은 0이 돼요.",
          "화살표 키로 대포를 5도씩 돌리고, 스페이스 키로 포탄을 쏴요.",
          "과녁 3곳을 차례로 다 맞히면 과녁이 승리를 외치고 사라져요."],
         ["Click the flag: the cannon faces right, angle is 90 and hits is 0.",
          "Turn the cannon 5 degrees with the arrow keys and fire with space.",
          "Hit all three targets in turn and the target cheers and disappears."]),
    text("1. 깃발을 눌러요.\n2. 과녁마다 각도를 먼저 어림하고 쏴요.\n3. 과녁 3개를 모두 맞힌 뒤 깃발을 다시 눌러 처음으로 돌아오는지 봐요.",
         "1. Click the flag.\n2. Estimate the angle for each target, then fire.\n3. After all three hits, click the flag again and check that everything resets."),
], "checks": [
    dyn(HIT3 + wait(4200), [var_is(HITS, 3), spr("과녁", "visible", "eq", False)], 16000),
    dyn(HIT3 + wait(4200) + FLAG + wait(200),
        [var_is(ANGLE, 90), var_is(HITS, 0), spr("대포", "direction", "eq", 90), spr("포탄", "visible", "eq", False),
         spr("과녁", "visible", "eq", True), spr("과녁", "x", "eq", -36, 5), spr("과녁", "y", "eq", 64, 5)], 17000),
]})

# ---------------------------------------------------------------- 8 확장 미션
steps.append({"key": "s16-missions", "title": L("확장 미션", "Bonus missions"), "content": [
    text("하나 이상 골라 해 보세요. 끝나면 선생님께 보여 주세요.", "Pick one or more. Show your teacher when you finish."),
    text("**★ 미션 A. 나만의 사격장**\n과녁 3곳의 x, y를 바꿔 나만의 사격장을 만들어요. 짝이 몇 발 만에 다 맞히는지 겨뤄 보세요.",
         "**★ Mission A. My own range**\nChange the x and y of the three spots to make your own range. See how many shots your partner needs."),
    text("**★ 미션 B. 펑! 발사 소리**\n쏠 때마다 포탄의 발사 소리가 나게 해요. [소리] 꾸러미에서 블록을 찾아요.",
         "**★ Mission B. BOOM!**\nPlay the cannonball's 발사 sound each time you fire. Find the block in [Sound]."),
    text("**★★ 미션 C. 포탄은 5발뿐**\n변수 포탄 수를 5로 시작해 쏠 때마다 1씩 줄여요. 0이 되면 더 쏠 수 없게 해요.",
         "**★★ Mission C. Only 5 cannonballs**\nStart a variable shots left at 5 and subtract 1 per shot. Stop firing at 0."),
    text("**★★ 미션 D. 불꽃과 펑**\n쏠 때 대포가 불꽃 모양으로, 맞을 때 과녁이 펑 모양으로 잠깐 바뀌게 해요.",
         "**★★ Mission D. Flash and boom**\nFlash the cannon's 불꽃 costume when firing and the target's 펑 costume on a hit."),
    text("**★★★ 미션 E. 움직이는 과녁**\n과녁이 위아래로 천천히 오르내리게 해요. 언제 쏴야 맞힐 수 있을까요?",
         "**★★★ Mission E. Moving target**\nMake the target bob slowly up and down. When should you fire to hit it?"),
    text("**★★★ 미션 F. 대포가 넘어가지 않게**\n각도가 0보다 작거나 105보다 커지지 않게 막아요.",
         "**★★★ Mission F. Don't flip the cannon**\nKeep the angle from going below 0 or above 105."),
]})

unit = {
    "subject": "scratch-lv1",
    "unitKey": "04-pirate-cannon",
    "order": 4,
    "title": L("해적선 대포", "Pirate Ship Cannon"),
    "starterProject": "starter.sb3",
    "steps": steps,
}
with open(os.path.join(OUT, "unit.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(unit, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("written", os.path.join(OUT, "unit.json"), len(steps), "steps")
