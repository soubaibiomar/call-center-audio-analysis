import { createRequire } from "node:module";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";

const require = createRequire(
    new URL("../../apps/web/package.json", import.meta.url),
);
const { chromium } = require("playwright");
const AxeBuilder = require("@axe-core/playwright").default;
const root = fileURLToPath(new URL("../../", import.meta.url));
const output = fileURLToPath(
    new URL(
        "../../docs/implementation/evidence/step22-20261031/",
        import.meta.url,
    ),
);
const base =
    process.env.PROJECT28_WEB_URL ?? "http://127.0.0.1:8781/workspace/";
if (!/^http:\/\/127\.0\.0\.1:(8781|8783)\/workspace\/$/.test(base))
    throw new Error("Only the local synthetic preview is supported");
const fixture = JSON.parse(
    await readFile(root + ".local/step21-ui-context.json", "utf8"),
);
await mkdir(output, { recursive: true });
const browser = await chromium.launch({
    ...(process.platform === "win32"
        ? {
              executablePath:
                  "C:/Program Files/Google/Chrome/Application/chrome.exe",
          }
        : {}),
    headless: true,
});
const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    reducedMotion: "reduce",
});
const page = await context.newPage();
const result = {
    base,
    fixture:
        "synthetic signed identities; isolated test database; no model inference",
    assertions: [],
    screenshots: [],
    axe: [],
    routeErrors: [],
    expectedFailures: [],
};
page.on("pageerror", (error) => result.routeErrors.push(error.message));
page.on("console", (message) => {
    if (
        message.type() === "error" &&
        !message.text().includes("Failed to load resource")
    )
        result.routeErrors.push(message.text());
});
async function check(name, run) {
    await run();
    result.assertions.push(name);
}
async function capture(name, width = 1440, height = 1000) {
    await page.setViewportSize({ width, height });
    await page.screenshot({ path: output + name + ".png", fullPage: true });
    assert.equal(
        await page.evaluate(
            () => document.documentElement.scrollWidth > innerWidth,
        ),
        false,
        `Overflow: ${name}`,
    );
    result.screenshots.push({ name, width, height, horizontalOverflow: false });
}
async function axe(name) {
    const audit = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze();
    result.axe.push({
        name,
        violations: audit.violations.map((v) => ({
            id: v.id,
            impact: v.impact,
            count: v.nodes.length,
        })),
    });
    assert.equal(
        audit.violations.length,
        0,
        `Accessibility: ${name} ${JSON.stringify(audit.violations.map((v) => [v.id, v.nodes.map((n) => n.target)]))}`,
    );
}
try {
    await check("public health connects to the actual local API", async () => {
        await page.goto(base + "#/health");
        await page
            .getByText("Liveness last checked", { exact: false })
            .waitFor();
        assert.equal(
            await page.getByText("Connected", { exact: true }).count(),
            2,
        );
        assert.equal(await page.getByText("Ready", { exact: true }).count(), 2);
    });
    for (const width of [1440, 1280, 1024, 390]) {
        await capture(`health-${width}`, width, width === 390 ? 844 : 1000);
        await axe(`health-${width}`);
    }
    await check(
        "mobile navigation opens, follows a route, and closes",
        async () => {
            await page
                .getByRole("button", { name: "Workspace menu", exact: true })
                .click();
            assert.equal(
                await page
                    .getByRole("button", {
                        name: "Workspace menu",
                        exact: true,
                    })
                    .getAttribute("aria-expanded"),
                "true",
            );
            await page.keyboard.press("Escape");
            assert.equal(await page.evaluate(() => document.activeElement?.getAttribute("aria-label")), "Workspace menu");
            assert.equal(await page.getByRole("button", { name: "Workspace menu", exact: true }).getAttribute("aria-expanded"), "false");
            await page.keyboard.press("Enter");
            await page
                .getByRole("navigation")
                .getByRole("link", { name: "Calls", exact: true })
                .click();
            await page.getByLabel("Workspace access token").waitFor();
            assert.equal(
                await page
                    .getByRole("button", {
                        name: "Workspace menu",
                        exact: true,
                    })
                    .getAttribute("aria-expanded"),
                "false",
            );
        },
    );
    await check(
        "invalid identity stays outside the protected route",
        async () => {
            await page
                .getByLabel("Workspace access token")
                .fill("synthetic-invalid");
            await page
                .getByRole("button", { name: "Connect securely" })
                .click();
            await page
                .getByRole("alert")
                .filter({ hasText: "expired or is invalid" })
                .waitFor();
            assert.equal(
                await page.getByLabel("Workspace access token").inputValue(),
                "",
            );
            result.expectedFailures.push({
                endpoint: "/api/v1/me",
                status: 401,
            });
            await capture("access-error-390", 390, 844);
            await axe("access-error-mobile");
        },
    );
    await check(
        "signed synthetic account opens the requested protected route",
        async () => {
            await page
                .getByLabel("Workspace access token")
                .fill(fixture.tokens.reviewerA);
            await page
                .getByRole("button", { name: "Connect securely" })
                .click();
            await page
                .getByRole("heading", { name: "Calls", exact: true })
                .waitFor();
            assert.equal(
                await page.evaluate(
                    () => localStorage.length + sessionStorage.length,
                ),
                0,
            );
            assert.equal(
                await page.locator('input[type="password"]').count(),
                0,
            );
        },
    );
    await capture("protected-calls-1440", 1440, 1000);
    await axe("protected-calls");
    for (const [path, heading] of [
        ["overview", "Overview"],
        ["calls", "Calls"],
        ["live", "Live monitoring"],
        ["knowledge", "Knowledge base"],
        ["models", "Model lab"],
        ["settings", "Settings"],
    ]) {
        await check(`protected route ${path} renders`, async () => {
            await page.goto(base + "#/" + path);
            await page
                .getByRole("heading", { name: heading, exact: true })
                .waitFor();
        });
    }
    await check("workspace page search has a useful empty state", async () => {
        await page.getByLabel("Find a workspace page").fill("no-such-page");
        await page.getByText("No matching pages.").waitFor();
        await page.getByLabel("Find a workspace page").fill("");
    });
    await page.goto(base + "#/health");
    await page.getByText("Verified", { exact: true }).waitFor();
    await capture("signed-health-1440");
    await check(
        "keyboard skip link moves focus to the page content",
        async () => {
            await page.locator("body").click({ position: { x: 2, y: 2 } });
            await page.keyboard.press("Control+Home");
            await page.evaluate(() => document.activeElement?.blur());
            for (let count = 0; count < 30; count++) {
                await page.keyboard.press("Tab");
                if (await page.evaluate(() => document.activeElement?.textContent === "Skip to content")) break;
            }
            assert.equal(await page.evaluate(() => document.activeElement?.textContent), "Skip to content");
            await capture("keyboard-focus-1440");
            await page.keyboard.press("Enter");
            assert.equal(
                await page.evaluate(() => document.activeElement?.id),
                "main",
            );
        },
    );
    await check(
        "disconnect clears access and blocks a protected deep link",
        async () => {
            await page
                .getByRole("button", { name: "Disconnect workspace" })
                .click();
            await page.goto(base + "#/calls");
            await page.getByLabel("Workspace access token").waitFor();
        },
    );
    await check(
        "reload does not persist a previously connected identity",
        async () => {
            await page.reload();
            await page.getByLabel("Workspace access token").waitFor();
            assert.equal(
                await page.evaluate(
                    () => localStorage.length + sessionStorage.length,
                ),
                0,
            );
        },
    );
    await check("unknown routes provide recovery", async () => {
        await page.goto(base + "#/unknown");
        await page.getByRole("heading", { name: "Page not found" }).waitFor();
        await capture("not-found-1440");
    });
    await check("network failure has a visible retry path", async () => {
        await page.route("**/health", (route) => route.abort("failed"));
        await page.goto(base + "#/health");
        await page
            .getByText("Cannot reach the local API.", { exact: false })
            .waitFor();
        await capture("offline-1440");
        await axe("offline");
        await page.unroute("**/health");
        await page.getByRole("button", { name: "Check again" }).click();
        await page
            .getByText("Liveness last checked", { exact: false })
            .waitFor();
    });
    await check("existing review UI remains reachable", async () => {
        const response = await page.request.get(
            "http://127.0.0.1:8781/review-ui/",
        );
        assert.equal(response.status(), 200);
        assert.match(await response.text(), /Emotion review/);
    });
    assert.equal(result.routeErrors.length, 0);
    result.decision = "PASS";
} catch (error) {
    result.decision = "FAIL";
    result.failure = String(error);
    throw error;
} finally {
    await writeFile(
        output + "browser-qa.json",
        JSON.stringify(result, null, 2),
    );
    await browser.close();
}
console.log(
    JSON.stringify({
        decision: result.decision,
        assertions: result.assertions.length,
        screenshots: result.screenshots.length,
        axeAudits: result.axe.length,
        routeErrors: result.routeErrors.length,
    }),
);
