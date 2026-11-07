import { createRequire } from "node:module";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
const require = createRequire(new URL("../../apps/web/package.json", import.meta.url));
const { chromium } = require("playwright");
const AxeBuilder = require("@axe-core/playwright").default;
const root = fileURLToPath(new URL("../../", import.meta.url));
const output = root + "docs/implementation/evidence/step24-20261031/";
const fixture = JSON.parse(await readFile(root + ".local/step24-ui-context.json", "utf8"));
const base = process.env.PROJECT28_REVIEW_WEB_URL ?? "http://127.0.0.1:8787/workspace/";
if (!/^http:\/\/127\.0\.0\.1:878[67]\/workspace\/$/.test(base)) throw new Error("Use only the isolated STEP24 preview");
const api = "http://127.0.0.1:8786/api/v1";
await mkdir(output, { recursive: true });
const result = { base, fixture: "synthetic silent WAV; signed identities; isolated PostgreSQL; no human labels", assertions: [], screenshots: [], axe: [], pageErrors: [], exportedSegments: 0 };
const browser = await chromium.launch({ ...(process.platform === "win32" ? { executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe" } : {}), headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: "reduce" });
const page = await context.newPage();
page.on("pageerror", e => result.pageErrors.push(e.message));
async function request(path, method = "GET", body, role = "admin") {
    const response = await fetch(api + path, { method, headers: { Authorization: `Bearer ${fixture.tokens[role]}`, "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body) });
    if (response.status === 204) return null;
    assert.ok(response.ok, `${method} ${path}: ${response.status}`);
    return response.json();
}
async function check(name, run) { await run(); result.assertions.push(name); }
async function capture(name, width = 1440) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
    await page.screenshot({ path: output + name + ".png", fullPage: true });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `Overflow ${name}`);
    result.screenshots.push({ name, width, horizontalOverflow: false });
    const audit = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    result.axe.push({ name, violations: audit.violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) })) });
    assert.equal(audit.violations.length, 0, JSON.stringify(result.axe.at(-1)));
}
async function connect(role, call = fixture.call_ids[0]) {
    await page.goto(base + "?validation=" + Date.now() + "#/reviews/" + call);
    await page.getByLabel("Workspace access token", { exact: true }).fill(fixture.tokens[role]);
    await page.getByRole("button", { name: "Connect securely", exact: true }).click();
    await page.getByRole("heading", { level: 1 }).filter({ hasNotText: "A secure start" }).waitFor();
}
async function recording() {
    await page.getByLabel("Local recording", { exact: true }).setInputFiles(root + fixture.source);
    await page.getByText("Checksum and duration match the registered source.", { exact: true }).waitFor();
    await page.locator("audio").evaluate(async audio => { await audio.play(); });
    await page.waitForTimeout(200);
    await page.locator("audio").evaluate(audio => audio.pause());
}
async function decision(reason) {
    await page.getByLabel("Decision rationale", { exact: true }).fill(reason);
    await page.getByLabel("I listened to the relevant audio and checked this saved revision.", { exact: true }).check();
}
try {
    // Erase only prior runs' corrections in this script's isolated synthetic tenant.
    for (const id of fixture.call_ids) {
        const res = await fetch(`${api}/calls/${id}/review`, { headers: { Authorization: `Bearer ${fixture.tokens.admin}` } });
        if (res.ok) { const item = await res.json(); await request(`/call-reviews/${item.id}?expected_revision=${item.revision}`, "DELETE"); }
    }
    await check("administrator registers a checksum and explicit training permission", async () => {
        await connect("admin");
        await page.getByRole("heading", { name: "Register review evidence" }).waitFor();
        await capture("registration-desktop");
        await page.getByLabel("Source recording", { exact: true }).setInputFiles(root + fixture.source);
        await page.getByLabel("Conversation reference", { exact: true }).fill("step24-synthetic-conversation");
        await page.getByLabel("Speaker references, separated by commas", { exact: true }).fill("synthetic-agent,synthetic-customer");
        await page.getByLabel("Source attestation", { exact: true }).fill("Synthetic silent source deliberately paired with fictional transcript to test the workflow only.");
        await page.getByLabel("Permission evidence", { exact: true }).fill("Synthetic test-only fixture; no real human labels");
        await page.getByLabel("Documented permission allows training", { exact: true }).check();
        await page.getByLabel("I verified this source belongs to this call and supplied stable grouping references.", { exact: true }).check();
        await page.getByRole("button", { name: "Register source", exact: true }).click();
        await page.getByRole("heading", { name: "Human transcript & QA review", exact: true }).waitFor();
    });
    const initial = await request(`/calls/${fixture.call_ids[0]}/review`);
    await check("supervisor corrects text, speaker, uncertainty and audio-backed QA score", async () => {
        await connect("supervisor"); await recording();
        await page.getByLabel("Corrected text 1", { exact: true }).fill("Synthetic corrected opening.");
        await page.getByLabel("Speaker 1", { exact: true }).selectOption("Customer");
        await page.getByLabel("Speaker 2", { exact: true }).selectOption("Agent");
        await page.getByLabel("Uncertain segment 2", { exact: true }).uncheck();
        await page.getByLabel("Override overall QA score", { exact: true }).check();
        await page.getByLabel("Corrected QA score", { exact: true }).fill("2.5");
        await page.getByLabel("QA rationale", { exact: true }).fill("Synthetic QA correction supported by the selected fixture interval.");
        await page.getByLabel("Evidence start (seconds)", { exact: true }).fill("0.25");
        await page.getByLabel("Evidence end (seconds)", { exact: true }).fill("1");
        await page.getByRole("button", { name: "Listen to QA evidence", exact: true }).click();
        assert.equal(await page.locator("audio").evaluate(a => a.currentTime), 0.25);
        for (const width of [1440, 1280, 1024, 390]) await capture(`draft-${width}`, width);
        await page.setViewportSize({ width: 1440, height: 1000 });
        await page.getByRole("button", { name: "Save corrections", exact: true }).click();
        await page.getByText("Review draft. Revision 2 saved.", { exact: true }).waitFor();
        await decision("Synthetic submission after playback and correction verification.");
        await page.getByRole("button", { name: "Submit for approval", exact: true }).click();
        await page.getByText("Review submitted. Revision 3 saved.", { exact: true }).waitFor();
        assert.equal(await page.getByRole("button", { name: "Approve review", exact: true }).isDisabled(), true);
        await capture("submitted-independent-approval-required");
    });
    await check("independent administrator approves; source preserved; export contains two synthetic segments", async () => {
        await connect("admin"); await recording();
        await decision("Independent synthetic approval after checking the saved correction.");
        await page.getByRole("button", { name: "Approve review", exact: true }).click();
        await page.getByText("Review approved. Revision 4 saved.", { exact: true }).waitFor();
        await page.getByRole("button", { name: "Load audit history", exact: true }).click();
        await page.getByText("Snapshot SHA-256", { exact: false }).first().waitFor();
        await page.getByRole("button", { name: "Preview approved export", exact: true }).click();
        await page.getByText("1 calls · 2 approved segments", { exact: true }).waitFor();
        const item = await request(`/calls/${fixture.call_ids[0]}/review`);
        assert.deepEqual(item.original, initial.original);
        assert.equal(item.original_sha256, initial.original_sha256);
        assert.equal(item.payload.segments[0].text, "Synthetic corrected opening.");
        const manifest = await request("/call-review-dataset");
        result.exportedSegments = manifest.approved_segments;
        await writeFile(output + "synthetic-export.json", JSON.stringify(manifest, null, 2));
        const downloaded = page.waitForEvent("download");
        await page.getByRole("button", { name: "Download annotation manifest", exact: true }).click();
        const stream = await (await downloaded).createReadStream();
        const parts = [];
        for await (const part of stream) parts.push(part);
        assert.deepEqual(JSON.parse(Buffer.concat(parts).toString()), manifest);
        await capture("approved-desktop"); await capture("approved-mobile", 390);
    });
    await check("permission revocation removes approved labels from current export", async () => {
        await page.setViewportSize({ width: 1440, height: 1000 });
        await page.getByLabel("Training permission", { exact: true }).uncheck();
        await page.getByLabel("Updated permission evidence", { exact: true }).fill("Synthetic test permission revoked");
        await page.getByRole("button", { name: "Save permission", exact: true }).click();
        await page.getByText("Review approved. Revision 5 saved.", { exact: true }).waitFor();
        await page.getByRole("button", { name: "Preview approved export", exact: true }).click();
        await page.getByText("0 calls · 0 approved segments", { exact: true }).waitFor();
        await capture("permission-revoked");
    });
    await check("mismatched audio disables decisions", async () => {
        await page.getByLabel("Local recording", { exact: true }).setInputFiles({ name: "wrong.wav", mimeType: "audio/wav", buffer: Buffer.from(await readFile(root + fixture.source)).subarray(0, 2000) });
        assert.equal(await page.getByRole("button", { name: "Approve review", exact: true }).isDisabled(), true);
        assert.equal(await page.getByLabel("I listened to the relevant audio and checked this saved revision.", { exact: true }).isDisabled(), true);
        await page.getByText("Select the registered recording to enable review decisions.", { exact: true }).waitFor();
        await capture("mismatched-recording");
    });
    await check("concurrent edit receives conflict and explicit refresh permits reapplication", async () => {
        const current = await request(`/calls/${fixture.call_ids[0]}/review`);
        await request(`/call-reviews/${current.id}`, "PATCH", { ...current.payload, expected_revision: current.revision }, "supervisor");
        await page.getByLabel("Corrected text 1", { exact: true }).fill("Unsaved conflicting synthetic change");
        await page.getByRole("button", { name: "Save corrections", exact: true }).click();
        await page.getByText("This review changed. Refresh it and reapply your corrections.", { exact: true }).waitFor();
        await capture("concurrent-edit-conflict");
        await page.getByRole("button", { name: "Refresh review (discard unsaved)", exact: true }).click();
        await page.getByText("Latest revision loaded. Reapply any unsaved corrections.", { exact: true }).waitFor();
        assert.equal(await page.getByLabel("Corrected text 1", { exact: true }).inputValue(), "Synthetic corrected opening.");
    });
    await check("agent is denied a correction screen", async () => {
        await connect("agent"); await page.getByRole("heading", { name: "Permission required", exact: true }).waitFor(); await capture("agent-permission-denied");
    });
    await check("independent reviewer can reject a resubmitted correction", async () => {
        await connect("supervisor"); await recording();
        await decision("Synthetic resubmission for rejection workflow verification.");
        await page.getByRole("button", { name: "Submit for approval", exact: true }).click();
        await page.getByText("Review submitted.", { exact: false }).waitFor();
        await connect("admin"); await recording();
        await decision("Independent reviewer rejects this synthetic correction for rework.");
        await page.getByRole("button", { name: "Reject review", exact: true }).click();
        await page.getByText("Review rejected.", { exact: false }).waitFor();
        await capture("rejected-review");
    });
    await check("administrator can erase annotation without changing original call", async () => {
        await page.getByText("Erase annotation and its audit snapshots", { exact: true }).click();
        await page.getByRole("button", { name: "Erase this annotation", exact: true }).click();
        await page.getByRole("heading", { name: "Register review evidence", exact: true }).waitFor();
        const report = await request(`/calls/${fixture.call_ids[0]}/report`);
        assert.deepEqual(report.transcription, initial.original.transcription);
        await capture("erased-annotation-source-preserved");
    });
    assert.deepEqual(result.pageErrors, []);
} catch (error) {
    await page.screenshot({ path: output + "failed-attempt.png", fullPage: true });
    await writeFile(output + "failed-labels.json", JSON.stringify({ labels: await page.locator("label").allTextContents(), text: await page.locator("main").innerText() }, null, 2));
    throw error;
} finally {
    await writeFile(output + "browser-results.json", JSON.stringify(result, null, 2));
    await browser.close();
}
console.log(`STEP24: ${result.assertions.length} browser scenarios; ${result.screenshots.length} screenshots; ${result.axe.length} accessibility scans; ${result.exportedSegments} synthetic approved segments before revocation.`);
