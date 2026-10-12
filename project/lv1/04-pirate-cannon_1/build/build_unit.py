"""Lv.1-4 해적선 대포 unit.json 생성기 (2판: 실습 확장 + 퀴즈 스텝).

- 퀴즈는 steps 배열 안에 "type": "quiz" 스텝으로 넣는다(옵션 A).
- 블록 그림은 scratchblocks 문법. 한국어 블록의 을(를), (으)로, (이)라면은 \\( \\)로 이스케이프한다.
"""
import json, os, sys

OUT = sys.argv[1]

ANGLE = {"ko": "각도", "en": "angle"}
HITS = {"ko": "명중", "en": "hits"}
SHOTS = {"ko": "발사", "en": "shots"}
SPACE = " "  # KeyboardEvent.key

def L(ko, en): return {"ko": ko, "en": en}
def text(ko, en): return {"type": "text", "value": L(ko, en)}
def blocks(pair): return {"type": "blocks", "value": L(pair[0].strip("\n"), pair[1].strip("\n"))}
def image(src, ko, en): return {"type": "image", "src": src, "alt": L(ko, en)}

# ---------------------------------------------------------------- 채점 도우미
def press(key, n=1):
    a = []
    for _ in range(n):
        a += [{"do": "keyPress", "key": key, "durationMs": 50}, {"do": "wait", "ms": 120}]
    return a
def wait(ms): return {"do": "wait", "ms": ms}
FLAG = [{"do": "greenFlag"}, {"do": "wait", "ms": 300}]
FIRE = [{"do": "keyPress", "key": SPACE, "durationMs": 50}]
def var_is(name, v): return {"target": "variable", "name": name, "op": "eq", "value": v}
def spr(s, p, op, v, tol=None):
    e = {"target": "sprite", "sprite": s, "property": p, "op": op, "value": v}
    if tol is not None: e["tolerance"] = tol
    return e
def dyn(actions, expect, timeout): return {"type": "dynamic", "actions": actions, "expect": expect, "timeoutMs": timeout}
def st(rule, **kw): return {"type": "static", "rule": rule, **kw}

# ---------------------------------------------------------------- 퀴즈 도우미
def q(qid, kind, prompt, options, answer, explain, blocks_pair=None, img=None):
    item = {"id": qid, "kind": kind, "prompt": prompt}
    if img: item["image"] = img
    if blocks_pair: item["blocks"] = L(blocks_pair[0].strip("\n"), blocks_pair[1].strip("\n"))
    # 정답 위치가 한쪽에 몰리지 않도록 문항 id로 정해지는 만큼 보기를 돌린다(매번 같은 결과).
    k = sum(map(ord, qid)) % len(options)
    rotated = options[k:] + options[:k]
    item["options"] = rotated
    item["answer"] = (answer - k) % len(options)
    item["explain"] = explain
    return item

def quiz(key, title, questions):
    return {"key": key, "type": "quiz", "title": title, "questions": questions}

# ---------------------------------------------------------------- 블록 (한국어, 영어)
B = {}
B["dir_try"] = (r"(0) 도 방향 보기", r"point in direction (0)")
B["dance"] = (r"""
이 스프라이트를 클릭했을 때
(0) 도 방향 보기
(0.5) 초 기다리기
(45) 도 방향 보기
(0.5) 초 기다리기
""", r"""
when this sprite clicked
point in direction (0)
wait (0.5) seconds
point in direction (45)
wait (0.5) seconds
""")
B["var_play"] = (r"""
[각도 v] 을\(를\) (90) 로 정하기

[각도 v] 을\(를\) (10) 만큼 바꾸기
""", r"""
set [angle v] to (90)

change [angle v] by (10)
""")
B["set_angle"] = (r"""
@greenFlag 클릭했을 때
[각도 v] 을\(를\) (90) 로 정하기
(각도) 도 방향 보기
""", r"""
when green flag clicked
set [angle v] to (90)
point in direction (angle)
""")
B["up"] = (r"""
[위쪽 화살표 v] 키를 눌렀을 때
[각도 v] 을\(를\) (-5) 만큼 바꾸기
(각도) 도 방향 보기
""", r"""
when [up arrow v] key pressed
change [angle v] by (-5)
point in direction (angle)
""")
B["say_angle"] = (r"(각도) 말하기", r"say (angle)")
B["ball_flag"] = (r"""
@greenFlag 클릭했을 때
숨기기
""", r"""
when green flag clicked
hide
""")
B["fire_start"] = (r"""
[스페이스 v] 키를 눌렀을 때
[대포 v] \(으\)로 이동하기
(각도) 도 방향 보기
보이기
""", r"""
when [space v] key pressed
go to [대포 v]
point in direction (angle)
show
""")
B["repeat_hint"] = (r"""
(40) 번 반복하기
(10) 만큼 움직이기
end
""", r"""
repeat (40)
move (10) steps
end
""")
B["sound"] = (r"[발사 v] 재생하기", r"start sound [발사 v]")
B["flash"] = (r"""
[스페이스 v] 키를 눌렀을 때
모양을 [불꽃 v] \(으\)로 바꾸기
(0.1) 초 기다리기
모양을 [대포 v] \(으\)로 바꾸기
""", r"""
when [space v] key pressed
switch costume to [불꽃 v]
wait (0.1) seconds
switch costume to [대포 v]
""")
B["target_start"] = (r"""
@greenFlag 클릭했을 때
[명중 v] 을\(를\) (0) 로 정하기
x: (-36) y: (64) \(으\)로 이동하기
보이기
""", r"""
when green flag clicked
set [hits v] to (0)
go to x: (-36) y: (64)
show
""")
B["hit_hint"] = (r"""
만약 <[목표 v] 에 닿았는가?> \(이\)라면
[명중 v] 을\(를\) (1) 만큼 바꾸기
숨기기
멈추기 [이 스크립트 v]
end
""", r"""
if <touching [목표 v]?> then
change [hits v] by (1)
hide
stop [this script v]
end
""")
B["wait_until"] = (r"""
<(명중) = (1)> 까지 기다리기
x: (90) y: (80) \(으\)로 이동하기
""", r"""
wait until <(hits) = (1)>
go to x: (90) y: (80)
""")
B["boom"] = (r"""
모양을 [펑 v] \(으\)로 바꾸기
(0.3) 초 기다리기
모양을 [과녁 v] \(으\)로 바꾸기
""", r"""
switch costume to [펑 v]
wait (0.3) seconds
switch costume to [과녁 v]
""")
B["win"] = (r"""
[승리! 3발 모두 명중!] 을\(를\) (2) 초 동안 말하기
숨기기
""", r"""
say [You win! 3 hits!] for (2) seconds
hide
""")
B["shots"] = (r"""
[발사 v] 을\(를\) (0) 로 정하기

[발사 v] 을\(를\) (1) 만큼 바꾸기
""", r"""
set [shots v] to (0)

change [shots v] by (1)
""")
# 확장 미션
B["ammo"] = (r"""
만약 <(포탄 수) = (0)> \(이\)라면
[포탄이 없어요!] 을\(를\) (1) 초 동안 말하기
멈추기 [이 스크립트 v]
end
[포탄 수 v] 을\(를\) (-1) 만큼 바꾸기
""", r"""
if <(shots left) = (0)> then
say [Out of cannonballs!] for (1) seconds
stop [this script v]
end
change [shots left v] by (-1)
""")
B["moving"] = (r"""
@greenFlag 클릭했을 때
무한 반복하기
(20) 번 반복하기
y좌표를 (2) 만큼 바꾸기
end
(20) 번 반복하기
y좌표를 (-2) 만큼 바꾸기
end
end
""", r"""
when green flag clicked
forever
repeat (20)
change y by (2)
end
repeat (20)
change y by (-2)
end
end
""")
B["limit"] = (r"""
만약 <(각도) < (0)> \(이\)라면
[각도 v] 을\(를\) (0) 로 정하기
end
""", r"""
if <(angle) < (0)> then
set [angle v] to (0)
end
""")
B["wind"] = (r"y좌표를 (-1) 만큼 바꾸기", r"change y by (-1)")

