#!/usr/bin/env bun
// @SID: hf_gate_playwright — Bun.WebView HF form-gate acceptor (Tier 3 browser automation)
//
// Uses Bun.WebView (built-in since v1.3.12) — no playwright npm dep needed.
// Chrome backend: DevTools Protocol, auto-detects installed Chrome/Chromium.
// All input is dispatched as OS-level events (isTrusted: true — indistinguishable from real user).
//
// Invoked by scripts/embed_gate_accept.py when a model is form-gated and
// --allow-playwright is passed.
//
// Usage:
//   bun run scripts/hf_gate_playwright.ts --model-id google/gemma-2b --token $HF_TOKEN
//
// Output: JSON to stdout
//   { "model_id": str, "pass": bool, "status": str, "method": "bun_webview", "detail": str }
//
// Exit: 0 = accepted/already-open, 1 = failed

// --- Arg parsing ---
const args = process.argv.slice(2);
function getArg(flag: string): string | undefined {
  const i = args.indexOf(flag);
  return i !== -1 ? args[i + 1] : undefined;
}

const modelId = getArg("--model-id");
const token = getArg("--token") || process.env.HF_TOKEN || process.env.HUGGINGFACE_HUB_TOKEN;

function emit(obj: Record<string, unknown>, exitCode = 0): never {
  console.log(JSON.stringify(obj, null, 2));
  process.exit(exitCode);
}

if (!modelId) {
  emit(
    { pass: false, status: "failed", method: "bun_webview", detail: "--model-id is required" },
    1
  );
}

const modelUrl = `https://huggingface.co/${modelId}`;

// Injected into the page — finds and clicks the first visible agree button.
// Returns the label text of the button clicked, or null if none found.
const FIND_AND_CLICK_AGREE = `
(function() {
  var byTestId = document.querySelector("[data-testid='accept-gate-button']");
  if (byTestId && byTestId.offsetParent !== null) { byTestId.click(); return byTestId.innerText.trim(); }
  var byForm = document.querySelector("form[action*='agree'] button[type='submit']");
  if (byForm && byForm.offsetParent !== null) { byForm.click(); return byForm.innerText.trim(); }
  var labels = ["Agree and access repository", "Agree and access", "I agree", "Accept"];
  var btns = Array.from(document.querySelectorAll("button"));
  for (var i = 0; i < labels.length; i++) {
    var label = labels[i].toLowerCase();
    var match = btns.find(function(b) { return b.innerText.trim().toLowerCase().indexOf(label) !== -1; });
    if (match && match.offsetParent !== null) { match.click(); return match.innerText.trim(); }
  }
  return null;
})()
`;

try {
  // Bun.WebView is built into the Bun runtime (v1.3.12+). Chrome backend uses
  // DevTools Protocol and auto-detects an installed Chrome/Chromium browser.
  const WebView = (Bun as unknown as {
    WebView: new (opts: Record<string, unknown>) => {
      navigate(url: string): Promise<void>;
      evaluate(expr: string): Promise<unknown>;
      cdp(method: string, params?: Record<string, unknown>): Promise<unknown>;
      readonly url: string;
      [Symbol.asyncDispose](): Promise<void>;
    };
  }).WebView;

  await using view = new WebView({
    backend: "chrome",
    width: 1280,
    height: 800,
    console: false,
  });

  // Inject HF auth cookie via CDP Network domain before navigating
  if (token) {
    await view.cdp("Network.enable", {});
    await view.cdp("Network.setCookie", {
      name: "token",
      value: token,
      domain: ".huggingface.co",
      path: "/",
      secure: true,
      sameSite: "Lax",
      expires: Math.floor(Date.now() / 1000) + 3600,
    });
  }

  // Navigate to model page
  await view.navigate(modelUrl);

  // Find and click the agree button (via injected JS — CSS :has-text() is not standard)
  const clicked = (await view.evaluate(FIND_AND_CLICK_AGREE)) as string | null;

  if (!clicked) {
    // No agree button found — probe if model is already accessible
    await view.navigate(`${modelUrl}/tree/main`);
    const urlAfter = view.url;
    if (urlAfter.includes("/tree/main") || urlAfter.includes(`/${modelId}/`)) {
      emit({
        model_id: modelId,
        pass: true,
        status: "already_accepted",
        method: "bun_webview",
        detail: "No gate button visible — model already accessible (file tree reachable)",
      });
    } else {
      emit(
        {
          model_id: modelId,
          pass: false,
          status: "pending_form",
          method: "bun_webview",
          detail: `Gate button not found and file tree not reachable. Manual acceptance required: ${modelUrl}`,
        },
        1
      );
    }
  }

  // Button was clicked — give the page a moment to process, then verify
  await new Promise((r) => setTimeout(r, 2000));
  await view.navigate(`${modelUrl}/tree/main`);
  const urlAfter = view.url;

  if (urlAfter.includes("/tree/main")) {
    emit({
      model_id: modelId,
      pass: true,
      status: "accepted_now",
      method: "bun_webview",
      detail: `Gate accepted via Bun.WebView (clicked: "${clicked}") — file tree accessible`,
    });
  } else {
    emit(
      {
        model_id: modelId,
        pass: false,
        status: "failed",
        method: "bun_webview",
        detail: `Gate click sent but file tree not accessible. Current URL: ${urlAfter}`,
      },
      1
    );
  }
} catch (err: unknown) {
  const msg = err instanceof Error ? err.message : String(err);
  emit(
    {
      model_id: modelId,
      pass: false,
      status: "failed",
      method: "bun_webview",
      detail: `Bun.WebView error: ${msg}`,
    },
    1
  );
}
