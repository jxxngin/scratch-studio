# -*- coding: utf-8 -*-
"""보물 지도 탐험 unit.json의 채점 규칙(checks)을 실제 스크래치 엔진(TurboWarp)에서 돌려 본다.

실행: python tools/01-treasure-map/verify/run_checks.py
필요: playwright (pip install playwright, python -m playwright install chromium), 인터넷(엔진을 CDN에서 받음)
먼저 build_tests.py로 tests/*.sb3를 만든다.

- 정적 검사(hasBlock, underHat)는 sb3의 project.json을 읽어 여기서 판정한다.
- 동적 검사는 harness.html이 엔진에 작품을 불러와 actions를 실제 시간대로 실행하고 expect를 확인한다.
- 입력 표 검사(record)는 사이트가 채점하므로 여기서는 건너뛴다.
- 정답(solution)과 꾸미기를 뺀 작품(core)는 EXPECT_FAIL에 적은 스텝만 떨어지고 나머지는 모두 통과해야 "맞음"이다.
- 틀린 작품(wrong-*)은 그 실수를 하는 스텝(EXPECT_FAIL)에서 떨어져야 "맞음"이다. 작품에는 마지막 스크립트가 다 들어 있어서
  다른 스텝도 함께 떨어질 수 있는데, 학생은 그 스텝들을 실수하기 전에 이미 통과했으므로 따지지 않는다.
  결과는 report.txt에도 남긴다.
"""
import asyncio, functools, http.server, json, os, sys, threading, zipfile
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
UNIT = os.path.join(ROOT, "project", "lv1", "01-treasure-map", "unit.json")
PORT = 8765

# 작품마다 떨어져야 하는 스텝. wrong-*은 그 실수를 하는 스텝
EXPECT_FAIL = {
    "solution": set(),
    "core": {"s11-hello", "s12-my-xy", "s18-found-say"},
    "wrong-no-start": {"s06-start"},
    "wrong-hello-first": {"s11-hello"},
    "wrong-step20": {"s09-arrows-x"},
    "wrong-left-plus": {"s09-arrows-x"},
    "wrong-up-minus": {"s10-arrows-y"},
    "wrong-no-wait": {"s15-wait-touch"},
    "wrong-swap34": {"s16-third-spot"},
    "wrong-no-finish": {"s20-time-say"},
    "wrong-no-fifth-wait": {"s20-time-say"},
    "wrong-arrow-goto": {"s09-arrows-x"},
    "wrong-script-in-explorer": {"s13-treasure-spot"},
}


def project_json(path):
    with zipfile.ZipFile(path) as z: return json.loads(z.read("project.json"))


def top_of(blocks, bid):
    while blocks[bid]["parent"]: bid = blocks[bid]["parent"]
    return blocks[bid]


def static_check(proj, c):
    sprites = [t for t in proj["targets"] if not t["isStage"]]
    if c["rule"] == "hasBlock":
        want = [t for t in sprites if c.get("sprite") in (None, "@any") or t["name"] == c["sprite"]]
        count = sum(1 for t in want for bid, b in t["blocks"].items()
                    if b["opcode"] == c["opcode"] and top_of(t["blocks"], bid)["opcode"].startswith("event_when"))
        return count >= c.get("minCount", 1), "개수 %d" % count
    if c["rule"] == "underHat":
        ok = any(b["opcode"] == c["opcode"] and top_of(t["blocks"], bid)["opcode"] == c["hat"]
                 for t in sprites for bid, b in t["blocks"].items())
        return ok, ""
    raise ValueError(c["rule"])


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map, **{".js": "text/javascript", ".sb3": "application/zip"})
    def log_message(self, *a): pass


async def run_variant(browser, name, steps, out):
    page = await browser.new_page()
    await page.goto("http://127.0.0.1:%d/tools/01-treasure-map/verify/harness.html" % PORT)
    await page.wait_for_function("window.ready === true")
    url = "/tools/01-treasure-map/verify/tests/%s.sb3" % name
    proj = project_json(os.path.join(HERE, "tests", name + ".sb3"))
    rows = []
    for s in steps:
        results = []
        for c in s.get("checks", []):
            if c["type"] == "record": results.append(("record", None, "사이트 채점")); continue
            if c["type"] == "static":
                ok, note = static_check(proj, c); results.append(("static", ok, c["rule"] + " " + c["opcode"] + " " + note)); continue
            if c["type"] == "dynamic":
                r = await page.evaluate("([u, c]) => runDynamic(u, c)", [url, c])
                fails = ["%s.%s %s %r 실제 %r" % (x["expect"].get("sprite", "var"), x["expect"].get("property", ""), x["expect"]["op"], x["expect"].get("value"), x["actual"])
                         for x in r["results"] if not x["pass"]]
                results.append(("dynamic", r["pass"], "; ".join(fails) or "%dms" % r["ms"])); continue
            raise ValueError(c["type"])
        graded = [r for r in results if r[1] is not None]
        passed = all(r[1] for r in graded) if graded else None
        rows.append((s["key"], passed, results))
    out[name] = rows
    await page.close()


async def main(names):
    unit = json.load(open(UNIT, encoding="utf-8"))
    steps = [s for s in unit["steps"] if s.get("checks")]
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Handler, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    out = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader"])
        # 한꺼번에 너무 많이 돌리면 실제 시간 기준의 동적 검사가 흔들리므로 셋씩 돌린다
        for i in range(0, len(names), 3):
            await asyncio.gather(*(run_variant(browser, n, steps, out) for n in names[i:i + 3]))
        await browser.close()
    srv.shutdown()

    all_ok = True
    lines = []
    for name in names:
        expect = EXPECT_FAIL.get(name, set())
        graded = [(k, p_, r) for k, p_, r in out[name] if p_ is not None]
        if name.startswith("wrong-"):
            failed = [k for k, p_, _ in graded if not p_]
            ok = expect <= set(failed)
            lines.append("\n=== %s: 실수하는 스텝 %s에서 %s (떨어진 스텝: %s)" % (name, ", ".join(sorted(expect)), "떨어짐, 맞음" if ok else "통과함, !! 틀림", ", ".join(failed) or "없음"))
        else:
            bad = [k for k, p_, _ in graded if p_ != (k not in expect)]
            ok = not bad
            lines.append("\n=== %s: 떨어져야 할 스텝 %s %s" % (name, ", ".join(sorted(expect)) or "없음", "맞음" if ok else "!! 틀림 " + ", ".join(bad)))
        all_ok = all_ok and ok
        for key, passed, results in graded:
            detail = " | ".join("%s:%s %s" % (k, "통과" if r else "실패", note) for k, r, note in results if r is not None)
            lines.append("  %-20s %-4s %s" % (key, "통과" if passed else "실패", detail))
    lines.append("\n결과: " + ("모두 예상대로" if all_ok else "예상과 다른 결과가 있음"))
    text = "\n".join(lines)
    print(text)
    open(os.path.join(HERE, "report.txt"), "w", encoding="utf-8").write(text + "\n")
    return all_ok


if __name__ == "__main__":
    names = sys.argv[1:] or list(EXPECT_FAIL)
    ok = asyncio.run(main(names))
    sys.exit(0 if ok else 1)