# 퀴즈용 블록
QB = {}
QB["dance3"] = (r"""
이 스프라이트를 클릭했을 때
(0) 도 방향 보기
(1) 초 기다리기
(90) 도 방향 보기
(1) 초 기다리기
(180) 도 방향 보기
""", r"""
when this sprite clicked
point in direction (0)
wait (1) seconds
point in direction (90)
wait (1) seconds
point in direction (180)
""")
QB["left_blank"] = (r"(?) 도 방향 보기", r"point in direction (?)")
QB["trace"] = (r"""
[각도 v] 을\(를\) (90) 로 정하기
[각도 v] 을\(를\) (-5) 만큼 바꾸기
[각도 v] 을\(를\) (-5) 만큼 바꾸기
[각도 v] 을\(를\) (-5) 만큼 바꾸기
""", r"""
set [angle v] to (90)
change [angle v] by (-5)
change [angle v] by (-5)
change [angle v] by (-5)
""")
QB["up_blank"] = (r"""
[위쪽 화살표 v] 키를 눌렀을 때
[각도 v] 을\(를\) (?) 만큼 바꾸기
(각도) 도 방향 보기
""", r"""
when [up arrow v] key pressed
change [angle v] by (?)
point in direction (angle)
""")
QB["up_plus"] = (r"""
[위쪽 화살표 v] 키를 눌렀을 때
[각도 v] 을\(를\) (5) 만큼 바꾸기
(각도) 도 방향 보기
""", r"""
when [up arrow v] key pressed
change [angle v] by (5)
point in direction (angle)
""")
QB["down_fixed"] = (r"""
[아래쪽 화살표 v] 키를 눌렀을 때
[각도 v] 을\(를\) (5) 만큼 바꾸기
(95) 도 방향 보기
""", r"""
when [down arrow v] key pressed
change [angle v] by (5)
point in direction (95)
""")
QB["goto_blank"] = (r"""
[스페이스 v] 키를 눌렀을 때
[? v] \(으\)로 이동하기
(각도) 도 방향 보기
보이기
""", r"""
when [space v] key pressed
go to [? v]
point in direction (angle)
show
""")
QB["range"] = (r"""
(40) 번 반복하기
(10) 만큼 움직이기
end
""", r"""
repeat (40)
move (10) steps
end
""")
QB["no_hide"] = (r"""
[스페이스 v] 키를 눌렀을 때
[대포 v] \(으\)로 이동하기
(각도) 도 방향 보기
보이기
(40) 번 반복하기
(10) 만큼 움직이기
end
""", r"""
when [space v] key pressed
go to [대포 v]
point in direction (angle)
show
repeat (40)
move (10) steps
end
""")
QB["wait_blank"] = (r"""
<(명중) = (1)> 까지 기다리기
x: (90) y: (80) \(으\)로 이동하기
<(명중) = (?)> 까지 기다리기
x: (207) y: (31) \(으\)로 이동하기
""", r"""
wait until <(hits) = (1)>
go to x: (90) y: (80)
wait until <(hits) = (?)>
go to x: (207) y: (31)
""")
QB["if_outside"] = (r"""
(40) 번 반복하기
(10) 만큼 움직이기
end
만약 <[목표 v] 에 닿았는가?> \(이\)라면
[명중 v] 을\(를\) (1) 만큼 바꾸기
end
""", r"""
repeat (40)
move (10) steps
end
if <touching [목표 v]?> then
change [hits v] by (1)
end
""")

def O(*pairs): return [L(a, b) for a, b in pairs]

steps = []
S = steps.append

# ================================================================ 1부. 이야기
S({"key": "s01-story-cannon", "title": L("투석기에서 대포로", "From catapults to cannons"), "content": [
    text("""## 오늘의 질문: 포탄을 어떻게 과녁에 맞힐까?

옛날 군대는 **투석기**로 돌을 던졌어요. 그러다 화약으로 쏘는 **대포**가 생기자 훨씬, 훨씬 멀리 쏠 수 있게 되었어요.""",
"""## Today's question: how do you hit a target with a cannonball?

Long ago, armies threw rocks with **catapults**. Then gunpowder **cannons** came along and could shoot much, much farther."""),
    image("media/story-catapult-cannon.png", "투석기는 수백 걸음, 대포는 훨씬 멀리 쏘는 모습", "A catapult throws a few hundred steps; a cannon shoots much farther"),
    text("""우리나라 조선 수군도 커다란 대포를 썼어요. **천자총통**은 사람 키보다 긴 쇠촉 화살 **대장군전**을 쏘는 대포예요. 옛 기록에는 대장군전이 **900보**를 날아갔다고 적혀 있어요.

**어림해 보기**: 900걸음이면 우리 학원에서 어디까지 갈 수 있을까요? 짝과 이야기해 보세요.""",
"""Korea's Joseon navy used big cannons too. The **Cheonja chongtong** fired the **Daejanggunjeon**, an iron-tipped arrow longer than a person is tall. Old records say it flew **900 paces**.

**Estimate**: How far from our classroom would 900 steps take you? Talk with your partner."""),
    image("media/story-cheonja.png", "천자총통과 대장군전 그림", "Drawing of the Cheonja chongtong and its giant arrow"),
]})

S({"key": "s02-story-angle", "title": L("포수의 비밀 무기는 '각도'", "A gunner's secret weapon: the angle"), "content": [
    text("""멀리 쏠 수 있게 되자 새 고민이 생겼어요. 대포가 **딱 1도**만 비뚤어져도 이만큼 빗나가요.

| 과녁까지 | 빗나가는 정도 |
| --- | --- |
| 100걸음 | 약 2걸음 |
| 1000걸음 | 약 17걸음 |

그래서 포수들은 대포 입구에 'ㄱ'자 모양 자를 꽂고, 실에 매단 추가 가리키는 눈금으로 각도를 쟀어요.""",
"""Shooting farther brought a new problem. If a cannon is off by **just 1 degree**, it misses by this much:

| Distance | Miss |
| --- | --- |
| 100 steps | about 2 steps |
| 1000 steps | about 17 steps |

So gunners put an L-shaped ruler into the cannon's mouth and read the angle where a hanging weight pointed."""),
    image("media/story-quadrant.png", "대포 입구에 꽂은 각도 자와 추", "An angle ruler in the cannon's mouth with a hanging weight"),
    text("""1537년, 이탈리아의 수학자 **타르탈리아**는 포수들에게 질문 하나당 돈을 받고 답해 주었대요. 그는 대포를 **45도**로 쏘면 포탄이 가장 멀리 날아간다는 것을 알아냈어요.

**그림을 보고 맞혀 보기**: 30도와 60도로 쏜 포탄은 어디에 떨어졌나요?""",
"""In 1537, the Italian mathematician **Tartaglia** reportedly charged gunners for each question he answered. He found that a cannon aimed at **45 degrees** shoots the farthest.

**Look and guess**: Where did the 30-degree and 60-degree shots land?"""),
    image("media/story-45.png", "30도, 45도, 60도로 쏜 포탄의 길", "Paths of shots at 30, 45 and 60 degrees"),
    text("""진짜 포탄은 땅으로 휘어 떨어지지만, 오늘 우리 게임의 포탄은 곧게 날아가요. 휘는 포탄은 확장 미션에서 만들어 볼 수 있어요.""",
"""Real cannonballs curve down to the ground, but today's cannonball flies in a straight line. You can make it curve in a bonus mission."""),
]})

