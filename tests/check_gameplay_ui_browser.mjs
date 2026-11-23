import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const temporaryRoot = mkdtempSync(path.join(os.tmpdir(), "varalica-ui-browser-"));
let appProcess = null;
let browserProcess = null;
let cdpSocket = null;
let cdpSend = null;

function browserExecutable() {
  const candidates = [
    process.env.BROWSER_BIN,
    process.platform === "win32" ? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" : null,
    process.platform === "win32" ? "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" : null,
    "/usr/bin/google-chrome",
    "/usr/bin/microsoft-edge",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter(Boolean);
  const executable = candidates.find((candidate) => existsSync(candidate));
  if (!executable) {
    throw new Error("No Chrome/Edge browser found. Set BROWSER_BIN to a Chromium-compatible executable.");
  }
  return executable;
}

function pythonExecutable() {
  const candidates = [
    path.join(projectRoot, ".venv", "Scripts", "python.exe"),
    path.join(projectRoot, ".venv", "bin", "python"),
  ];
  return candidates.find((candidate) => existsSync(candidate)) || "python";
}

async function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(() => resolve(address.port));
    });
  });
}

async function waitFor(getValue, label, attempts = 100) {
  let lastError;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      const value = await getValue();
      if (value) return value;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`${label} did not become ready${lastError ? `: ${lastError.message}` : ""}`);
}

function connectCdp(url) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(url);
    socket.addEventListener("open", () => resolve(socket), { once: true });
    socket.addEventListener("error", () => reject(new Error("CDP WebSocket connection failed")), { once: true });
  });
}

