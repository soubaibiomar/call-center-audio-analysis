import { createRequire } from "node:module";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
const require = createRequire(new URL("../../apps/web/package.json", import.meta.url));
const { chromium } = require("playwright");
const AxeBuilder = require("@axe-core/playwright").default;
const root = fileURLToPath(new URL("../../", import.meta.url));
const out = root + "docs/implementation/evidence/step25-20261031/";
const fixture = JSON.parse(await readFile(root + ".local/step25-ui-context.json", "utf8"));
const base = "http://127.0.0.1:8788/workspace/";
const api = "http://127.0.0.1:8788/api/v1";
await mkdir(out, { recursive: true });
const result = { fixture: "Two isolated signed identities; actual Chrome WebRTC, Windows SAPI synthetic microphone input, cached local Whisper Tiny CPU inference", assertions: [], screenshots: [], axe: [], pageErrors: [], audioReceipts: [], transcriptEvents: [], mediaSamples: [], reconnects: [] };
const browser = await chromium.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true,
    args: ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", `--use-file-for-fake-audio-capture=${root}.local/step25-browser-speech.wav`, "--autoplay-policy=no-user-gesture-required"],
});
const contexts = await Promise.all([0,1].map(() => browser.newContext({ viewport: { width: 1440, height: 1100 }, reducedMotion: "reduce", timezoneId: "Africa/Casablanca", permissions: ["microphone"] })));
for (const context of contexts) await context.addInitScript(() => {
    const original = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    navigator.mediaDevices.getUserMedia = async constraints => {
        const stream = await original(constraints);
        window.__project28TestTracks ??= [];
        window.__project28TestTracks.push(...stream.getTracks());
        return stream;
    };
});
const a = await contexts[0].newPage(), b = await contexts[1].newPage();
for (const [index,page] of [a,b].entries()) {
    page.on("pageerror", e => result.pageErrors.push({ participant: index, message: e.message }));
    page.on("websocket", socket => socket.on("framereceived", frame => {
        try { const value = JSON.parse(String(frame.payload)); if (value.type === "transcript") result.transcriptEvents.push({ participant: index, event: value }); } catch {}
    }));
    page.on("response", async response => {
        if (response.url().endsWith("/audio")) {
            result.audioReceipts.push({ participant: index, status: response.status(), ...(response.ok() ? await response.json() : {}) });
        }
    });
}
async function request(path, method = "GET", body, role = "admin", extra = {}) {
    const response = await fetch(api + path, { method, headers: { Authorization: `Bearer ${fixture.tokens[role]}`, Origin: "http://127.0.0.1:8788", "Content-Type": "application/json", ...extra }, body: body === undefined ? undefined : JSON.stringify(body) });
    if (response.status === 204) return null;
    assert.ok(response.ok, `${method} ${path}: ${response.status}`); return response.json();
}
async function connect(page, role) {
    await page.goto(base + "#/live");
    await page.getByLabel("Workspace access token", { exact: true }).fill(fixture.tokens[role]);
    await page.getByRole("button", { name: "Connect securely", exact: true }).click();
    await page.getByRole("heading", { name: "A conversation with consent.", exact: true }).waitFor();
}
async function check(name, work) { await work(); result.assertions.push(name); }
async function capture(page, name, width = 1440) {
    await page.setViewportSize({ width, height: width === 390 ? 844 : 1100 });
    await page.screenshot({ path: out + name + ".png", fullPage: true });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, name + " overflows");
    result.screenshots.push({ name, width, horizontalOverflow: false });
    const audit = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    result.axe.push({ name, violations: audit.violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) })) });
    assert.equal(audit.violations.length, 0, JSON.stringify(result.axe.at(-1)));
}
async function waitConnected(page) {
    await page.getByTestId("call-connection").filter({ hasText: /^connected$/ }).waitFor({ timeout: 20000 });
    await page.getByTestId("dtls-state").filter({ hasText: /^connected$/ }).waitFor();
}
async function consentAndJoin(page) {
    await page.getByLabel("I consent to use my microphone for this two-party call.", { exact: true }).check();
    await page.getByRole("button", { name: "Join with microphone", exact: true }).click();
}
async function stats(page) {
    return { packetsReceived: Number(await page.getByTestId("received-packets").innerText()), packetsLost: Number(await page.getByTestId("lost-packets").innerText()), bytesReceived: Number(await page.getByTestId("received-bytes").innerText()), continuity: await page.getByTestId("continuity").innerText(), dtls: await page.getByTestId("dtls-state").innerText(), codec: await page.getByTestId("audio-codec").innerText() };
}
try {
    for (const room of (await request("/live/sessions")).items) await request(`/live/sessions/${room.id}`, "DELETE");
    const agent = await request("/me", "GET", undefined, "agent");
    await check("explicit microphone consent is required before either browser joins", async () => {
        await connect(a, "admin"); await connect(b, "agent");
        await a.getByLabel("Call participant", { exact: true }).selectOption(agent.user_id);
        await a.getByRole("button", { name: "Create call invitation", exact: true }).click();
        await a.getByText("Session ", { exact: false }).first().waitFor();
        assert.equal(await a.getByRole("button", { name: "Join with microphone", exact: true }).isDisabled(), true);
        for (const width of [1440,1280,1024,390]) await capture(a, `live-setup-${width}`, width);
        await a.setViewportSize({ width: 1440, height: 1100 });
        await b.getByRole("button", { name: "Refresh call invitations", exact: true }).click();
    });
    await check("two authenticated browsers exchange real encrypted WebRTC audio without capture consent", async () => {
        await consentAndJoin(a); await consentAndJoin(b);
        await waitConnected(a); await waitConnected(b);
        await a.waitForTimeout(4000);
        assert.equal(result.audioReceipts.length, 0);
        for (const page of [a,b]) { const value = await stats(page); assert.ok(value.packetsReceived > 0); assert.ok(value.bytesReceived > 0); assert.equal(value.dtls, "connected"); assert.equal(value.codec, "audio/opus"); result.mediaSamples.push(value); }
        await capture(a, "two-party-call-analysis-off");
    });
    await check("one participant's analysis permission is insufficient", async () => {
        await a.getByLabel("I allow my microphone audio to be analyzed locally for this call.", { exact: true }).check();
        await a.waitForTimeout(1800);
        assert.equal(result.audioReceipts.length, 0);
        await capture(a, "one-sided-analysis-consent");
    });
    await check("both permissions admit bounded PCM to real local ASR and emit transcript events", async () => {
        await b.getByLabel("I allow my microphone audio to be analyzed locally for this call.", { exact: true }).check();
        await a.getByTestId("analysis-state").filter({ hasText: "Analysis permitted by both participants" }).waitFor();
        await a.getByText("No authorized transcript event has arrived.", { exact: true }).waitFor({ state: "hidden", timeout: 30000 });
        await a.waitForFunction(() => new Set(Array.from(document.querySelectorAll(".transcript-panel li strong"), node => node.textContent)).size >= 2, undefined, { timeout: 30000 });
        assert.ok(result.audioReceipts.some(r => r.participant === 0 && r.status === 200));
        assert.ok(result.audioReceipts.some(r => r.participant === 1 && r.status === 200));
        assert.ok(result.transcriptEvents.some(e => e.event.segments.length > 0));
        await capture(a, "authorized-local-asr-desktop"); await capture(b, "authorized-local-asr-mobile", 390);
        await b.setViewportSize({ width: 1440, height: 1100 });
    });
    await check("revocation stops admission while peer conversation remains connected", async () => {
        await b.getByLabel("I allow my microphone audio to be analyzed locally for this call.", { exact: true }).uncheck();
        await a.getByTestId("analysis-state").filter({ hasText: "Analysis is off" }).waitFor();
        const room = (await request("/live/sessions")).items[0];
        const denied = await fetch(api + `/live/sessions/${room.id}/audio`, { method: "POST", body: new Uint8Array(32000), headers: { Authorization: `Bearer ${fixture.tokens.admin}`, Origin: "http://127.0.0.1:8788", "Content-Type": "application/octet-stream", "X-Audio-Sequence": "0", "X-Audio-Start-Sample": "0", "X-Consent-Revision": String(room.consent_revision) } });
        assert.equal(denied.status, 403);
        await waitConnected(a); await waitConnected(b);
        await capture(a, "analysis-revoked-call-continues");
    });
    await check("ending clears both browsers and server session", async () => {
        await a.getByRole("button", { name: "End call", exact: true }).click();
        await a.getByTestId("call-connection").filter({ hasText: /^ended$/ }).waitFor();
        await b.getByTestId("call-connection").filter({ hasText: /^ended$/ }).waitFor();
        assert.deepEqual((await request("/live/sessions")).items, []);
        for (const page of [a,b]) assert.equal(await page.locator('audio[aria-label="Remote participant audio"]').evaluate(audio => audio.srcObject === null && audio.paused), true);
        for (const page of [a,b]) assert.equal(await page.evaluate(() => window.__project28TestTracks.length > 0 && window.__project28TestTracks.every(track => track.readyState === "ended")), true);
        await capture(a, "call-ended-session-cleared");
    });
    await check("reconnect starts a new room with fresh consent", async () => {
        await a.getByText("No invitation is waiting for your account.", { exact: true }).waitFor();
        await a.getByRole("button", { name: "Reconnect with a new invitation", exact: true }).click();
        await b.getByRole("button", { name: "Refresh call invitations", exact: true }).click();
        assert.equal(await a.getByLabel("I consent to use my microphone for this two-party call.", { exact: true }).isChecked(), false);
        await consentAndJoin(a); await consentAndJoin(b);
        await waitConnected(a); await waitConnected(b);
        result.reconnects.push({ attempted: true, connected: true });
        await capture(a, "reconnected-fresh-consent");
        await a.goto(base + "#/health");
        await b.getByTestId("call-connection").filter({ hasText: /^ended$/ }).waitFor();
        assert.deepEqual((await request("/live/sessions")).items, []);
    });
    assert.deepEqual(result.pageErrors, []);
} catch (error) {
    await a.screenshot({ path: out + "failed-live-a.png", fullPage: true });
    await b.screenshot({ path: out + "failed-live-b.png", fullPage: true });
    await writeFile(out + "failed-live-text.json", JSON.stringify({ a: await a.locator("main").innerText(), b: await b.locator("main").innerText() }, null, 2));
    throw error;
} finally {
    await writeFile(out + "browser-results.json", JSON.stringify(result, null, 2));
    await browser.close();
}
console.log(`STEP25: ${result.assertions.length} scenarios; ${result.screenshots.length} screenshots; ${result.axe.length} accessibility scans; ${result.audioReceipts.length} PCM receipts; ${result.transcriptEvents.length} ASR event deliveries.`);