S({"key": "s03-story-pirates", "title": L("오늘 우리는 해적선 포수", "Today you're a pirate gunner"), "content": [
    text("""해적선은 배 옆구리에 대포를 줄줄이 실었어요. 유명한 해적 **검은 수염(블랙비어드)**의 배 '앤 여왕의 복수호'는 1718년 바닷가 모래톱에 걸려 멈췄어요. 이 배는 1996년에 바닷속에서 발견되었고, 지금까지 **대포 20문이 넘게** 건져 올려졌어요.""",
"""Pirate ships carried rows of cannons along their sides. The famous pirate **Blackbeard**'s ship, *Queen Anne's Revenge*, ran aground in 1718. Its wreck was found in 1996, and **more than 20 cannons** have been raised from the sea."""),
    image("media/story-pirate-ship.png", "옆구리에 대포 구멍이 줄지어 있는 해적선", "A pirate ship with a row of cannon ports"),
    text("""## 오늘 만들 게임

화살표 키로 대포 각도를 바꾸고, 스페이스 키로 쏴서 하늘의 **과녁 3개**를 차례로 맞혀요.

**꼭 만들 것**: 각도 조절 · 발사 · 명중 판정 · 과녁 3곳 · 발사 수 세기
**새로 배울 것**: **변수**(이름표 붙은 상자), **방향**(바라보는 쪽을 나타내는 숫자)""",
"""## Today's game

Turn the cannon with the arrow keys, fire with space, and hit **3 targets** in the sky one by one.

**Must-haves**: aiming · firing · hit detection · three targets · counting shots
**New today**: **variables** (labeled boxes) and **direction** (a number for the way a sprite faces)"""),
    image("media/stage-start.png", "오늘 쓸 무대: 해적선, 각도기, 과녁", "Today's stage: ship, protractor and target"),
]})

# ================================================================ 2부. 방향
S({"key": "s04-direction", "title": L("방향 블록 눌러 보기", "Click the direction block"), "content": [
    text("""스크래치는 바라보는 쪽을 **숫자**로 말해요. 시계처럼 **위쪽이 0**, 오른쪽이 90이에요.""",
"""Scratch uses a **number** for the way a sprite faces. Like a clock, **up is 0** and right is 90."""),
    image("media/direction.png", "위 0, 오른쪽 90, 아래 180, 왼쪽 -90", "Up 0, right 90, down 180, left -90"),
    text("""**할 일**
1. 스프라이트 목록에서 **대포**를 고르세요.
2. **동작** 묶음에서 아래 블록을 찾아 숫자를 바꿔 가며 **눌러** 보세요. 누르기 전에 어디를 볼지 먼저 맞혀요!""",
"""**To do**
1. Pick the **대포** (cannon) sprite.
2. Find this block in **Motion**, change the number and **click** it. Guess where it will face first!"""),
    blocks(B["dir_try"]),
    text("""**도전 표**: 맞혔으면 손가락으로 체크!

| 숫자 | 내 예상 | 실제 |
| --- | --- | --- |
| 0 | | |
| 45 | | |
| 180 | | |
| 135 | | |
| -90 | | |

대포 옆의 흰 눈금(각도기)도 같은 숫자를 써요. 45는 직각(90)의 딱 절반이에요.""",
"""**Challenge table**: tick it off when you guess right!

| Number | My guess | Result |
| --- | --- | --- |
| 0 | | |
| 45 | | |
| 180 | | |
| 135 | | |
| -90 | | |

The white protractor marks use the same numbers. 45 is exactly half of a right angle (90)."""),
]})

S({"key": "s05-cannon-dance", "title": L("미션: 대포 체조", "Mission: cannon workout"), "content": [
    text("""대포를 누르면 대포가 **체조**를 하게 만들어요. **대포** 스프라이트에 만드세요.""",
"""Make the cannon do a **workout** when you click it. Build this on the **대포** (cannon) sprite."""),
    blocks(B["dance"]),
    text("""**이어서 스스로**: 45도 다음에 **90 → 180 → 90**도 순서로 돌게 이어 붙이세요. 사이사이에 0.5초씩 기다려요. 마지막에는 오른쪽(90)을 보고 끝나야 해요.

**확인**: 대포를 눌러 보세요. 위 → 오른쪽 위 → 오른쪽 → 아래 → 오른쪽으로 도나요?""",
"""**Continue on your own**: After 45, add **90 → 180 → 90**, waiting 0.5 seconds between each. It must end facing right (90).

**Check**: Click the cannon. Does it go up → up-right → right → down → right?"""),
], "checks": [
    st("hasBlock", opcode="motion_pointindirection", sprite="대포", minCount=5),
    st("underHat", hat="event_whenthisspriteclicked", opcode="control_wait"),
    dyn([{"do": "clickSprite", "sprite": "대포"}, wait(3200)], [spr("대포", "direction", "eq", 90)], 5000),
]})

S(quiz("q1-direction", L("확인 퀴즈: 방향", "Quiz: direction"), [
    q("q1-1", "choice", L("대포가 그림처럼 보고 있어요. 몇 도일까요?", "The cannon faces like this. What is its direction?"),
      O(("0", "0"), ("90", "90"), ("180", "180"), ("-90", "-90")), 0,
      L("스크래치에서는 위쪽이 0도예요.", "In Scratch, up is 0 degrees."), img="media/quiz-cannon-up.png"),
    q("q1-2", "code", L("대포가 **왼쪽**을 보게 하려면 ? 에 무엇을 넣어야 할까요?", "To make the cannon face **left**, what goes in the ? ?"),
      O(("90", "90"), ("-90", "-90"), ("180", "180"), ("0", "0")), 1,
      L("왼쪽은 -90이에요. 270을 넣어도 왼쪽을 보지만 스크래치는 -90으로 바꿔 보여 줘요.", "Left is -90. 270 also faces left, but Scratch shows it as -90."),
      blocks_pair=QB["left_blank"]),
    q("q1-3", "predict", L("이 대포를 누르면 **마지막**에 어느 쪽을 볼까요?", "After clicking, where does the cannon face **at the end**?"),
      O(("위", "Up"), ("오른쪽", "Right"), ("아래", "Down"), ("왼쪽", "Left")), 2,
      L("마지막 블록이 180도라서 아래를 봐요.", "The last block is 180, so it faces down."),
      blocks_pair=QB["dance3"]),
]))

# ================================================================ 3부. 변수
S({"key": "s06-angle-variable", "title": L("변수 '각도' 만들기", "Make the 'angle' variable"), "content": [
    text("""**변수**는 값을 넣어 두는 **이름표 붙은 상자**예요. 대포가 지금 몇 도인지 담을 상자 `각도`를 만들어요.

**할 일**
1. **변수** 묶음 → **변수 만들기**
2. 이름: `각도`
3. **모든 스프라이트에서 사용** 고르고 확인

무대 왼쪽 위에 `각도 0`이 보이면 성공!""",
"""A **variable** is a **labeled box** that holds a value. Make a box called `angle` for the cannon's direction.

**To do**
1. **Variables** → **Make a Variable**
2. Name: `angle`
3. Choose **For all sprites**, then OK

If `angle 0` appears at the top left of the stage, you did it!"""),
    text("""**왜 '모든 스프라이트에서 사용'일까?** 나중에 포탄도 이 상자를 봐야 하거든요. 교실 칠판처럼 모두가 함께 보는 상자예요.""",
"""**Why "For all sprites"?** Later the cannonball needs to read this box too. It's like a whiteboard the whole class can see."""),
], "checks": [st("variableExists", kind="variable", name=ANGLE)]})

