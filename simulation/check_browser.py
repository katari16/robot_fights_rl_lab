"""Acceptance check against a running demo: python simulation/check_browser.py --url URL."""

import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", default="http://localhost:8765")
    p.add_argument(
        "--screenshot", type=Path, default=Path("simulation/output/mjswan.png")
    )
    args = p.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
            ],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(args.url, wait_until="networkidle")
        page.wait_for_function("window.arenaDemo !== undefined", timeout=90000)
        page.click("#play")
        page.evaluate("window.arenaDemo.seek(3)")
        first = page.locator("canvas").screenshot()
        page.evaluate("window.arenaDemo.seek(5)")
        page.wait_for_timeout(200)
        second = page.locator("canvas").screenshot()
        assert first != second, "Scrubbing did not change the rendered pose"
        start = page.evaluate("window.arenaDemo.time")
        page.wait_for_timeout(250)
        assert page.evaluate("window.arenaDemo.time") == start, (
            "Pause did not hold the frame"
        )
        page.click("#play")
        page.wait_for_timeout(400)
        page.click("#play")
        assert page.evaluate("window.arenaDemo.time") > start, (
            "Play did not advance the motion"
        )
        page.click("#reset")
        assert page.evaluate("window.arenaDemo.time") == 0
        page.select_option("#speed", "0.25")
        page.select_option("#mode", "nominal")
        page.wait_for_timeout(150)
        assert page.evaluate("window.arenaDemo.time") == 0
        page.select_option("#mode", "replay")
        page.select_option("#camera", "overhead")
        page.select_option("#camera", "arena")
        assert (
            page.evaluate("window.arenaDemo.engine.getState().interactionMode")
            == "view"
        )
        # The engine refuses malformed poses and physics/replay conflicts.
        checks = page.evaluate("""() => {
          const e=window.arenaDemo.engine, q=window.arenaDemo.motion.qpos[0];
          const rejected=(v)=>{try{e.setPose(v);return false;}catch{return true;}};
          const invalid=q.slice();invalid[3]=invalid[4]=invalid[5]=invalid[6]=0;
          const results=[rejected([0]),rejected(q.map(()=>NaN)),rejected(invalid)];
          e.play();results.push(rejected(q));e.pause();return results;
        }""")
        assert all(checks), f"Pose validation failed: {checks}"
        page.evaluate("window.arenaDemo.seek(4.8)")
        page.wait_for_timeout(250)
        args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(args.screenshot))
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
            "Mobile layout overflows"
        )
        assert page.locator("#play").is_visible()
        assert not errors, errors
        assert page.evaluate("window.arenaDemo.engine.getState().error") is None
        browser.close()
    print(
        "Browser checks passed: render, scrub, pause, play, reset, nominal, cameras, pose validation, mobile layout."
    )


if __name__ == "__main__":
    main()