function cdpClient(socket) {
  let nextId = 1;
  const pending = new Map();
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (!message.id || !pending.has(message.id)) return;
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) reject(new Error(message.error.message));
    else resolve(message.result);
  });
  return (method, params = {}) => new Promise((resolve, reject) => {
    const id = nextId;
    nextId += 1;
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

async function stopProcess(child) {
  if (!child || child.exitCode !== null) return;
  const exited = new Promise((resolve) => child.once("exit", resolve));
  child.kill();
  await Promise.race([
    exited,
    new Promise((resolve) => setTimeout(resolve, 2000)),
  ]);
}

async function main() {
  const appPort = await freePort();
  const debugPort = await freePort();
  const appUrl = `http://127.0.0.1:${appPort}/`;
  const databasePath = path.join(temporaryRoot, "browser.sqlite3");
  appProcess = spawn(
    pythonExecutable(),
    ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", String(appPort)],
    {
      cwd: projectRoot,
      env: { ...process.env, VARALICA_DB_PATH: databasePath },
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    },
  );
  await waitFor(async () => {
    const response = await fetch(`${appUrl}health`);
    return response.ok;
  }, "local Varalica server");

  browserProcess = spawn(
    browserExecutable(),
    [
      "--headless=new",
      `--remote-debugging-port=${debugPort}`,
      `--user-data-dir=${path.join(temporaryRoot, "browser-profile")}`,
      "--disable-background-networking",
      "--disable-default-apps",
      "--disable-gpu",
      "--no-first-run",
      "--no-default-browser-check",
      "--window-size=1280,900",
      appUrl,
    ],
    { stdio: ["ignore", "ignore", "pipe"], windowsHide: true },
  );

  const target = await waitFor(async () => {
    const response = await fetch(`http://127.0.0.1:${debugPort}/json/list`);
    const targets = await response.json();
    return targets.find((candidate) => candidate.type === "page" && candidate.url.startsWith(appUrl));
  }, "headless browser page");
  cdpSocket = await connectCdp(target.webSocketDebuggerUrl);
  const send = cdpClient(cdpSocket);
  cdpSend = send;
  await send("Runtime.enable");
  await send("Page.enable");

  const evaluate = async (expression) => {
    const result = await send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    if (result.exceptionDetails) {
      throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    }
    return result.result.value;
  };

  await waitFor(async () => evaluate(
    "document.readyState === 'complete' && typeof renderFinalVoting === 'function' && Boolean(window.VaralicaI18n)",
  ), "Varalica frontend");
  await evaluate(`
    window.VaralicaI18n.setUiLanguage("hr", { manual: true });
    document.querySelector("#languageGate")?.classList.add("hidden");
    document.querySelector(".app-shell")?.removeAttribute("inert");
    true
  `);

  const voteResult = await evaluate(`(async () => {
    localRoomCode = "12345";
    localPlayerId = "p1";
    localCredential = "browser-test-token";
    roomState = {
      room_code: "12345",
      round_number: 1,
      overtime_count: 0,
      state: "final_voting",
      viewer_id: "p1",
      host_id: "p1",
      viewer_is_spectator: false,
      required_vote_targets: 2,
      players: [
        { id: "p1", name: "One", avatar: "🥸", is_active_round_player: true, has_voted: false },
        { id: "p2", name: "Two", avatar: "😎", is_active_round_player: true, has_voted: false },
        { id: "p3", name: "Three", avatar: "🤖", is_active_round_player: true, has_voted: false },
        { id: "p4", name: "Four", avatar: "👻", is_active_round_player: true, has_voted: false }
      ]
    };
    clearPendingVoteTargets();
    renderFinalVoting();
    document.querySelector('[data-target-id="p2"]').click();
    const firstSelected = document.querySelector('[data-select-target-id="p2"]').classList.contains("selected");
    roomState = {
      ...roomState,
      players: roomState.players.map((player) => player.id === "p4" ? { ...player, has_voted: true } : player)
    };
    renderFinalVoting();
    const retainedAfterPeerRender = document.querySelector('[data-select-target-id="p2"]').classList.contains("selected");
    document.querySelector('[data-target-id="p3"]').click();
    const submitEnabled = !document.querySelector("#submitMultiVoteButton").disabled;
    const requested = [];
    window.fetch = async (url, options) => {
      requested.push({ url, options });
      return { ok: true, status: 200, json: async () => ({ ok: true }) };
    };
    await submitFinalVote([...pendingVoteTargets]);
    return {
      firstSelected,
      retainedAfterPeerRender,
      submitEnabled,
      requestCount: requested.length,
      submittedTargets: JSON.parse(requested[0].options.body).target_ids,
      pendingAfterSubmit: pendingVoteTargets.size
    };
  })()`);
  assert.equal(voteResult.firstSelected, true);
  assert.equal(voteResult.retainedAfterPeerRender, true);
  assert.equal(voteResult.submitEnabled, true);
  assert.equal(voteResult.requestCount, 1);
  assert.deepEqual(voteResult.submittedTargets.sort(), ["p2", "p3"]);
  assert.equal(voteResult.pendingAfterSubmit, 0);

  const leaveResult = await evaluate(`(async () => {
    const setSession = () => {
      localRoomCode = "54321";
      localPlayerId = "self-player";
      localCredential = "self-credential";
      localStorage.setItem("varalica_room_code", localRoomCode);
      localStorage.setItem("varalica_player_id", localPlayerId);
      localStorage.setItem("varalica_player_credential", localCredential);
      isExplicitlyLeavingRoom = false;
      leaveNavigationPromise = null;
      socket = null;
    };
    const normalCalls = [];
    setSession();
    window.fetch = async (url, options) => {
      normalCalls.push({ url, options });
      return { ok: true, status: 200, json: async () => ({ ok: true }) };
    };
    const results = await Promise.all([goToHome(), goToHome()]);
    const normal = {
      requestCount: normalCalls.length,
      url: normalCalls[0].url,
      authorization: normalCalls[0].options.headers.Authorization,
      body: JSON.parse(normalCalls[0].options.body),
      results,
      cleared: !localRoomCode && !localPlayerId && !localCredential
    };

    const failedCalls = [];
    setSession();
    window.fetch = async (...args) => {
      failedCalls.push(args);
      throw new Error("offline");
    };
    const failedResult = await goToHome();
    return {
      normal,
      failed: {
        requestCount: failedCalls.length,
        result: failedResult,
        cleared: !localRoomCode && !localPlayerId && !localCredential,
        setupVisible: !setupView.classList.contains("hidden")
      }
    };
  })()`);
  assert.equal(leaveResult.normal.requestCount, 1);
  assert.equal(leaveResult.normal.url, "/api/rooms/54321/leave");
  assert.equal(leaveResult.normal.authorization, "Bearer self-credential");
  assert.deepEqual(leaveResult.normal.body, { player_id: "self-player" });
  assert.deepEqual(leaveResult.normal.results, [true, true]);
  assert.equal(leaveResult.normal.cleared, true);
  assert.equal(leaveResult.failed.requestCount, 1);
  assert.equal(leaveResult.failed.result, false);
  assert.equal(leaveResult.failed.cleared, true);
  assert.equal(leaveResult.failed.setupVisible, true);

  const patchResult = await evaluate(`(() => {
    setupView.classList.add("hidden");
    roomView.classList.remove("hidden");
    const players = [
      {
        id: "p1", name: "Host", avatar: "🥸", is_host: true, is_spectator: false,
        is_current: true, is_active_round_player: true, connection_status: "active",
        play_mode: "chat", reactions: [], association: null, suspicion_percent: 0, has_voted: false
      },
      {
        id: "p2", name: "Guest", avatar: "😎", is_host: false, is_spectator: false,
        is_current: false, is_active_round_player: true, connection_status: "active",
        play_mode: "chat", reactions: [], association: null, suspicion_percent: 0, has_voted: false
      }
    ];
    roomState = {
      room_code: "12345", round_number: 1, state: "discussion", viewer_id: "p1", host_id: "p1",
      viewer_is_spectator: false, player_count: 2, max_players: 10, play_mode: "live",
      suspicion_open: false, suspicion_visible: false, viewer_suspicion_target_id: null,
      change_word_available: false, change_word_seconds_left: 0,
      discussion: { current_player_id: "p1", remaining_seconds: 90, voting_unlocked: false },
      overtime: null, players
    };
    lastPlayersListPhase = "";
    lastSuspicionOpen = null;
    lastHostPanelStructureKey = "";
    renderPlayers();
    renderHostPanel();
    const row = playersList.querySelector('[data-player-id="p2"]');
    const statuses = [];
    for (const status of ["away", "idle", "offline", "active"]) {
      roomState.players[1].connection_status = status;
      renderPlayers();
      const dot = row.querySelector(".status-dot");
      statuses.push({
        status,
        sameRow: row === playersList.querySelector('[data-player-id="p2"]'),
        patched: dot.classList.contains(status),
        titled: Boolean(dot.getAttribute("title"))
      });
    }
    const select = document.querySelector("#transferHostSelect");
    select.value = "p2";
    select.focus();
    const originalSelect = select;
    roomState.discussion = { ...roomState.discussion, remaining_seconds: 89, voting_unlocked: true };
    renderHostPanel();
    const discussionFocus = {
      sameNode: originalSelect === document.querySelector("#transferHostSelect"),
      focused: document.activeElement === originalSelect,
      value: originalSelect.value,
      votingEnabled: !document.querySelector("#hostOpenVotingButton").disabled
    };

    roomState.state = "overtime";
    roomState.discussion = null;
    roomState.overtime = { current_player_id: "p1", remaining_seconds: 29, voting_unlocked: false };
    lastPlayersListPhase = "";
    renderPlayers();
    const overtimeRow = playersList.querySelector('[data-player-id="p2"]');
    roomState.players[1].connection_status = "away";
    renderPlayers();
    return {
      statuses,
      discussionFocus,
      overtimeSameRow: overtimeRow === playersList.querySelector('[data-player-id="p2"]'),
      overtimeAway: overtimeRow.querySelector(".status-dot").classList.contains("away")
    };
  })()`);
  assert.ok(patchResult.statuses.every((item) => item.sameRow && item.patched && item.titled));
  assert.deepEqual(patchResult.discussionFocus, {
    sameNode: true,
    focused: true,
    value: "p2",
    votingEnabled: true,
  });
  assert.equal(patchResult.overtimeSameRow, true);
  assert.equal(patchResult.overtimeAway, true);

  for (const width of [320, 375, 390, 768, 1280]) {
    await send("Emulation.setDeviceMetricsOverride", {
      width,
      height: width <= 390 ? 844 : 900,
      deviceScaleFactor: 1,
      mobile: width <= 390,
    });
    const dimensions = await evaluate(`(async () => {
      setupView.classList.add("hidden");
      roomView.classList.remove("hidden");
      roomState.state = "discussion";
      roomState.discussion = { current_player_id: "p1", remaining_seconds: 80, voting_unlocked: false };
      roomState.overtime = null;
      roomState.players[1].connection_status = "active";
      lastPlayersListPhase = "";
      lastHostPanelStructureKey = "";
      forceFullRender = true;
      render();
      forceFullRender = false;
      const input = document.querySelector("#associationInput");
      const next = document.querySelector("#nextPlayerButton");
      const headers = [];
      for (const language of ["hr", "sr", "de", "tr"]) {
        window.VaralicaI18n.setUiLanguage(language, { manual: true });
        const header = document.querySelector(".players-header");
        const heading = header.querySelector("h2");
        const logo = document.querySelector("#playersHeaderLogo");
        const counter = document.querySelector("#playerCountBadge");
        await logo.decode().catch(() => {});
        const headerRect = header.getBoundingClientRect();
        const headingRect = heading.getBoundingClientRect();
        const logoRect = logo.getBoundingClientRect();
        const counterRect = counter.getBoundingClientRect();
        headers.push({
          language,
          file: decodeURIComponent(new URL(logo.src).pathname.split("/").pop()),
          header: { left: headerRect.left, right: headerRect.right, center: headerRect.left + headerRect.width / 2 },
          heading: { left: headingRect.left, right: headingRect.right, centerY: headingRect.top + headingRect.height / 2 },
          logo: {
            left: logoRect.left,
            right: logoRect.right,
            center: logoRect.left + logoRect.width / 2,
            centerY: logoRect.top + logoRect.height / 2,
            width: logoRect.width,
            height: logoRect.height,
            naturalWidth: logo.naturalWidth,
            naturalHeight: logo.naturalHeight
          },
          counter: {
            left: counterRect.left,
            right: counterRect.right,
            centerY: counterRect.top + counterRect.height / 2,
            text: counter.textContent.trim()
          }
        });
      }
      window.VaralicaI18n.setUiLanguage("hr", { manual: true });
      return {
        viewport: innerWidth,
        documentWidth: document.documentElement.scrollWidth,
        inputRight: input ? input.getBoundingClientRect().right : 0,
        nextRight: next ? next.getBoundingClientRect().right : 0,
        headers
      };
    })()`);
    assert.equal(dimensions.viewport, width);
    assert.ok(dimensions.documentWidth <= width, `${width}px viewport overflowed to ${dimensions.documentWidth}px`);
    assert.ok(dimensions.inputRight <= width);
    assert.ok(dimensions.nextRight <= width);
    const expectedLogoFiles = {
      hr: "Varalica_home.png",
      sr: "Varalica_home.png",
      de: "Betrüger_home.png",
      tr: "Sahtekar_home.png",
    };
    for (const header of dimensions.headers) {
      const label = `${width}px ${header.language}`;
      assert.equal(header.file, expectedLogoFiles[header.language], `${label} used the wrong logo`);
      assert.ok(Math.abs(header.logo.center - header.header.center) <= 0.75, `${label} logo was not centered`);
      assert.ok(header.heading.left >= header.header.left - 0.5, `${label} heading clipped left`);
      assert.ok(header.counter.right <= header.header.right + 0.5, `${label} counter clipped right`);
      assert.ok(header.heading.right <= header.logo.left + 0.5, `${label} heading overlapped logo`);
      assert.ok(header.logo.right <= header.counter.left + 0.5, `${label} logo overlapped counter`);
      assert.ok(header.logo.width > 0 && header.logo.height > 0, `${label} logo was hidden`);
      assert.ok(header.heading.right > header.heading.left, `${label} heading was hidden`);
      assert.match(header.counter.text, /\d+\/10/, `${label} counter was hidden`);
      assert.ok(header.logo.naturalWidth > 0 && header.logo.naturalHeight > 0, `${label} logo did not load`);
      const naturalRatio = header.logo.naturalWidth / header.logo.naturalHeight;
      const renderedRatio = header.logo.width / header.logo.height;
      assert.ok(Math.abs(renderedRatio - naturalRatio) < 0.02, `${label} logo proportions changed`);
      assert.ok(Math.abs(header.heading.centerY - header.logo.centerY) <= 1, `${label} heading left the header row`);
      assert.ok(Math.abs(header.counter.centerY - header.logo.centerY) <= 1, `${label} counter left the header row`);
    }
  }
  await send("Emulation.clearDeviceMetricsOverride");

  console.log("gameplay UI browser checks passed");
}

try {
  await main();
} finally {
  if (cdpSend) {
    try {
      await cdpSend("Browser.close");
    } catch {
      // The browser may already be closing after a failed assertion.
    }
  }
  if (cdpSocket) cdpSocket.close();
  await stopProcess(browserProcess);
  await stopProcess(appProcess);
  rmSync(temporaryRoot, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
}