S({"key": "s07-variable-play", "title": L("변수 놀이터", "Variable playground"), "content": [
    text("""변수 블록을 **눌러서** 상자 속 숫자가 어떻게 바뀌는지 직접 보세요. 블록을 작업 공간에 꺼내 놓기만 하고 눌러요.""",
"""**Click** the variable blocks and watch the number in the box change. Just drag them into the workspace and click."""),
    blocks(B["var_play"]),
    text("""**실험 표**: 먼저 예상하고 눌러요.

| 할 일 | 내 예상 | 무대의 각도 |
| --- | --- | --- |
| `90로 정하기` 누르기 | | |
| `10만큼 바꾸기` 3번 누르기 | | |
| 숫자를 `-20`으로 고쳐서 1번 누르기 | | |
| `90로 정하기` 다시 누르기 | | |

**발견!** `정하기`는 상자를 **새 값으로 바꿔 넣고**, `바꾸기`는 **지금 값에 더해요**. 실험이 끝나면 꺼낸 블록은 지워도 돼요.""",
"""**Experiment table**: guess first, then click.

| Action | My guess | angle on stage |
| --- | --- | --- |
| Click `set to 90` | | |
| Click `change by 10` three times | | |
| Change it to `-20`, click once | | |
| Click `set to 90` again | | |

**Discovery!** `set` **replaces** the value; `change` **adds to** the current value. You can delete these blocks afterwards."""),
]})

S(quiz("q2-variable", L("확인 퀴즈: 변수", "Quiz: variables"), [
    q("q2-1", "choice", L("변수를 가장 잘 설명한 것은?", "Which best describes a variable?"),
      O(("스프라이트의 모양", "A sprite's costume"), ("값을 담아 두는 이름표 붙은 상자", "A labeled box that holds a value"),
        ("무대의 배경", "The stage backdrop"), ("소리를 내는 블록", "A block that plays sound")), 1,
      L("변수는 이름으로 값을 넣고 꺼내 쓰는 상자예요.", "A variable is a box you read and write by name.")),
    q("q2-2", "predict", L("이 블록들을 위에서부터 차례로 누르면 `각도`는 얼마가 될까요?", "If you click these from top to bottom, what is `angle`?"),
      O(("85", "85"), ("75", "75"), ("80", "80"), ("105", "105")), 1,
      L("90에서 5씩 세 번 빼면 75예요.", "90 minus 5 three times is 75."), blocks_pair=QB["trace"]),
    q("q2-3", "choice", L("`각도`를 '모든 스프라이트에서 사용'으로 만든 까닭은?", "Why did we make `angle` \"For all sprites\"?"),
      O(("숫자가 더 크게 보이려고", "To show the number bigger"), ("포탄도 대포의 각도를 읽을 수 있게", "So the cannonball can read the cannon's angle too"),
        ("대포만 쓸 수 있게", "So only the cannon can use it"), ("블록이 빨리 움직이게", "To make blocks run faster")), 1,
      L("모든 스프라이트가 같은 상자를 보게 하려고요.", "So every sprite sees the same box.")),
]))

S({"key": "s08-ready", "title": L("깃발을 누르면 대포 준비", "Green flag: get the cannon ready"), "content": [
    text("""게임을 시작할 때마다 대포가 **오른쪽(90)**을 보게 해요. **대포**에 만드세요.""",
"""Each time the game starts, the cannon should face **right (90)**. Build this on the **대포** (cannon) sprite."""),
    blocks(B["set_angle"]),
    text("""**포인트**: 두 번째 블록의 숫자 칸에는 숫자 대신 **둥근 `각도` 블록**을 끌어다 넣어요. 그러면 대포가 늘 상자 속 숫자 쪽을 봐요.

**확인**: 대포를 눌러 아래를 보게 한 뒤 깃발을 누르세요. 다시 오른쪽을 보나요?""",
"""**Key point**: Drag the **round `angle` block** into the number slot of the second block. Then the cannon always faces the number in the box.

**Check**: Click the cannon so it ends up facing somewhere else, then click the green flag. Does it face right again?"""),
], "checks": [
    st("hasBlock", opcode="data_setvariableto", sprite="대포"),
    st("underHat", hat="event_whenflagclicked", opcode="motion_pointindirection"),
    dyn(FLAG, [var_is(ANGLE, 90), spr("대포", "direction", "eq", 90)], 3000),
]})

S({"key": "s09-up", "title": L("위쪽 화살표로 대포 들기", "Up arrow lifts the cannon"), "content": [
    blocks(B["up"]),
    text("""**왜 -5일까?** 각도기를 보세요. 대포가 위로 갈수록 숫자가 90 → 60 → 30 → 0으로 **작아져요**. 그래서 빼야 위로 들려요.

**확인**: 깃발 → 위쪽 화살표 두 번 → `각도`가 **80**이고 대포가 조금 들렸나요?""",
"""**Why -5?** Look at the protractor. Going up, the numbers get **smaller**: 90 → 60 → 30 → 0. So we subtract to lift the cannon.

**Check**: Green flag → up arrow twice → is `angle` **80** and the cannon tilted up a little?"""),
], "checks": [
    dyn(FLAG + press("ArrowUp", 2) + [wait(200)], [var_is(ANGLE, 80), spr("대포", "direction", "eq", 80)], 4000),
]})

S({"key": "s10-down", "title": L("아래쪽 화살표는 스스로", "Down arrow on your own"), "content": [
    text("""**아래쪽 화살표**를 누르면 대포가 **5도씩 내려가게** 만들어 보세요.

- 힌트 1: 위쪽 스크립트를 오른쪽 클릭 → **복사하기**
- 힌트 2: 고칠 곳은 **두 군데**예요. 어떤 키? 더할까, 뺄까?

**확인**: 깃발 → 아래쪽 화살표 한 번 → `각도`가 **95**인가요?""",
"""Make the **down arrow** lower the cannon **5 degrees** at a time.

- Hint 1: Right-click the up-arrow script → **Duplicate**
- Hint 2: Change **two** things. Which key? Add or subtract?

**Check**: Green flag → down arrow once → is `angle` **95**?"""),
], "checks": [
    dyn(FLAG + press("ArrowDown", 1) + [wait(200)], [var_is(ANGLE, 95), spr("대포", "direction", "eq", 95)], 4000),
    dyn(FLAG + press("ArrowUp", 3) + press("ArrowDown", 1) + [wait(200)], [var_is(ANGLE, 80)], 5000),
]})

S({"key": "s11-say-angle", "title": L("미션: 대포가 각도를 말해요", "Mission: the cannon says its angle"), "content": [
    text("""포수가 각도를 소리쳐 알려 주듯, 대포가 지금 각도를 **말하게** 해요.

**할 일**: 위쪽, 아래쪽 화살표 스크립트 **맨 아래**에 이 블록을 붙이세요. 말풍선 칸에 둥근 `각도` 블록을 넣어요.""",
"""Like a gunner calling out the angle, make the cannon **say** its current angle.

**To do**: Attach this block to the **bottom** of both arrow scripts. Put the round `angle` block in the speech slot."""),
    blocks(B["say_angle"]),
    text("""**확인**: 위쪽 화살표를 누르면 대포가 "85"라고 말하나요?

**도전**: 각도기 눈금 **60**에 대포를 정확히 맞춰 보세요. 몇 번 눌러야 할까요? 누르기 전에 계산해 보세요.""",
"""**Check**: Press the up arrow. Does the cannon say "85"?

**Challenge**: Line the cannon up exactly with **60** on the protractor. How many presses? Work it out before pressing."""),
], "checks": [
    st("hasBlock", opcode="looks_say", sprite="대포", minCount=2),
    dyn(FLAG + press("ArrowUp", 1) + [wait(200)], [spr("대포", "sayText", "eq", "85")], 4000),
    dyn(FLAG + press("ArrowDown", 1) + [wait(200)], [spr("대포", "sayText", "eq", "95")], 4000),
]})

