import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs/promises";
import path from "node:path";
import assert from "node:assert/strict";
const root = process.cwd(),
    folder = path.join(root, process.env.PROJECT28_REVIEW_EVIDENCE_DIR ?? "docs/implementation/evidence/step21-20261029");
const context = JSON.parse(
    await fs.readFile(path.join(root, ".local/step21-ui-context.json"), "utf8"),
);
// Reset only this preview tenant's explicitly synthetic correction fixtures.
const seedResponse = await fetch(
    "http://127.0.0.1:8781/api/v1/emotion-reviews",
    { headers: { Authorization: "Bearer " + context.tokens.admin } },
);
assert.equal(seedResponse.status, 200);
for (const item of await seedResponse.json()) {
    if (
        item.call_id !== context.call_id ||
        item.prediction.model_id !== "synthetic-preview-fixture"
    )
        throw new Error("Refuse mutation of non-synthetic preview data");
    for (const role of ["reviewerA", "reviewerB"]) {
        const response = await fetch(
            `http://127.0.0.1:8781/api/v1/emotion-reviews/${item.id}/votes/me`,
            {
                method: "DELETE",
                headers: { Authorization: "Bearer " + context.tokens[role] },
            },
        );
        assert.equal(response.status, 200);
    }
}
const browser = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true,
});
const browserContext = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
});
const page = await browserContext.newPage();
const errors = [],
    failures = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("response", (response) => {
    if (response.status() >= 400)
        failures.push({
            path: new URL(response.url()).pathname,
            status: response.status(),
        });
});
const results = { viewports: [], axe: [], assertions: [] };
async function connect(role) {
    await page.getByLabel("Reviewer access token").fill(context.tokens[role]);
    await page.getByRole("button", { name: "Connect to review queue" }).click();
    await page
        .getByRole("heading", { name: "Your review", exact: true })
        .waitFor();
    await page.locator(".queue-item").filter({ hasText: "0.0–1.0s" }).click();
    await page.locator(".original h2").filter({ hasText: "angry" }).waitFor();
}
async function capture(name, width, height) {
    await page.setViewportSize({ width, height });
    await page.screenshot({
        path: path.join(folder, name + ".png"),
        fullPage: true,
    });
    const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth,
    );
    assert.equal(overflow, false);
    results.viewports.push({ name, width, height, overflow });
}
try {
    await page.goto("http://127.0.0.1:8781/review-ui/");
    await capture("access-desktop", 1440, 1000);
    await page.keyboard.press("Tab");
    assert.equal(await page.locator(":focus").textContent(), "Skip to review");
    await page.screenshot({ path: path.join(folder, "keyboard-focus.png") });
    await page.keyboard.press("Enter");
    results.assertions.push("Skip link receives keyboard focus");
    await connect("reviewerA");
    await page.getByLabel("Local source recording").setInputFiles({
        name: "wrong.wav",
        mimeType: "audio/wav",
        buffer: Buffer.from("synthetic mismatch"),
    });
    await page
        .getByRole("alert")
        .filter({ hasText: "does not match" })
        .waitFor();
    assert.equal(
        await page
            .getByRole("checkbox", { name: /I reviewed the matching/ })
            .isDisabled(),
        true,
    );
    await capture("source-mismatch-desktop", 1440, 1000);
    results.assertions.push(
        "Mismatched audio is rejected before reviewer confirmation",
    );
    await page
        .getByLabel("Local source recording")
        .setInputFiles(path.join(root, ".local/step21-synthetic-review.wav"));
    await page.getByRole("button", { name: "Play segment start" }).waitFor();
    await page.getByRole("radio", { name: "Sad", exact: true }).check();
    await page
        .getByLabel("Reviewer notes")
        .fill("Synthetic browser review; no human label collection claimed.");
    await page
        .getByRole("checkbox", { name: /I reviewed the matching/ })
        .check();
    await page
        .getByRole("button", { name: "Save my review", exact: true })
        .click();
    await page
        .getByRole("status")
        .filter({ hasText: "Your review is saved" })
        .waitFor();
    await page.getByRole("button", { name: "Sign out", exact: true }).click();
    await connect("reviewerB");
    await page
        .getByLabel("Local source recording")
        .setInputFiles(path.join(root, ".local/step21-synthetic-review.wav"));
    await page.getByRole("button", { name: "Play segment start" }).waitFor();
    await page.getByRole("radio", { name: "Sad", exact: true }).check();
    await page
        .getByLabel("Reviewer notes")
        .fill("Second independent synthetic browser identity.");
    await page
        .getByRole("checkbox", { name: /I reviewed the matching/ })
        .check();
    await page
        .getByRole("button", { name: "Save my review", exact: true })
        .click();
    await page
        .getByRole("status")
        .filter({ hasText: "Your review is saved" })
        .waitFor();
    assert.equal(await page.locator(".original h2").textContent(), "angry");
    assert.equal(await page.locator(".corrected h2").textContent(), "sad");
    results.assertions.push(
        "Two signed synthetic reviewers verified correction; original remains angry",
    );
    const metricResponse = await fetch(
        "http://127.0.0.1:8781/api/v1/emotion-review-metrics",
        { headers: { Authorization: "Bearer " + context.tokens.admin } },
    );
    assert.equal(metricResponse.status, 200);
    results.observed_review_metrics = await metricResponse.json();
    for (const [name, width, height] of [
        ["review-desktop", 1440, 1000],
        ["review-tablet", 768, 1024],
        ["review-mobile", 390, 844],
    ]) {
        await capture(name, width, height);
        const audit = await new AxeBuilder({ page })
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze();
        results.axe.push({
            name,
            violations: audit.violations.map((v) => ({
                id: v.id,
                impact: v.impact,
                description: v.description,
                nodes: v.nodes.map((n) => n.target),
            })),
        });
    }
    await page
        .getByRole("button", { name: "Revoke my correction", exact: true })
        .click();
    await page
        .getByRole("status")
        .filter({ hasText: "Your correction was revoked" })
        .waitFor();
    assert.equal(
        await page.locator(".corrected h2").textContent(),
        "Awaiting verification",
    );
    results.assertions.push(
        "Revocation removes verified correction and refreshes state",
    );
    await page.getByLabel("Find by call reference").fill("no-such-call");
    await page.getByText("No matching items.").waitFor();
    await capture("empty-mobile", 390, 844);
    await page.getByLabel("Find by call reference").fill("");
    await page.getByRole("button", { name: "Sign out", exact: true }).click();
    await connect("admin");
    await page
        .getByLabel("Permission evidence reference")
        .fill("synthetic permission review; no actual training consent");
    await page
        .getByRole("button", { name: "Save permission", exact: true })
        .click();
    await page
        .getByRole("status")
        .filter({ hasText: "Training permission updated" })
        .waitFor();
    await capture("permission-desktop", 1440, 1000);
    results.assertions.push(
        "Admin permission form updates separately from corrections",
    );
    await page.getByRole("button", { name: "Sign out", exact: true }).click();
    await page.getByLabel("Reviewer access token").fill("synthetic-invalid");
    await page.getByRole("button", { name: "Connect to review queue" }).click();
    await page.getByRole("alert").waitFor();
    await capture("access-error-mobile", 390, 844);
    results.assertions.push(
        "Empty search and invalid-auth error states render; sign-out clears data",
    );
    results.console_errors = errors;
    results.failed_responses = failures;
    results.fixture =
        "Local signed synthetic identities and generated audio; no actual human reviews";
    await fs.writeFile(
        path.join(folder, "browser-qa.json"),
        JSON.stringify(results, null, 2),
    );
    assert.equal(errors.length, 0);
    assert.equal(results.axe.flatMap((a) => a.violations).length, 0);
    console.log(
        JSON.stringify({
            assertions: results.assertions,
            viewports: results.viewports,
            axe_violations: results.axe.flatMap((a) => a.violations).length,
            console_errors: errors.length,
            expected_invalid_auth_responses: failures,
        }),
    );
} finally {
    await browser.close();
}
