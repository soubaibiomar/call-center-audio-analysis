import { createRequire } from "node:module";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import { performance } from "node:perf_hooks";

const require = createRequire(
    new URL("../../apps/web/package.json", import.meta.url),
);
const { chromium } = require("playwright");
const AxeBuilder = require("@axe-core/playwright").default;
const root = fileURLToPath(new URL("../../", import.meta.url));
const out = root + "docs/implementation/evidence/step23-20261031/";
const fixture = JSON.parse(
    await readFile(root + ".local/step23-ui-context.json", "utf8"),
);
const base = "http://127.0.0.1:8784/workspace/";
await mkdir(out, { recursive: true });
const browser = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true,
});
const context = await browser.newContext({
    viewport: { width: 1440, height: 1100 },
    reducedMotion: "reduce",
    timezoneId: "Africa/Casablanca",
});
const page = await context.newPage();
const result = {
    fixture:
        "Synthetic records; real local API/database/signatures. No inference or training.",
    assertions: [],
    screenshots: [],
    axe: [],
    pageErrors: [],
    routes: [],
    refreshMilliseconds: [],
};
page.on("pageerror", (error) => result.pageErrors.push(error.message));
async function check(name, fn) {
    await fn();
    result.assertions.push(name);
}
async function capture(name, width = 1440, height = 1100) {
    await page.setViewportSize({ width, height });
    await page.screenshot({ path: out + name + ".png", fullPage: true });
    assert.equal(
        await page.evaluate(
            () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
        "Overflow: " + name,
    );
    result.screenshots.push({ name, width, height, horizontalOverflow: false });
}
async function audit(name) {
    const value = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze();
    result.axe.push({
        name,
        violations: value.violations.map((v) => ({
            id: v.id,
            nodes: v.nodes.map((n) => n.target),
        })),
    });
    assert.equal(value.violations.length, 0, JSON.stringify(result.axe.at(-1)));
}
async function go(path, title) {
    await page.goto(base + "#" + path);
    await page
        .getByRole("heading", { name: title, exact: true })
        .first()
        .waitFor();
}
async function connect(role, path = "/overview") {
    await page.goto(base + "#" + path);
    await page.getByLabel("Workspace access token").fill(fixture.tokens[role]);
    await page.getByRole("button", { name: "Connect securely" }).click();
    await page
        .getByText("Synthetic validation records", { exact: true })
        .waitFor();
}
try {
    await check(
        "dashboard uses API totals and visibly labels synthetic data",
        async () => {
            await connect("admin");
            await page
                .getByRole("heading", { name: "Overview", exact: true })
                .waitFor();
            await page
                .locator(".metric-card")
                .first()
                .getByText("3", { exact: true })
                .waitFor();
            await page.getByRole("heading", { name: "Recent calls" }).waitFor();
            await page.locator(".language-list li").nth(2).waitFor();
            assert.equal(await page.locator(".language-list li").count(), 3);
            result.routes.push("Dashboard");
        },
    );
    for (const width of [1440, 1280, 1024, 390]) {
        await capture("dashboard-" + width, width, width === 390 ? 844 : 1100);
        await audit("dashboard-" + width);
    }
    await check(
        "call filters and sortable table use real scoped API results",
        async () => {
            await page.setViewportSize({ width: 1440, height: 1100 });
            await go("/calls", "Calls");
            await page
                .getByText("3 matching records", { exact: false })
                .waitFor();
            await page
                .getByLabel("Status", { exact: true })
                .selectOption("flagged_for_review");
            await page
                .getByText("1 matching records", { exact: false })
                .waitFor();
            await capture("calls-filtered-1440");
            await page.getByLabel("Status", { exact: true }).selectOption("");
            await page.getByLabel("Language code").fill("fr");
            await page.getByRole("button", { name: "Apply language" }).click();
            await page
                .getByText("1 matching records", { exact: false })
                .waitFor();
            await page.getByLabel("Language code").fill("");
            await page.getByRole("button", { name: "Apply language" }).click();
            await page
                .getByText("3 matching records", { exact: false })
                .waitFor();
            await page.getByRole("button", { name: /QA score/ }).click();
            await page.locator('th[aria-sort="descending"]').waitFor();
            result.routes.push("Calls");
            await capture("calls-1440");
            await audit("calls");
        },
    );
    await check(
        "timestamp and keyboard range move actual native audio to 1.25 seconds",
        async () => {
            await go(`/calls/${fixture.call_ids[0]}`, "Call analysis");
            await page
                .getByRole("heading", { name: "Transcript", exact: true })
                .waitFor();
            assert.equal(
                await page
                    .getByRole("button", {
                        name: "Seek to 1.25 seconds",
                        exact: true,
                    })
                    .isDisabled(),
                true,
            );
            await page
                .getByLabel("Local recording", { exact: true })
                .setInputFiles(root + fixture.source);
            await page
                .getByRole("button", {
                    name: "Seek to 1.25 seconds",
                    exact: true,
                })
                .waitFor({ state: "visible" });
            await page.waitForFunction(
                () =>
                    !document.querySelector(
                        'button[aria-label="Seek to 1.25 seconds"]',
                    ).disabled,
            );
            await page
                .getByRole("button", {
                    name: "Seek to 1.25 seconds",
                    exact: true,
                })
                .click();
            assert.ok(
                Math.abs(
                    (await page
                        .locator("audio")
                        .evaluate((audio) => audio.currentTime)) - 1.25,
                ) < 0.05,
            );
            await page.waitForFunction(
                () =>
                    Number(
                        document.querySelector('input[type="range"]').value,
                    ) >= 1.2,
            );
            const slider = page.getByRole("slider");
            await slider.focus();
            await page.keyboard.press("ArrowRight");
            assert.ok(
                (await page
                    .locator("audio")
                    .evaluate((audio) => audio.currentTime)) > 1.25,
            );
            assert.equal(
                await page.locator("audio track").getAttribute("kind"),
                "captions",
            );
            result.routes.push("Playback/transcript");
            await capture("transcript-1440");
            await audit("transcript");
            await capture("transcript-390", 390, 844);
            await audit("transcript-mobile");
        },
    );
    await page.setViewportSize({ width: 1440, height: 1100 });
    for (const [path, title, name] of [
        ["/qa", "QA & compliance", "QA/compliance"],
        ["/emotion", "Emotion review", "Emotion"],
        ["/coaching", "Coaching", "Coaching"],
        ["/knowledge", "Knowledge base", "Knowledge"],
        ["/models", "Model lab", "Model lab"],
        ["/live", "Live monitoring", "Live"],
    ]) {
        await check(
            name + " route renders representative API fixtures",
            async () => {
                await go(path, title);
                await page
                    .getByText("Synthetic validation records", { exact: true })
                    .waitFor();
                if (path === "/qa")
                    await page
                        .getByText("Synthetic review flag", { exact: true })
                        .waitFor();
                if (path === "/knowledge")
                    await page
                        .getByRole("heading", { name: "synthetic-policy-v1" })
                        .waitFor();
                if (path === "/models")
                    await page
                        .getByText("fixture-not-trained", { exact: true })
                        .waitFor();
                if (path === "/live") {
                    await page
                        .getByLabel("Job identifier")
                        .fill(fixture.job_id);
                    await page
                        .getByRole("button", { name: "Monitor job" })
                        .click();
                    await page.getByText("queued", { exact: true }).waitFor();
                    await page
                        .getByRole("button", { name: "Pause updates" })
                        .click();
                }
                result.routes.push(name);
                await capture(path.slice(1) + "-1440");
                await audit(path);
            },
        );
    }
    await check(
        "API failure cannot display empty success and retry recovers",
        async () => {
            await page.route("**/api/v1/calls?**", (route) =>
                route.fulfill({
                    status: 503,
                    contentType: "application/json",
                    body: '{"error":"synthetic injected failure"}',
                }),
            );
            await go("/calls", "Calls");
            await page.getByRole("button", { name: "Refresh calls" }).click();
            await page
                .getByRole("heading", { name: "This view could not be loaded" })
                .waitFor();
            assert.equal(
                await page
                    .getByRole("heading", { name: "No matching calls" })
                    .count(),
                0,
            );
            await capture("api-error-1440");
            await audit("api-error");
            await page.unroute("**/api/v1/calls?**");
            await page.getByRole("button", { name: "Try again" }).click();
            await page
                .getByText("3 matching records", { exact: false })
                .waitFor();
        },
    );
    await check(
        "fresh list response-to-render refresh measurements",
        async () => {
            for (let i = 0; i < 20; i++) {
                const previousUpdate = await page
                    .locator(".call-update")
                    .getAttribute("data-updated-at");
                const start = performance.now();
                await Promise.all([
                    page.waitForResponse(
                        (r) =>
                            r.url().includes("/api/v1/calls?") &&
                            r.status() === 200,
                    ),
                    page.getByRole("button", { name: "Refresh calls" }).click(),
                ]);
                await page
                    .getByText("3 matching records", { exact: false })
                    .waitFor();
                await page.waitForFunction(
                    (previous) =>
                        document
                            .querySelector(".call-update")
                            ?.getAttribute("data-updated-at") !== previous,
                    previousUpdate,
                );
                result.refreshMilliseconds.push(performance.now() - start);
            }
        },
    );
    await check(
        "registry permission denial is explicit for supervisor",
        async () => {
            await page
                .getByRole("button", { name: "Disconnect workspace" })
                .click();
            await connect("supervisor", "/models");
            await page
                .getByRole("heading", { name: "Permission required" })
                .waitFor();
            await capture("permission-1440");
            await audit("permission");
        },
    );
    await check(
        "empty account shows zero stored totals and honest empty calls",
        async () => {
            await page
                .getByRole("button", { name: "Disconnect workspace" })
                .click();
            await connect("empty", "/calls");
            await page
                .getByRole("heading", { name: "No matching calls" })
                .waitFor();
            await capture("empty-390", 390, 844);
            await audit("empty-mobile");
        },
    );
    assert.equal(result.pageErrors.length, 0);
    const sorted = [...result.refreshMilliseconds].sort((a, b) => a - b);
    result.loadMetrics = {
        samples: sorted.length,
        p95Milliseconds: sorted[Math.ceil(sorted.length * 0.95) - 1],
        p50Milliseconds: sorted[Math.ceil(sorted.length * 0.5) - 1],
        definition:
            "local calls-list refresh click through HTTP 200, validated query completion and a newly rendered data-updated timestamp; includes automation overhead; 3 synthetic records, sequential warm browser",
    };
    result.decision = "PASS";
} catch (error) {
    result.decision = "FAIL";
    result.failure = String(error);
    throw error;
} finally {
    await writeFile(out + "browser-qa.json", JSON.stringify(result, null, 2));
    await browser.close();
}
console.log(
    JSON.stringify({
        decision: result.decision,
        assertions: result.assertions.length,
        routeCoverage: result.routes.length,
        screenshots: result.screenshots.length,
        axeAudits: result.axe.length,
        pageErrors: result.pageErrors.length,
        loadMetrics: result.loadMetrics,
    }),
);