S(quiz("q3-aim", L("확인 퀴즈: 조준", "Quiz: aiming"), [
    q("q3-1", "code", L("위쪽 화살표를 누르면 대포가 **위로** 5도 들리게 하려면 ? 에 무엇을 넣을까요?", "To lift the cannon **up** 5 degrees, what goes in the ? ?"),
      O(("5", "5"), ("-5", "-5"), ("90", "90"), ("0", "0")), 1,
      L("위로 갈수록 숫자가 작아지니까 -5예요.", "Numbers get smaller going up, so -5."), blocks_pair=QB["up_blank"]),
    q("q3-2", "predict", L("친구가 위쪽 화살표 스크립트를 이렇게 만들었어요. 위쪽 화살표를 누르면?", "A friend built the up-arrow script like this. What happens when you press up?"),
      O(("대포가 위로 들린다", "The cannon tilts up"), ("대포가 아래로 내려간다", "The cannon tilts down"),
        ("아무 일도 없다", "Nothing happens"), ("대포가 사라진다", "The cannon disappears")), 1,
      L("+5를 하면 숫자가 커져서 아래쪽으로 돌아요.", "+5 makes the number bigger, so it turns down."), blocks_pair=QB["up_plus"]),
    q("q3-3", "predict", L("아래쪽 화살표를 **여러 번** 누르면 어떻게 될까요?", "What happens if you press the down arrow **many times**?"),
      O(("대포가 계속 내려간다", "The cannon keeps going down"), ("각도 숫자는 바뀌지만 대포는 늘 95도를 본다", "angle changes, but the cannon always faces 95"),
        ("각도 숫자도 안 바뀐다", "angle doesn't change either"), ("대포가 위로 간다", "The cannon goes up")), 1,
      L("방향 칸에 `각도` 대신 95를 적어서, 상자 숫자가 바뀌어도 대포는 늘 95를 봐요.", "The slot has 95 instead of `angle`, so the cannon always faces 95."),
      blocks_pair=QB["down_fixed"]),
]))

# ================================================================ 4부. 발사
S({"key": "s12-ball-ready", "title": L("포탄 준비", "Load the cannonball"), "content": [
    text("""이제 **포탄** 스프라이트를 고르세요. 시작하면 포탄은 숨어 있어요.""",
"""Now pick the **포탄** (cannonball) sprite. It hides when the game starts."""),
    blocks(B["ball_flag"]),
    text("""스페이스 키를 누르면 포탄이 **대포 자리로 가서, 대포와 같은 쪽을 보고, 나타나요.**""",
"""When space is pressed, the cannonball **goes to the cannon, faces the same way, and appears.**"""),
    blocks(B["fire_start"]),
    text("""**변수의 힘!** 포탄은 대포가 아니지만, `각도` 상자를 보고 대포와 똑같은 쪽을 볼 수 있어요.

**확인**: 각도를 바꾸고 스페이스! 포탄이 대포 끝에 같은 방향으로 나타나나요? (아직 날아가지는 않아요)""",
"""**Variable power!** The cannonball isn't the cannon, but it reads the `angle` box and faces exactly the same way.

**Check**: Change the angle and press space! Does the cannonball appear at the cannon, facing the same way? (It doesn't fly yet.)"""),
], "checks": [
    st("hasBlock", opcode="motion_goto", sprite="포탄"),
    st("underHat", hat="event_whenflagclicked", opcode="looks_hide"),
    dyn(FLAG + [wait(200)], [spr("포탄", "visible", "eq", False)], 3000),
    dyn(FLAG + press("ArrowUp", 2) + FIRE + [wait(150)], [spr("포탄", "visible", "eq", True), spr("포탄", "direction", "eq", 80)], 4000),
]})

S({"key": "s13-fly", "title": L("포탄아 날아라!", "Fly, cannonball!"), "content": [
    text("""포탄이 앞으로 날아가게 해요.

- 질문: 10걸음씩 **40번** 움직이려면 어떤 블록으로 감싸야 할까요? (**제어** 묶음)
- 질문: 다 날아간 뒤 포탄은? (힌트: 처음처럼)

모양이 기억나지 않으면 아래 그림을 보세요.""",
"""Make the cannonball fly forward.

- Question: To move 10 steps **40 times**, which block wraps around it? (**Control**)
- Question: What happens to the cannonball after it lands? (Hint: like at the start)

If you forget the shape, look here."""),
    blocks(B["repeat_hint"]),
    text("""**확인**: 여러 각도로 쏴 보세요. 대포가 보는 쪽으로 날아가다 사라지나요?

**놀아 보기**: 각도기 **0**(바로 위)으로 쏘면? **90**(오른쪽)으로 쏘면? **105**로 쏘면 어디로 갈까요?""",
"""**Check**: Fire at different angles. Does it fly where the cannon points and then disappear?

**Play**: What about **0** (straight up)? **90** (right)? Where does **105** go?"""),
], "checks": [
    st("inside", parent="control_repeat", child="motion_movesteps"),
    dyn(FLAG + press("ArrowUp", 2) + FIRE + [wait(300)], [spr("포탄", "x", "gt", -150), spr("포탄", "direction", "eq", 80)], 4000),
    dyn(FLAG + FIRE + [wait(2500)], [spr("포탄", "visible", "eq", False)], 5000),
]})

S({"key": "s14-sound", "title": L("미션: 펑! 발사 소리", "Mission: BOOM sound"), "content": [
    text("""**포탄** 스프라이트에는 `발사` 소리가 들어 있어요. 스페이스 스크립트에 소리를 넣어 보세요.

- 질문: 소리 블록은 어디에 넣어야 쏘는 순간 "펑!" 할까요? 맨 위? 맨 아래?""",
"""The **포탄** (cannonball) sprite has a sound called `발사`. Add it to the space-key script.

- Question: Where should the sound block go so it booms the moment you fire? Top? Bottom?"""),
    blocks(B["sound"]),
    text("""**주의**: `끝까지 재생하기`가 아니라 `재생하기`를 써요. 왜 그럴까요? 둘 다 써 보고 포탄이 언제 출발하는지 비교해 보세요.""",
"""**Careful**: Use `start sound`, not `play sound until done`. Why? Try both and compare when the cannonball leaves."""),
], "checks": [
    {"type": "anyOf", "checks": [st("hasBlock", opcode="sound_play", sprite="포탄"), st("hasBlock", opcode="sound_playuntildone", sprite="포탄")]},
]})

S({"key": "s15-flash", "title": L("미션: 대포 불꽃", "Mission: muzzle flash"), "content": [
    text("""**대포** 스프라이트에는 `불꽃` 모양이 있어요. 쏘는 순간 대포 끝에서 불꽃이 번쩍하게 만들어요. **대포**에 만드세요.""",
"""The **대포** (cannon) sprite has a `불꽃` (flash) costume. Make it flash when firing. Build this on the cannon."""),
    blocks(B["flash"]),
    text("""**실험**: `0.1초`를 `1초`로 바꾸면 어떻게 보이나요? 가장 멋진 숫자를 골라 보세요(단, 마지막에는 꼭 `대포` 모양으로 돌아와야 해요).""",
"""**Experiment**: What if you change `0.1` to `1`? Pick the coolest number (but it must switch back to the `대포` costume at the end)."""),
], "checks": [
    st("hasBlock", opcode="looks_switchcostumeto", sprite="대포", minCount=2),
    dyn(FLAG + FIRE + [wait(1500)], [spr("대포", "costume", "eq", "대포")], 4000),
]})

