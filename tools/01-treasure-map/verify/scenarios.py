# -*- coding: utf-8 -*-
"""채점 규칙 밖에서 교안과 강사용 안내서가 말하는 동작을 실제 엔진에서 확인한다.

실행: python tools/01-treasure-map/verify/scenarios.py   (먼저 build_tests.py)
- 깃발을 다시 눌렀을 때의 경쟁(탐험가가 첫 자리 가까이에 있을 때)
- 걸린 시간을 말하는 값
- 심화 도전 로봇(2초, 1초 미끄러지기)
- 탐색 표의 정답: s08(이동하기와 바꾸기), s14(순서 바꾸기)
- 퀴즈 q2-1, q2-2를 문항의 코드 그대로
- 게임 도중 다시 시작, 확장 미션 E(보이지 않는 보물)
- 강사용 안내서 6장의 오개념 작품이 실제로 어떻게 움직이는지
"""
import asyncio, copy, functools, http.server, json, os, threading, zipfile
from playwright.async_api import async_playwright
from build_tests import Script, gotoxy, say_secs, wait_touch, OUT, STARTER, LEGS_KEYS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PORT = 8766
SCEN = os.path.join(OUT, "scenario")
os.makedirs(SCEN, exist_ok=True)


def press(key, n):
    out = []
    for _ in range(n): out += [{"do": "keyPress", "key": key, "durationMs": 50}, {"do": "wait", "ms": 70}]
    return out


LEGS = [sum((press(k, n) for k, n in leg), []) for leg in LEGS_KEYS]


def one_script(body, sprite="탐험가"):
    """스프라이트 하나에 깃발 스크립트 하나만 넣은 작품 (탐색 표, 퀴즈 확인용)."""
    s = Script()
    s.stack("event_whenflagclicked", body)
    with zipfile.ZipFile(STARTER) as z:
        proj = json.loads(z.read("project.json"))
        assets = {n: z.read(n) for n in z.namelist() if n != "project.json"}
    for t in proj["targets"]:
        if t["name"] == sprite: t["blocks"] = s.blocks
    return proj, assets


def write(name, proj_assets):
    proj, assets = proj_assets
    with zipfile.ZipFile(os.path.join(SCEN, name + ".sb3"), "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("project.json", json.dumps(proj, ensure_ascii=False))
        for n, d in assets.items(): z.writestr(n, d)
    return "/tools/01-treasure-map/verify/tests/scenario/%s.sb3" % name


def chx(dx): return ("motion_changexby", {"DX": ("num", dx)})
SAY = say_secs(("text", "출발!"), 1)

EXPLORE = {
    # s08: 줄마다 가운데에서 시작
    "s08-1": ([gotoxy(0, 0), gotoxy(60, 0), gotoxy(60, 0)], 300, "x", 60),
    "s08-2": ([gotoxy(0, 0), chx(60), chx(60)], 300, "x", 120),
    "s08-3": ([gotoxy(0, 0), gotoxy(-60, 0), chx(60)], 300, "x", 0),
    # s14: 말하는 동안(0.5초 때) 탐험가가 있는 자리
    "s14-1": ([gotoxy(0, 0), SAY, gotoxy(120, 60)], 500, "xy", (0, 0)),
    "s14-2": ([gotoxy(120, 60), SAY, gotoxy(0, 0)], 500, "xy", (120, 60)),
    "s14-3": ([gotoxy(0, 0), gotoxy(120, 60), SAY], 500, "xy", (120, 60)),
}


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map, **{".js": "text/javascript", ".sb3": "application/zip"})
    def log_message(self, *a): pass


async def scenario(page, url, actions):
    return await page.evaluate("([u, a]) => runScenario(u, a)", [url, actions])


def fmt(st, *names):
    return "  ".join("%s(%d, %d)%s" % (n, st[n]["x"], st[n]["y"], " '%s'" % st[n]["sayText"] if st[n]["sayText"] else "") for n in names)