S({"key": "s16-range", "title": L("실험: 사거리 바꾸기", "Experiment: change the range"), "content": [
    text("""포탄이 얼마나 멀리 갈지는 **반복 횟수 × 걸음 수**로 정해져요. 바꿔 가며 쏴 보세요.

| 반복 | 걸음 | 내 예상 | 실제로 어디까지? |
| --- | --- | --- | --- |
| 40 | 10 | 무대 오른쪽 끝 근처 | |
| 20 | 10 | | |
| 10 | 10 | | |
| 20 | 20 | | |
| 80 | 5 | | |

- 질문: 20 × 20과 40 × 10은 날아가는 거리가 같아요. 그럼 무엇이 다를까요?
- 질문: 한 번에 **50걸음**씩 뛰면 과녁을 **뛰어넘을** 수도 있어요. 왜 그럴까요?

**끝나면 꼭 40번, 10걸음으로 되돌려 놓으세요.** 그래야 다음 스텝을 통과해요.""",
"""How far the cannonball goes is **repeat count × steps**. Change them and fire.

| Repeat | Steps | My guess | Where did it reach? |
| --- | --- | --- | --- |
| 40 | 10 | near the right edge | |
| 20 | 10 | | |
| 10 | 10 | | |
| 20 | 20 | | |
| 80 | 5 | | |

- Question: 20 × 20 and 40 × 10 reach the same distance. What's different?
- Question: Jumping **50 steps** at a time can **skip over** the target. Why?

**When done, set it back to 40 and 10.** You need that to pass the next steps."""),
], "checks": [
    st("hasBlock", opcode="control_repeat", sprite="포탄", inputs={"TIMES": {"op": "eq", "value": 40}}),
    st("hasBlock", opcode="motion_movesteps", sprite="포탄", inputs={"STEPS": {"op": "eq", "value": 10}}),
]})

S(quiz("q4-fire", L("확인 퀴즈: 발사", "Quiz: firing"), [
    q("q4-1", "code", L("포탄이 대포에서 출발하려면 ? 에 무엇을 골라야 할까요?", "For the cannonball to start at the cannon, what goes in the ? ?"),
      O(("마우스 포인터", "mouse-pointer"), ("무작위 위치", "random position"), ("대포", "대포 (cannon)"), ("목표", "목표 (target)")), 2,
      L("대포 자리로 가야 대포에서 쏜 것처럼 보여요.", "Going to the cannon makes it look like it was fired from there."),
      blocks_pair=QB["goto_blank"]),
    q("q4-2", "predict", L("이 블록대로 날아가면 포탄은 모두 몇 걸음을 움직일까요?", "How many steps does the cannonball move in total?"),
      O(("50걸음", "50 steps"), ("40걸음", "40 steps"), ("400걸음", "400 steps"), ("4000걸음", "4000 steps")), 2,
      L("10걸음씩 40번이면 400걸음이에요.", "10 steps, 40 times, is 400 steps."), blocks_pair=QB["range"]),
    q("q4-3", "predict", L("마지막의 `숨기기`를 빠뜨렸어요. 쏘면 어떻게 될까요?", "The final `hide` is missing. What happens when you fire?"),
      O(("포탄이 날아가지 않는다", "The cannonball doesn't fly"), ("포탄이 날아간 끝자리에 그대로 남는다", "The cannonball stays where it stopped"),
        ("포탄이 대포로 돌아온다", "It returns to the cannon"), ("게임이 멈춘다", "The game stops")), 1,
      L("숨기지 않으면 반복이 끝난 자리에 계속 보여요.", "Without hide, it stays visible where the loop ended."), blocks_pair=QB["no_hide"]),
]))

S({"key": "s17-five-degrees", "title": L("실험: 5도 차이는 얼마나 클까?", "Experiment: how big is 5 degrees?"), "content": [
    text("""포수처럼 실험해요. 포탄이 멈춘 자리를 보려면 **잠깐** 스페이스 스크립트 맨 아래의 `숨기기`를 떼어 놓으세요.

1. 각도 **60**으로 쏘기 → 포탄이 멈춘 자리를 기억
2. 각도 **65**로 쏘기 → 아까 자리와 비교
3. 이번엔 반복을 **10번**으로 줄여서 60, 65로 다시 쏘기 (가까운 거리)

- 질문: 가까이에서와 멀리에서, 두 포탄 사이가 어디서 더 벌어졌나요?""",
"""Experiment like a gunner. To see where the cannonball stops, **temporarily** detach the final `hide` block.

1. Fire at **60** → remember where it stopped
2. Fire at **65** → compare
3. Change the repeat to **10** and fire at 60 and 65 again (short distance)

- Question: Were the two cannonballs farther apart up close or far away?"""),
    image("media/angle-gap.png", "60도와 65도로 쏜 길이 멀리 갈수록 벌어지는 그림", "Paths at 60 and 65 degrees spreading wider with distance"),
    text("""같은 5도인데 **멀리 갈수록 크게 벌어져요**. 이야기 속 포수들이 1도까지 꼼꼼히 잰 이유예요.

**실험이 끝나면** 반복을 40으로, `숨기기`를 제자리에 붙여 두세요.""",
"""The same 5 degrees **spreads wider the farther it goes**. That's why gunners measured every single degree.

**When you're done**, set the repeat back to 40 and reattach `hide`."""),
], "checks": [
    st("hasBlock", opcode="control_repeat", sprite="포탄", inputs={"TIMES": {"op": "eq", "value": 40}}),
    dyn(FLAG + FIRE + [wait(2500)], [spr("포탄", "visible", "eq", False)], 5000),
]})

# ================================================================ 5부. 명중
S({"key": "s18-target-ready", "title": L("변수 '명중'과 과녁 준비", "The 'hits' variable and the target"), "content": [
    text("""맞힌 수를 셀 두 번째 상자를 만들어요.

**변수 만들기**: 이름 `명중`, **모든 스프라이트에서 사용**

이제 **목표** 스프라이트에 만드세요. 시작할 때마다 명중을 0으로 되돌리고 과녁을 첫 자리에 놓아요.""",
"""Make a second box to count hits.

**Make a variable**: name `hits`, **For all sprites**

Now build this on the **목표** (target) sprite. Each new game resets hits to 0 and puts the target in its first spot."""),
    blocks(B["target_start"]),
    text("""**확인**: 무대에서 과녁을 마우스로 아무 데나 옮긴 뒤 깃발을 누르세요. 첫 자리로 돌아오나요?""",
"""**Check**: Drag the target anywhere on the stage, then click the green flag. Does it go back to its first spot?"""),
], "checks": [
    st("variableExists", kind="variable", name=HITS),
    st("hasBlock", opcode="data_setvariableto", sprite="목표"),
    st("hasBlock", opcode="motion_gotoxy", sprite="목표"),
    dyn(FLAG, [var_is(HITS, 0), spr("목표", "visible", "eq", True), spr("목표", "x", "eq", -36, tol=1), spr("목표", "y", "eq", 64, tol=1)], 3000),
]})

S({"key": "s19-hit", "title": L("명중했는지 알아내기", "Detect a hit"), "content": [
    text("""**포탄** 스프라이트로 가요. 포탄이 날아가는 **도중에** 과녁에 닿았는지 확인해야 해요.

- 질문: "닿았는가?" 블록은 어느 묶음에? (**감지**)
- 질문: 확인 블록은 반복 블록 **안**? **밖**? 왜?

닿았다면 할 일 세 가지: **명중 1 올리기 → 숨기기 → 이 스크립트 멈추기**(새 블록!)""",
"""Go to the **포탄** (cannonball) sprite. It must check for the target **while** flying.

- Question: Which category has the "touching?" block? (**Sensing**)
- Question: Does the check go **inside** or **outside** the repeat? Why?

If it touches: **add 1 to hits → hide → stop this script** (new block!)"""),
    blocks(B["hit_hint"]),
    text("""**확인**: 첫 과녁을 맞히면 포탄이 바로 사라지고 `명중`이 1이 되나요? 빗나가면 그대로 0인가요?""",
"""**Check**: When you hit the first target, does the cannonball vanish and `hits` become 1? If you miss, does it stay 0?"""),
], "checks": [
    st("inside", parent="control_repeat", child="control_if"),
    st("inside", parent="control_if", child="data_changevariableby"),
    dyn(FLAG + press("ArrowUp", 9) + FIRE + [wait(2000)], [var_is(HITS, 1), spr("포탄", "visible", "eq", False)], 6000),
    dyn(FLAG + FIRE + [wait(2500)], [var_is(HITS, 0)], 5000),
]})

S({"key": "s20-next-spot", "title": L("과녁아 다음 자리로!", "Target, move on!"), "content": [
    text("""과녁은 `명중` 상자를 지켜보다가 숫자가 바뀌면 움직여요. 새 블록 `~까지 기다리기`(**제어**)를 쓰면 돼요.

**목표**의 깃발 스크립트 **아래에 이어서** 붙이세요.""",
"""The target watches the `hits` box and moves when it changes. Use the new block `wait until` (**Control**).

Attach these **below** the target's green-flag script."""),
    blocks(B["wait_until"]),
    text("""**확인**: 첫 과녁을 맞히면 과녁이 오른쪽 위 두 번째 자리로 옮겨 가나요?

**생각해 보기**: 포탄과 과녁은 서로 말을 걸지 않았는데 어떻게 알았을까요?""",
"""**Check**: When you hit the first target, does it move to the second spot?

**Think**: The cannonball and target never talked to each other. How did the target know?"""),
], "checks": [
    st("hasBlock", opcode="control_wait_until", sprite="목표"),
    dyn(FLAG + press("ArrowUp", 9) + FIRE + [wait(1800)], [spr("목표", "x", "eq", 90, tol=2), spr("목표", "y", "eq", 80, tol=2)], 5000),
]})

S({"key": "s21-boom", "title": L("미션: 펑! 터지는 과녁", "Mission: exploding target"), "content": [
    text("""**목표** 스프라이트에는 `펑` 모양이 있어요. 맞히면 과녁이 잠깐 터졌다가 다음 자리로 가게 해요.

**할 일**: `~까지 기다리기`와 `이동하기` **사이에** 아래 세 블록을 끼워 넣으세요.""",
"""The **목표** (target) sprite has a `펑` (boom) costume. Make it explode briefly before moving on.

**To do**: Put these three blocks **between** `wait until` and `go to`."""),
    blocks(B["boom"]),
    text("""**놓치기 쉬운 곳**: 게임 도중에 멈추면 과녁이 `펑` 모양으로 남을 수 있어요. 깃발 스크립트 맨 위에 `모양을 과녁으로 바꾸기`도 넣어 두세요.""",
"""**Easy to miss**: If you stop mid-game, the target can stay in the `펑` costume. Add `switch costume to 과녁` at the top of the green-flag script too."""),
], "checks": [
    st("hasBlock", opcode="looks_switchcostumeto", sprite="목표", minCount=2),
    dyn(FLAG + press("ArrowUp", 9) + FIRE + [wait(1800)], [spr("목표", "costume", "eq", "과녁"), spr("목표", "x", "eq", 90, tol=2)], 5000),
]})

S({"key": "s22-three-targets", "title": L("과녁 3곳과 승리", "Three targets and victory"), "content": [
    text("""**스스로 완성하기**: 과녁 자리는 모두 세 곳이에요.

| 순서 | 자리 | 언제 옮겨 갈까? |
| --- | --- | --- |
| 1번 | x: -36, y: 64 | 시작할 때 |
| 2번 | x: 90, y: 80 | 명중이 1이 되면 |
| 3번 | x: 207, y: 31 | 명중이 2가 되면 |

명중이 **3**이 되면 펑! 하고 승리를 외친 뒤 사라지게 하세요.""",
"""**Finish it yourself**: The target has three spots.

| Order | Spot | When does it move? |
| --- | --- | --- |
| 1 | x: -36, y: 64 | At the start |
| 2 | x: 90, y: 80 | When hits becomes 1 |
| 3 | x: 207, y: 31 | When hits becomes 2 |

When hits reaches **3**, go boom, cheer, and disappear."""),
    blocks(B["win"]),
    text("""**확인**: 처음부터 끝까지 해 보세요. 과녁 3개를 모두 맞히면 통과!""",
"""**Check**: Play from start to finish. Hit all three to pass!"""),
    image("media/targets.png", "과녁 세 곳의 위치", "The three target spots"),
], "checks": [
    st("hasBlock", opcode="control_wait_until", sprite="목표", minCount=3),
    dyn(FLAG + press("ArrowUp", 9) + FIRE + [wait(1800)] + press("ArrowDown", 3) + FIRE + [wait(2200)]
        + press("ArrowDown", 3) + FIRE + [wait(2600)], [var_is(HITS, 3)], 15000),
]})

S(quiz("q5-hit", L("확인 퀴즈: 명중", "Quiz: hits"), [
    q("q5-1", "code", L("3번 자리로 옮기기 전에 기다리는 조건이에요. ? 에 들어갈 숫자는?", "This is the wait before moving to spot 3. What number goes in the ? ?"),
      O(("1", "1"), ("2", "2"), ("3", "3"), ("0", "0")), 1,
      L("두 번째 과녁을 맞혀서 명중이 2가 되면 3번 자리로 가요.", "After the second hit, hits is 2, so it moves to spot 3."), blocks_pair=QB["wait_blank"]),
    q("q5-2", "choice", L("과녁은 포탄이 자기를 맞혔다는 것을 어떻게 알까요?", "How does the target know it was hit?"),
      O(("포탄이 과녁에게 말을 건다", "The cannonball talks to it"), ("모두가 보는 `명중` 상자의 숫자가 바뀌는 것을 본다", "It sees the shared `hits` box change"),
        ("선생님이 알려 준다", "The teacher tells it"), ("과녁이 포탄 모양을 본다", "It looks at the cannonball's costume")), 1,
      L("모든 스프라이트가 보는 변수 덕분에 서로 신호를 주고받을 수 있어요.", "A shared variable lets sprites signal each other.")),
    q("q5-3", "predict", L("만약 블록을 반복 **밖**으로 옮겼어요. 과녁을 정확히 겨눠 쏘면?", "The if block was moved **outside** the repeat. If you aim perfectly and fire?"),
      O(("평소처럼 명중이 1 오른다", "hits goes up by 1 as usual"), ("포탄이 과녁을 지나쳐 날아가고, 명중이 거의 오르지 않는다", "It flies past the target and hits rarely goes up"),
        ("포탄이 날아가지 않는다", "It doesn't fly"), ("명중이 40 오른다", "hits goes up by 40")), 1,
      L("반복이 다 끝난 뒤에 한 번만 확인하니까, 그때 포탄은 이미 과녁을 지나간 뒤예요.", "It only checks once after the loop, when the cannonball has already passed the target."),
      blocks_pair=QB["if_outside"]),
]))

S({"key": "s23-shots", "title": L("발사 수 세기", "Count your shots"), "content": [
    text("""진짜 포수는 포탄을 아껴요. 몇 발을 쐈는지 세어 봐요.

**변수 만들기**: 이름 `발사`, **모든 스프라이트에서 사용**

- 질문: 게임을 시작할 때 `발사`를 0으로 정하는 블록은 어느 스크립트에 넣을까요? (힌트: 대포의 깃발 스크립트)
- 질문: 1씩 올리는 블록은 어느 스크립트에 넣을까요? (힌트: 쏠 때마다)""",
"""Real gunners save cannonballs. Let's count how many you fire.

**Make a variable**: name `shots`, **For all sprites**

- Question: Which script should set `shots` to 0 at the start? (Hint: the cannon's green-flag script)
- Question: Which script should add 1? (Hint: every time you fire)"""),
    blocks(B["shots"]),
    text("""**확인**: 깃발을 누르고 스페이스를 두 번 누르면 `발사`가 2가 되나요?""",
"""**Check**: Green flag, then press space twice. Is `shots` 2?"""),
], "checks": [
    st("variableExists", kind="variable", name=SHOTS),
    dyn(FLAG + FIRE + [wait(300)] + FIRE + [wait(300)], [var_is(SHOTS, 2)], 4000),
]})