async def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Handler, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    lines = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader"])
        page = await browser.new_page()
        await page.goto("http://127.0.0.1:%d/tools/01-treasure-map/verify/harness.html" % PORT)
        await page.wait_for_function("window.ready === true")
        sol = "/tools/01-treasure-map/verify/tests/solution.sb3"

        # 1. 탐험가가 첫 자리 (-60, -60)에 서 있는 채로 깃발을 다시 누르면
        log = await scenario(page, sol, [{"do": "greenFlag"}, {"do": "wait", "ms": 300}] + LEGS[0] +
                             [{"do": "wait", "ms": 1500, "log": "첫 보물을 찾은 뒤"}, {"do": "greenFlag"},
                              {"do": "wait", "ms": 1500, "log": "그 자리에서 깃발을 다시 누른 뒤 1.5초"}])
        lines.append("1. 첫 자리에서 다시 시작")
        for l in log: lines.append("   %s: %s" % (l["label"], fmt(l["state"], "탐험가", "보물")))

        # 2. 걸린 시간 값 (채점 경로대로 다 찾은 뒤)
        acts = [{"do": "greenFlag"}, {"do": "wait", "ms": 300}]
        for leg in LEGS: acts += leg + [{"do": "wait", "ms": 300}]
        acts += [{"do": "wait", "ms": 600, "log": "다 찾고 0.6초 뒤"}]
        log = await scenario(page, sol, acts)
        lines.append("2. 걸린 시간: 보물이 말한 값 '%s', 타이머 %.1f초" % (log[0]["state"]["보물"]["sayText"], log[0]["state"]["timer"]))

        # 3. 로봇: 깃발 → a 키 → 2초마다 기록
        for name, total in (("robot-2s", 16000), ("robot-1s", 10000)):
            acts = [{"do": "greenFlag"}, {"do": "wait", "ms": 300}, {"do": "keyPress", "key": "a", "durationMs": 50}]
            for t in range(0, total, 2000): acts.append({"do": "wait", "ms": 2000, "log": "%d초" % ((t + 2000) // 1000)})
            log = await scenario(page, "/tools/01-treasure-map/verify/tests/%s.sb3" % name, acts)
            lines.append("3. %s (a 키를 누른 뒤)" % name)
            for l in log: lines.append("   %4s: %s" % (l["label"], fmt(l["state"], "탐험가", "보물")))

        # 4. 탐색 표 정답
        lines.append("4. 탐색 표")
        for key, (body, at_ms, prop, want) in EXPLORE.items():
            url = write(key, one_script(body))
            log = await scenario(page, url, [{"do": "greenFlag"}, {"do": "wait", "ms": at_ms, "log": key}])
            st = log[0]["state"]["탐험가"]
            got = st["x"] if prop == "x" else (st["x"], st["y"])
            lines.append("   %s: 실제 %s, 교안 정답 %s %s" % (key, got, want, "맞음" if got == want else "!! 다름"))

        # 5. 퀴즈 q2-1, q2-2: 깃발만 누르고 1.5초 뒤 보물 자리
        lines.append("5. 퀴즈")
        q21 = [gotoxy(-60, -60), wait_touch("탐험가"), gotoxy(-120, 60)]
        q22 = [gotoxy(-120, 60), gotoxy(-60, -60), wait_touch("탐험가")]
        for key, body, want in (("q2-1", q21, (-60, -60)), ("q2-2", q22, (-60, -60))):
            url = write(key, one_script(body, "보물"))
            log = await scenario(page, url, [{"do": "greenFlag"}, {"do": "wait", "ms": 1500, "log": key}])
            st = log[0]["state"]["보물"]
            got = (st["x"], st["y"])
            lines.append("   %s: 보물 %s, 퀴즈 정답 %s %s" % (key, got, want, "맞음" if got == want else "!! 다름"))

        # 6. 게임 도중 다시 시작: "찾았다!"를 말하는 도중, 두 번째 보물을 향해 가는 도중
        lines.append("6. 게임 도중 다시 시작")
        start = [{"do": "greenFlag"}, {"do": "wait", "ms": 300}]
        for label, acts in (("찾았다!를 말하는 도중", start + LEGS[0] + [{"do": "wait", "ms": 100, "log": "깃발 직전"}]),
                            ("두 번째 보물로 가는 도중", start + LEGS[0] + [{"do": "wait", "ms": 1200}] + LEGS[1][:12] + [{"do": "wait", "ms": 100, "log": "깃발 직전"}])):
            acts = acts + [{"do": "greenFlag"}, {"do": "wait", "ms": 600, "log": "깃발 0.6초 뒤"}]
            log = await scenario(page, sol, acts)
            lines.append("   %s" % label)
            for l in log: lines.append("     %s: %s 타이머 %.2f" % (l["label"], fmt(l["state"], "탐험가", "보물"), l["state"]["timer"]))

        # 7. 확장 미션 E: 보물이 안 보여도 채점 경로대로 가면 다 찾는가
        acts = [{"do": "greenFlag"}, {"do": "wait", "ms": 300}]
        for leg in LEGS: acts += leg + [{"do": "wait", "ms": 300}]
        acts += [{"do": "wait", "ms": 600, "log": "다 찾고 0.6초 뒤"}]
        log = await scenario(page, "/tools/01-treasure-map/verify/tests/mission-e.sb3", acts)
        lines.append("7. 미션 E: %s" % fmt(log[0]["state"], "탐험가", "보물"))

        # 8. 오개념 작품이 실제로 하는 일
        lines.append("8. 오개념 작품")
        cases = [
            ("wrong-no-fifth-wait", "네 번째까지 찾은 뒤", start + sum(LEGS[:4], []) + [{"do": "wait", "ms": 1500, "log": "네 번째를 찾고 1.5초"}]),
            ("wrong-arrow-goto", "깃발 → 오른쪽 3번", start + [{"do": "wait", "ms": 2000}] + LEGS[0][:6] + [{"do": "wait", "ms": 300, "log": "오른쪽 3번 뒤"}]),
            ("wrong-script-in-explorer", "깃발만", [{"do": "greenFlag"}, {"do": "wait", "ms": 1500, "log": "깃발 1.5초 뒤"}]),
            ("wrong-script-in-explorer", "깃발 → 방향키로 배→1번 경로", start + LEGS[0] + [{"do": "wait", "ms": 500, "log": "1번 경로 뒤"}]),
        ]
        for name, label, acts in cases:
            log = await scenario(page, "/tools/01-treasure-map/verify/tests/%s.sb3" % name, acts)
            for l in log: lines.append("   %s (%s) %s: %s" % (name, label, l["label"], fmt(l["state"], "탐험가", "보물")))

        # 9. 안내서 6장의 나머지 설명
        lines.append("9. 안내서 6장의 나머지 설명")
        out_of_order = start + press("ArrowRight", 24) + press("ArrowUp", 24) + [{"do": "wait", "ms": 1500, "log": "세 번째 자리로 먼저 간 뒤"}]
        log = await scenario(page, sol, out_of_order)
        lines.append("   s17 도전 (순서를 건너뛰어 세 번째 자리로): %s" % fmt(log[0]["state"], "탐험가", "보물"))
        acts = [{"do": "greenFlag"}, {"do": "wait", "ms": 300}, {"do": "keyPress", "key": "a", "durationMs": 50}]
        for t in range(0, 14000, 2000): acts.append({"do": "wait", "ms": 2000, "log": "%d초" % ((t + 2000) // 1000)})
        log = await scenario(page, "/tools/01-treasure-map/verify/tests/robot-swap34.sb3", acts)
        lines.append("   s23 로봇 3·4번을 바꿔 쌓음 (a 키를 누른 뒤)")
        for l in log: lines.append("     %4s: %s" % (l["label"], fmt(l["state"], "탐험가", "보물")))
        acts = start + [{"do": "wait", "ms": 2200}] + LEGS[0][:12] + [{"do": "wait", "ms": 200, "log": "오른쪽 6번 뒤"},
                {"do": "keyPress", "key": " ", "durationMs": 50}, {"do": "wait", "ms": 300, "log": "스페이스 0.3초 뒤"}]
        log = await scenario(page, "/tools/01-treasure-map/verify/tests/wrong-space-twice.sb3", acts)
        lines.append("   미션 C를 스페이스로 만듦")
        for l in log: lines.append("     %s: %s" % (l["label"], fmt(l["state"], "탐험가", "보물")))
        await browser.close()
    srv.shutdown()
    text = "\n".join(lines)
    print(text)
    open(os.path.join(HERE, "scenarios.txt"), "w", encoding="utf-8").write(text + "\n")


asyncio.run(main())