S({"key": "s24-gunner-test", "title": L("포수 시험: 어림해서 맞히기", "Gunner's test: estimate, then fire"), "content": [
    text("""진짜 포수 시험이에요. 규칙은 하나! **쏘기 전에 각도를 먼저 어림하기.**

1. 과녁을 보고 각도기 눈금으로 "몇 도쯤?" 어림
2. 대포가 말하는 숫자를 보며 그 각도에 맞추기
3. 쏘고, 빗나가면 어느 쪽으로 빗나갔는지 보고 고치기

**기록표**

| 과녁 | 내 어림 | 맞은 각도 | 쏜 횟수 |
| --- | --- | --- | --- |
| 1번 | | | |
| 2번 | | | |
| 3번 | | | |

**단계별 도전**
- 🥉 7발 안에 3개
- 🥈 5발 안에 3개
- 🥇 3발 만에 3개 (한 발도 안 빗나가기!)""",
"""The real gunner's test. One rule! **Estimate the angle before firing.**

1. Look at the target and guess the angle with the protractor
2. Use the number the cannon says to set that angle
3. Fire; if you miss, see which way and adjust

**Record sheet**

| Target | My estimate | Hit angle | Shots |
| --- | --- | --- | --- |
| 1 | | | |
| 2 | | | |
| 3 | | | |

**Challenge levels**
- 🥉 3 targets in 7 shots
- 🥈 3 targets in 5 shots
- 🥇 3 targets in 3 shots (no misses!)"""),
    text("""**생각해 보기**: 1번 과녁은 조금 틀려도 맞는데, 3번 과녁은 딱 맞아야만 맞아요. 5도 실험을 떠올리면 왜 그럴까요?""",
"""**Think**: Target 1 forgives small mistakes, but target 3 only counts if you're exact. Remember the 5-degree experiment: why?"""),
]})

S(quiz("q6-wrap", L("마무리 퀴즈", "Wrap-up quiz"), [
    q("q6-1", "choice", L("3번 과녁이 가장 맞히기 어려운 까닭은?", "Why is target 3 the hardest?"),
      O(("과녁이 가장 작아서", "It's the smallest"), ("가장 멀어서, 같은 각도 차이도 크게 빗나가서", "It's the farthest, so the same angle error misses by more"),
        ("색깔이 달라서", "It's a different color"), ("포탄이 느려져서", "The cannonball slows down")), 1,
      L("세 과녁의 크기는 같아요. 멀수록 작은 각도 차이가 크게 벌어져요.", "All targets are the same size. Distance makes small angle errors big.")),
    q("q6-2", "choice", L("오늘 만든 변수가 **아닌** 것은?", "Which is **not** a variable we made today?"),
      O(("각도", "angle"), ("명중", "hits"), ("발사", "shots"), ("방향", "direction")), 3,
      L("`방향`은 스크래치에 원래 있는 블록이에요. 우리가 만든 변수는 각도, 명중, 발사예요.", "`direction` is built into Scratch. We made angle, hits and shots.")),
    q("q6-3", "choice", L("타르탈리아에 따르면 대포를 몇 도로 쏴야 가장 멀리 날아갈까요?", "According to Tartaglia, which angle shoots the farthest?"),
      O(("30도", "30 degrees"), ("45도", "45 degrees"), ("60도", "60 degrees"), ("90도", "90 degrees")), 1,
      L("45도예요. 30도와 60도는 같은 곳에 떨어져요.", "45 degrees. 30 and 60 land in the same place.")),
]))

S({"key": "s25-missions", "title": L("확장 미션", "Bonus missions"), "content": [
    text("""필수 구현 끝! 남은 시간에 미션을 골라 도전하세요. 하나 끝낼 때마다 **선생님께 보여 주세요**.

## ★ 미션 A. 나만의 사격장
과녁 3곳을 내가 정한 자리로 바꾸고 짝에게 도전장! 짝은 몇 발 만에 맞힐까요?""",
"""Must-haves done! Pick a mission for the time left. **Show your teacher** each time you finish one.

## ★ Mission A. My own range
Move the three targets anywhere you like and challenge your partner. How many shots will they need?"""),
    text("""## ★★ 미션 B. 포탄은 5발뿐
변수 `포탄 수`를 만들어 시작할 때 5로 정하고, 쏠 때마다 1씩 줄이세요. 0이면 못 쏘게 해요. 스페이스 스크립트 **맨 처음**에 넣어요.""",
"""## ★★ Mission B. Only 5 cannonballs
Make `shots left`, set it to 5 at the start and subtract 1 per shot. At 0, no firing. Put this at the **very start** of the space script."""),
    blocks(B["ammo"]),
    text("""## ★★ 미션 C. 움직이는 과녁
과녁이 위아래로 오르내리게 해요. 움직이는 과녁은 언제 쏴야 맞을까요? **목표**에 깃발 스크립트를 하나 더 만들어요.""",
"""## ★★ Mission C. Moving target
Make the target bob up and down. When should you fire? Add one more green-flag script to the **목표** (target) sprite."""),
    blocks(B["moving"]),
    text("""## ★★★ 미션 D. 대포가 뒤로 넘어가지 않게
각도가 **0보다 작아지거나 105보다 커지지 않게** 막아요. 화살표 스크립트에서 각도를 바꾼 **다음**에 확인해요. 105 쪽은 스스로!""",
"""## ★★★ Mission D. Don't flip the cannon
Keep the angle from going **below 0 or above 105**. Check right **after** changing it in the arrow scripts. Do the 105 side yourself!"""),
    blocks(B["limit"]),
    text("""## ★★★ 미션 E. 바람이 분다 (휘는 포탄)
포탄이 날아가는 반복 **안**에 아래 블록을 넣어 조금씩 끌어내려 보세요. 포탄 길이 어떻게 휘나요? 이제 각도를 어떻게 어림해야 할까요? 타르탈리아의 45도와 비교해 보세요.""",
"""## ★★★ Mission E. Wind (curving shots)
Put this block **inside** the flying repeat to pull the cannonball down little by little. How does the path bend? How should you estimate now? Compare with Tartaglia's 45 degrees."""),
    blocks(B["wind"]),
]})

unit = {"subject": "scratch-lv1", "unitKey": "04-pirate-cannon", "order": 4,
        "title": L("해적선 대포", "Pirate Ship Cannon"), "starterProject": "starter.sb3", "steps": steps}

with open(os.path.join(OUT, "unit.json"), "w", encoding="utf-8") as f:
    json.dump(unit, f, ensure_ascii=False, indent=2); f.write("\n")

# 검증용: 모든 블록 문자열
allb = {}
for k, v in B.items(): allb["B_" + k] = {"ko": v[0].strip("\n"), "en": v[1].strip("\n")}
for k, v in QB.items(): allb["Q_" + k] = {"ko": v[0].strip("\n"), "en": v[1].strip("\n")}
json.dump(allb, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "blocks.json"), "w", encoding="utf-8"), ensure_ascii=False)

n_quiz = sum(1 for s in steps if s.get("type") == "quiz")
print("steps", len(steps), "(quiz", n_quiz, ") checks", sum(len(s.get("checks", [])) for s in steps),
      "questions", sum(len(s.get("questions", [])) for s in steps))
