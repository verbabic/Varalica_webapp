const setupView = document.querySelector("#setupView");
const landingSplash = document.querySelector("#landingSplash");
const expiredRoomView = document.querySelector("#expiredRoomView");
const homeButton = document.querySelector("#homeButton");
const roomView = document.querySelector("#roomView");
const playerNameInput = document.querySelector("#playerName");
const roomCodeInput = document.querySelector("#roomCode");
const createRoomButton = document.querySelector("#createRoomButton");
const joinRoomButton = document.querySelector("#joinRoomButton");
const copyCodeButton = document.querySelector("#copyCodeButton");
const copyLinkButton = document.querySelector("#copyLinkButton");
const showQrButton = document.querySelector("#showQrButton");
const resetRoomButton = document.querySelector("#resetRoomButton");
const leaveRoomButton = document.querySelector("#leaveRoomButton");
const connectionStatus = document.querySelector("#connectionStatus");
const roomCodeDisplay = document.querySelector("#roomCodeDisplay");
const roundDisplay = document.querySelector("#roundDisplay");
const phaseContent = document.querySelector("#phaseContent");
const associationOverlayDock = document.querySelector("#associationOverlayDock");
const playersList = document.querySelector("#playersList");
const playerCountBadge = document.querySelector("#playerCountBadge");
const errorBox = document.querySelector("#errorBox");
const inviteNotice = document.querySelector("#inviteNotice");
const avatarGrid = document.querySelector("#avatarGrid");
const clearAvatarButton = document.querySelector("#clearAvatarButton");
const qrPanel = document.querySelector("#qrPanel");
const hostPanel = document.querySelector("#hostPanel");
const hostPanelActions = document.querySelector("#hostPanelActions");
const rulesButton = document.querySelector("#rulesButton");
const liveModeButton = document.querySelector("#liveModeButton");
const chatModeButton = document.querySelector("#chatModeButton");
const rulesModal = document.querySelector("#rulesModal");
const leaveModal = document.querySelector("#leaveModal");
const cancelLeaveButton = document.querySelector("#cancelLeaveButton");
const confirmLeaveButton = document.querySelector("#confirmLeaveButton");
const confirmActionModal = document.querySelector("#confirmActionModal");
const confirmActionText = document.querySelector("#confirmActionText");
const cancelActionButton = document.querySelector("#cancelActionButton");
const confirmActionButton = document.querySelector("#confirmActionButton");
const toastContainer = document.querySelector("#toastContainer");
const roomPanelToggle = document.querySelector("#roomPanelToggle");

const SESSION_MAX_AGE_MS = 15 * 60 * 1000;
const HEARTBEAT_INTERVAL_MS = 12000;
const NEXT_PLAYER_UNLOCK_DELAY_MS = 1000;
const PRODUCTION_ORIGIN = "https://varalica.autolovac.space";
const IMPOSTOR_REVEAL_RING_URL = "/static/assets/varalica_neon_ring.svg";
const IMPOSTOR_REVEAL_SMOKE_URL = "/static/assets/varalica_smoke_overlay.svg";
const IMPOSTOR_REVEAL_SCANLINES_URL = "/static/assets/varalica_glitch_scanlines.svg";
const ASSET_CACHE = "20260605_6";
const PRIVATE_CARD_CLOSED_URL = `/static/assets/wordcard.png?v=${ASSET_CACHE}`;
const PRIVATE_CARD_OPEN_NORMAL_URL = `/static/assets/Prikazikartu_player_normal_eyes.png?v=${ASSET_CACHE}`;
const PRIVATE_CARD_OPEN_VARALICA_URL = `/static/assets/Prikazikartu.png?v=${ASSET_CACHE}`;
const REVEAL_COUNTDOWN_BASE_URL = `/static/assets/reveal_countdown_base.png?v=${ASSET_CACHE}`;
const REVEAL_FLYING_CARD_URL = `/static/assets/wordcard.png?v=${ASSET_CACHE}`;
const RESULT_CAUGHT_SCENE_URL = `/static/assets/result_caught_scene.png?v=${ASSET_CACHE}`;
const RESULT_SURVIVED_SCENE_URL = `/static/assets/result_survived_scene_base.png?v=${ASSET_CACHE}`;
const REVEAL_COUNTDOWN_STEP_MS = 1000;
const REVEAL_FLYING_MS = 2400;
const REVEAL_BLACKOUT_MS = 520;
const FINAL_RESULT_FULLSCREEN_MS = 3000;
const REACTION_EMOJIS_LEFT = ["😂", "🧐", "😎"];
const REACTION_EMOJIS_RIGHT = ["🤢", "🤥", "🙈"];
const AVATARS = [
  "🥸","🤤","😁","😇","🥳","😎","😝","👹","😈","🤠","🤡","👻","💩","👽","👾","🤖","🎃","😺","🧠","👶",
  "👩‍🦰","👨🏻","👨🏿","👨🏽","👩🏾‍🦰","👩🏻‍🦱","🧑🏻‍🦱","🧑🏾‍🦱","👨🏿‍🦰","👨🏽‍🦳","🧔","🧔🏼‍♂️","👲","🧕","👳🏻‍♂️","👮‍♀️","👮","👮🏻‍♂️","👷‍♀️","💂‍♀️",
  "👨🏻‍⚕️","👩‍🎓","🧑‍🍳","🧑‍🎤","👨‍🏫","👩‍🏭","👨‍🎤","👩‍🏫","👩🏻‍💻","👩‍🔧","👨🏻‍🚒","🧑‍🚒","👩‍🚀","🥷🏻","🥷🏿","🦹‍♀️","🦸‍♂️","🤴","🧌","🧛",
  "🧞‍♀️","🧜‍♀️","🧟","🧟‍♂️","💃","👑","⛑️","👠","🐶","🐭","🐹","🦊","🐱","🐰","🐻","🐼","🦁","🐯","🐻‍❄️","🐷",
  "🐽","🐸","🐵","🐒","🐥","🐴","🐗","🦄","🐝","🐢","🐞","🐌","🦋","🐛","🪲","🐍","🪼","🦞","🐬","🐳",
  "🦧","🐖","🐏","🐎","🦬","🐁","🦜","🌞","⭐️","⛄️","🍉","🍎","🍆","🌽","🥨","🍳","🍖","🍟","🍭","⚽️",
  "🏀","🎾","🎱","⛷️","🏋️","🪂","🚵‍♀️","🎹","🎷","🎸","🪗","🎲","🚗","🚕","🚒","🚜","🚓","🚑","🚛","✈️","🧸",
];

initLandingSplash();
expireOldSession();

let roomState = null;
let socket = null;
let localRoomCode = localStorage.getItem("varalica_room_code") || "";
let localPlayerId = localStorage.getItem("varalica_player_id") || "";
let selectedAvatar = localStorage.getItem("varalica_avatar") || "";
let selectedPlayMode = localStorage.getItem("varalica_play_mode") || "live";
let selectedCategory = localStorage.getItem("varalica_selected_category") || "Sve kategorije";
let selectedDiscussionSeconds = Number(localStorage.getItem("varalica_discussion_seconds") || 120);
let selectedVaralicaCount = Number(localStorage.getItem("varalica_count") || 1);
let associationDraft = sessionStorage.getItem("varalica_association_draft") || "";
let associationSentFeedbackUntil = 0;
let associationSendInFlight = false;
let hasRevealedPrivateCard = false;
let lastRoomState = "";
let revealSequence = {
  active: false,
  phase: "complete",
  countdown: 0,
  complete: false,
  showReplay: false,
};
let revealSequenceTimers = [];
let finalResultSceneState = {
  roundKey: "",
  mode: "fullscreen",
  timer: null,
};
let inviteRoomCode = "";
let reconnectTimer = null;
let heartbeatTimer = null;
let shouldReconnectSocket = true;
let connectionMode = "disconnected";
let hadSocketDisconnect = false;
let isExplicitlyLeavingRoom = false;
let lastSeenEventId = "";
let currentTurnId = "";
let nextPlayerUnlockAt = 0;
let nextPlayerCountdownTimer = null;
let pendingNextPlayerTurnId = "";
let pendingNextPlayerStartedAt = 0;
let pendingConfirmAction = null;
let roomPanelCollapsed = sessionStorage.getItem("varalica_room_panel_collapsed") === "true";
let lastAssociationBannerStackKey = "";
let lastPlayersListPhase = "";
let lastRenderedRevealPhase = "";

function initLandingSplash() {
  if (!landingSplash) return;
  const splashImage = landingSplash.querySelector(".landing-splash-image");
  let removed = false;

  const removeSplash = () => {
    if (removed) return;
    removed = true;
    landingSplash.classList.add("is-hiding");
    window.setTimeout(() => landingSplash.remove(), 760);
  };

  window.setTimeout(removeSplash, 3000);
  window.setTimeout(removeSplash, 5000);
  splashImage?.addEventListener("error", removeSplash, { once: true });
}

const pathRoomMatch = window.location.pathname.match(/^\/room\/([A-Z0-9]{5})$/i);
if (pathRoomMatch) {
  inviteRoomCode = pathRoomMatch[1].toUpperCase();
  setupView.classList.add("hidden");
  createRoomButton.classList.add("hidden");
}

playerNameInput.value = sessionStorage.getItem("varalica_username") || "";

createRoomButton.addEventListener("click", createRoom);
joinRoomButton.addEventListener("click", joinRoom);
homeButton.addEventListener("click", goToHome);
playerNameInput.addEventListener("input", () => {
  sessionStorage.setItem("varalica_username", playerNameInput.value.trim());
  updateJoinButtons();
});
roomCodeInput.addEventListener("input", () => {
  roomCodeInput.value = roomCodeInput.value.replace(/[^1-9]/g, "").slice(0, 5);
});
copyCodeButton.addEventListener("click", copyRoomCode);
copyLinkButton.addEventListener("click", copyRoomLink);
showQrButton.addEventListener("click", toggleQrPanel);
resetRoomButton.addEventListener("click", promptRestartRoom);
leaveRoomButton.addEventListener("click", showLeaveModal);
roomPanelToggle?.addEventListener("click", toggleRoomPanel);
phaseContent?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-reaction-emoji]");
  if (!button || button.disabled) return;
  if (!canSendReactions()) return;
  sendReaction(button.dataset.reactionEmoji);
});
rulesButton.addEventListener("click", () => showModal(rulesModal));
liveModeButton.addEventListener("click", () => setPlayMode("live"));
chatModeButton.addEventListener("click", () => setPlayMode("chat"));
cancelLeaveButton.addEventListener("click", () => hideModal(leaveModal));
confirmLeaveButton.addEventListener("click", leaveRoom);
cancelActionButton.addEventListener("click", closeConfirmAction);
confirmActionButton.addEventListener("click", async () => {
  const action = pendingConfirmAction;
  closeConfirmAction();
  if (action) await action();
});
document.querySelectorAll(".modal-backdrop").forEach((modal) => {
  modal.addEventListener("click", (event) => {
    if (event.target === modal) hideModal(modal);
  });
});
document.querySelectorAll("[data-close-modal]").forEach((button) => {
  button.addEventListener("click", () => {
    const modal = document.querySelector(`#${button.dataset.closeModal}`);
    if (modal) hideModal(modal);
  });
});
document.addEventListener("visibilitychange", () => {
  touchSession();
  sendHeartbeat();
});
window.addEventListener("beforeunload", sendLikelyTabClose);
window.addEventListener("pagehide", (event) => {
  if (!event.persisted && !isLikelyMobileBrowser()) {
    sendLikelyTabClose();
  }
});
renderAvatarGrid();
renderModeToggle();
applyRoomPanelCollapse();
setConnectionMode("disconnected");
touchSession();
updateJoinButtons();

function toggleRoomPanel() {
  roomPanelCollapsed = !roomPanelCollapsed;
  sessionStorage.setItem("varalica_room_panel_collapsed", roomPanelCollapsed ? "true" : "false");
  applyRoomPanelCollapse();
}

function applyRoomPanelCollapse() {
  const appShell = document.querySelector(".app-shell");
  if (!roomPanelToggle) return;
  const inRoom = !roomView.classList.contains("hidden");
  appShell?.classList.toggle("room-compact-collapsed", roomPanelCollapsed && inRoom);
  roomPanelToggle.setAttribute("aria-expanded", roomPanelCollapsed ? "false" : "true");
  roomPanelToggle.textContent = roomPanelCollapsed ? "▼" : "▲";
}

function hasValidPlayerName() {
  const length = playerNameInput.value.trim().length;
  return length >= 3 && length <= 15;
}

function updateJoinButtons() {
  const disabled = !hasValidPlayerName();
  createRoomButton.disabled = disabled || createRoomButton.classList.contains("hidden");
  joinRoomButton.disabled = disabled;
}

function setPlayMode(mode) {
  const nextMode = mode === "chat" ? "chat" : "live";
  const roomMode = roomState?.play_mode === "chat" ? "chat" : roomState?.play_mode === "live" ? "live" : "";
  if (roomMode) {
    selectedPlayMode = roomMode;
    localStorage.setItem("varalica_play_mode", selectedPlayMode);
    renderModeToggle();
    if (nextMode !== roomMode) {
      showToast(`Host je napravio ${roomMode === "chat" ? "Chat" : "Live"} sobu.`, "info");
    }
    return;
  }

  selectedPlayMode = nextMode;
  localStorage.setItem("varalica_play_mode", selectedPlayMode);
  renderModeToggle();
}

function syncPlayModeFromRoom() {
  if (!roomState) return;
  const me = roomState.players.find((player) => player.id === roomState.viewer_id);
  const roomMode = roomState.play_mode === "chat" ? "chat" : roomState.play_mode === "live" ? "live" : "";
  if (roomMode || me?.play_mode) {
    selectedPlayMode = roomMode || me.play_mode;
    localStorage.setItem("varalica_play_mode", selectedPlayMode);
  }
  renderModeToggle();
}

function renderModeToggle() {
  const roomMode = roomState?.play_mode === "chat" ? "chat" : roomState?.play_mode === "live" ? "live" : "";
  liveModeButton.classList.toggle("active", selectedPlayMode === "live");
  chatModeButton.classList.toggle("active", selectedPlayMode === "chat");
  liveModeButton.classList.toggle("mode-locked-unavailable", Boolean(roomMode && roomMode !== "live"));
  chatModeButton.classList.toggle("mode-locked-unavailable", Boolean(roomMode && roomMode !== "chat"));
  liveModeButton.disabled = false;
  chatModeButton.disabled = false;
}

async function createRoom() {
  clearError();
  const name = playerNameInput.value.trim();
  if (!hasValidPlayerName()) {
    updateJoinButtons();
    showError("Username mora imati 3 do 15 znakova.");
    return;
  }
  sessionStorage.setItem("varalica_username", name);
  const result = await apiRequest("/api/rooms", { name, avatar: selectedAvatar || null, play_mode: selectedPlayMode });
  if (!result) return;
  if (result.room_play_mode) {
    selectedPlayMode = result.room_play_mode;
    localStorage.setItem("varalica_play_mode", selectedPlayMode);
    renderModeToggle();
  }
  enterRoom(result.room_code, result.player_id, result.avatar);
}

async function joinRoom() {
  clearError();
  const name = playerNameInput.value.trim();
  if (!hasValidPlayerName()) {
    updateJoinButtons();
    showError("Username mora imati 3 do 15 znakova.");
    return;
  }
  sessionStorage.setItem("varalica_username", name);
  const code = roomCodeInput.value.trim().toUpperCase();
  if (!code) {
    showError("Unesi kod sobe.");
    return;
  }
  try {
    const response = await fetch(`/api/rooms/${code}/join`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        avatar: selectedAvatar || null,
        play_mode: selectedPlayMode,
        player_id: localRoomCode === code ? localPlayerId || null : null,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      if (response.status === 404 && isExpiredRoomDetail(data.detail)) {
        showExpiredRoomUI(code);
        return;
      }
      showError(data.detail || "Doslo je do greske.");
      return;
    }
    if (data.room_play_mode) {
      selectedPlayMode = data.room_play_mode;
      localStorage.setItem("varalica_play_mode", selectedPlayMode);
      renderModeToggle();
    }
    enterRoom(data.room_code, data.player_id, data.avatar);
    if (data.spectator && data.message) {
      showToast(data.message, "info");
    }
  } catch {
    showError("Nije moguce spojiti se na server.");
  }
}

function enterRoom(roomCode, playerId, avatar) {
  isExplicitlyLeavingRoom = false;
  localRoomCode = roomCode;
  localPlayerId = playerId;
  hasRevealedPrivateCard = false;
  lastPlayersListPhase = "";
  localStorage.setItem("varalica_room_code", roomCode);
  localStorage.setItem("varalica_player_id", playerId);
  touchSession();
  if (avatar) {
    selectedAvatar = avatar;
    localStorage.setItem("varalica_avatar", avatar);
    renderAvatarGrid();
  }
  window.history.replaceState({}, "", `/room/${roomCode}`);
  setupView.classList.add("hidden");
  roomView.classList.remove("hidden");
  connectionStatus.classList.remove("hidden");
  applyRoomPanelCollapse();
  connectSocket();
}

function setConnectionMode(mode) {
  connectionMode = mode;
  if ((!localRoomCode && !roomState) || (roomView.classList.contains("hidden") && !roomState)) {
    connectionStatus.classList.add("hidden");
    connectionStatus.textContent = "";
    return;
  }
  connectionStatus.classList.remove("hidden");
  const labels = {
    stable: "Stable",
    reconnecting: "Reconnecting",
    disconnected: "Disconnected",
  };
  const icons = {
    stable: "●",
    reconnecting: "●",
    disconnected: "●",
  };
  connectionStatus.className = `status-pill connection-${mode}`;
  connectionStatus.textContent = `${icons[mode]} ${labels[mode]}`;
}

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.classList.add("leaving"), 1800);
  setTimeout(() => toast.remove(), 2300);
}

function handleRoomEvent(event) {
  if (!event || event.event_id === lastSeenEventId) return;
  lastSeenEventId = event.event_id;
  if (event.created_at && Date.now() / 1000 - event.created_at > 6) return;
  if (event.type === "change_word") {
    hasRevealedPrivateCard = false;
    showToast("Host je promijenio riječ. Pogledajte novu karticu.", "success");
    return;
  }
  if (event.player_id === localPlayerId) return;
  if (event.type === "join") {
    showToast(`${event.player_avatar || ""} ${event.player_name} se pridruzio`, "celebrate");
  }
  if (event.type === "reconnect") {
    showToast(`${event.player_avatar || ""} ${event.player_name} se vratio`, "success");
  }
}

function updateTurnLock(state) {
  const turnId = state.discussion?.current_player_id || state.overtime?.current_player_id || "";
  if (turnId && turnId !== currentTurnId) {
    currentTurnId = turnId;
    clearPendingNextPlayer();
    nextPlayerUnlockAt = Date.now() + NEXT_PLAYER_UNLOCK_DELAY_MS;
    scheduleNextPlayerCountdown();
  }
}

function clearPendingNextPlayer() {
  pendingNextPlayerTurnId = "";
  pendingNextPlayerStartedAt = 0;
}

function scheduleNextPlayerCountdown() {
  if (nextPlayerCountdownTimer) clearTimeout(nextPlayerCountdownTimer);
  if (Date.now() >= nextPlayerUnlockAt) {
    render();
    return;
  }
  nextPlayerCountdownTimer = setTimeout(scheduleNextPlayerCountdown, 250);
  render();
}

function nextPlayerLockSecondsLeft() {
  return Math.max(0, Math.ceil((nextPlayerUnlockAt - Date.now()) / 1000));
}

function showModal(modal) {
  modal.classList.remove("hidden");
}

function hideModal(modal) {
  modal.classList.add("hidden");
}

function showLeaveModal() {
  showModal(leaveModal);
}

function showConfirmAction(message, action, danger = true) {
  confirmActionText.textContent = message;
  pendingConfirmAction = action;
  confirmActionButton.classList.toggle("danger", danger);
  confirmActionButton.classList.toggle("secondary", !danger);
  showModal(confirmActionModal);
}

function closeConfirmAction() {
  pendingConfirmAction = null;
  hideModal(confirmActionModal);
}

function connectSocket() {
  shouldReconnectSocket = true;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (socket) {
    shouldReconnectSocket = false;
    socket.close();
  }
  shouldReconnectSocket = true;
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${window.location.host}/ws/${localRoomCode}/${localPlayerId}`);

  socket.addEventListener("open", () => {
    setConnectionMode("stable");
    startHeartbeat();
    if (hadSocketDisconnect) {
      showToast("Ponovno povezano", "success");
      hadSocketDisconnect = false;
    }
    touchSession();
  });

  socket.addEventListener("message", (event) => {
    const previousState = roomState?.state || "";
    const incoming = JSON.parse(event.data);
    if (incoming.type === "kicked") {
      handleKicked(incoming.message || "Izbaceni ste iz sobe.");
      return;
    }
    roomState = incoming;
    touchSession();
    handleRoomEvent(roomState.last_event);
    updateTurnLock(roomState);
    if (roomState.state !== previousState) {
      lastPlayersListPhase = "";
    }
    if (roomState.state === "reveal" && previousState !== "reveal") {
      hasRevealedPrivateCard = false;
      clearAssociationSentFeedback();
      resetRevealSequence();
    }
    syncRevealCardStateFromRoom();
    if (roomState.state === "lobby" && previousState && previousState !== "lobby") {
      hasRevealedPrivateCard = false;
      lastPlayersListPhase = "";
      clearAssociationSentFeedback();
      resetRevealSequence();
      associationDraft = "";
      sessionStorage.removeItem("varalica_association_draft");
      lastAssociationBannerStackKey = "";
      syncPlayModeFromRoom();
    }
    if (roomState.state !== "discussion" && roomState.state !== "overtime") {
      lastAssociationBannerStackKey = "";
    }
    if (roomState.state === "results" && previousState !== "results") {
      startRevealCountdown();
    }
    lastRoomState = roomState.state;
    render();
  });

  socket.addEventListener("close", (event) => {
    stopHeartbeat();
    hadSocketDisconnect = true;
    if (event.code === 1008) {
      if (!shouldReconnectSocket) return;
      handleInvalidSessionClose();
      return;
    }
    if (shouldReconnectSocket && localRoomCode && localPlayerId) {
      setConnectionMode("reconnecting");
      reconnectTimer = setTimeout(connectSocket, 2000);
    } else {
      setConnectionMode("disconnected");
    }
  });
}

async function handleInvalidSessionClose() {
  const code = localRoomCode || inviteRoomCode || roomCodeInput.value.trim().toUpperCase();
  if (code && await validateRoomExists(code)) {
    shouldReconnectSocket = false;
    clearStoredSession();
    localRoomCode = "";
    localPlayerId = "";
    roomState = null;
    showValidInviteUI(code);
    showError("Sesija je istekla. Unesi ime i pridruži se ponovo.");
    setConnectionMode("disconnected");
    return;
  }
  handleExpiredRoom();
}

function startHeartbeat() {
  stopHeartbeat();
  sendHeartbeat();
  heartbeatTimer = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_MS);
}

function stopHeartbeat() {
  if (heartbeatTimer) clearInterval(heartbeatTimer);
  heartbeatTimer = null;
}

function sendHeartbeat() {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "heartbeat", hidden: document.hidden, sent_at: Date.now() }));
  }
}

function isLikelyMobileBrowser() {
  return window.matchMedia("(pointer: coarse)").matches || navigator.maxTouchPoints > 0;
}

function sendLikelyTabClose() {
  if (isExplicitlyLeavingRoom || !localRoomCode || !localPlayerId) return;
  const payload = JSON.stringify({ player_id: localPlayerId });
  const url = `/api/rooms/${encodeURIComponent(localRoomCode)}/tab-close`;
  if (navigator.sendBeacon) {
    const blob = new Blob([payload], { type: "application/json" });
    navigator.sendBeacon(url, blob);
    return;
  }
  fetch(url, {
    method: "POST",
    body: payload,
    headers: { "Content-Type": "application/json" },
    keepalive: true,
  }).catch(() => {});
}

async function startRound() {
  clearError();
  touchSession();
  hasRevealedPrivateCard = false;
  await apiRequest(`/api/rooms/${localRoomCode}/start`, {
    player_id: localPlayerId,
    category: selectedCategory,
    discussion_seconds: selectedDiscussionSeconds,
    varalica_count: selectedVaralicaCount,
  });
}

async function markSecretViewed() {
  return apiRequest(`/api/rooms/${localRoomCode}/view-secret`, { player_id: localPlayerId });
}

async function changeWord() {
  clearError();
  touchSession();
  hasRevealedPrivateCard = false;
  await apiRequest(`/api/rooms/${localRoomCode}/change-word`, { player_id: localPlayerId });
}

async function confirmSeen() {
  clearError();
  touchSession();
  await apiRequest(`/api/rooms/${localRoomCode}/confirm`, { player_id: localPlayerId });
}

async function nextPlayer() {
  clearError();
  touchSession();
  const turnId = currentTurnPlayerId();
  if (!turnId) {
    showError("Trenutni igrač nije spreman.");
    return;
  }
  if (pendingNextPlayerTurnId && pendingNextPlayerTurnId === turnId) return;
  pendingNextPlayerTurnId = turnId;
  pendingNextPlayerStartedAt = Date.now();
  syncDiscussionMonitorActions();
  const response = await apiRequest(`/api/rooms/${localRoomCode}/next-player`, { player_id: localPlayerId });
  if (!response?.ok) {
    clearPendingNextPlayer();
    syncDiscussionMonitorActions();
  }
}

async function requestVote() {
  clearError();
  touchSession();
  await apiRequest(`/api/rooms/${localRoomCode}/request-vote`, { player_id: localPlayerId });
}

async function openFinalVoting() {
  clearError();
  touchSession();
  await apiRequest(`/api/rooms/${localRoomCode}/open-final-voting`, { player_id: localPlayerId });
}

async function submitFinalVote(targetIds) {
  clearError();
  touchSession();
  const normalizedTargets = Array.isArray(targetIds) ? targetIds : [targetIds];
  await apiRequest(`/api/rooms/${localRoomCode}/vote`, {
    player_id: localPlayerId,
    target_id: normalizedTargets[0] || null,
    target_ids: normalizedTargets,
  });
}

async function sendAssociation() {
  if (associationSendInFlight) return;
  clearError();
  touchSession();
  const input = document.querySelector("#associationInput");
  const text = input?.value || associationDraft;
  if (!text.trim()) {
    showError("Unesi asocijaciju.");
    return;
  }
  associationSendInFlight = true;
  try {
    const result = await apiRequest(`/api/rooms/${localRoomCode}/association`, {
      player_id: localPlayerId,
      text: text.trim(),
    });
    if (!result) return;
    associationDraft = "";
    sessionStorage.removeItem("varalica_association_draft");
    if (input) input.value = "";
    associationSentFeedbackUntil = Date.now() + 3000;
    updateAssociationComposerState();
    window.setTimeout(() => {
      if (Date.now() >= associationSentFeedbackUntil) {
        updateAssociationComposerState();
      }
    }, 3100);
  } finally {
    associationSendInFlight = false;
  }
}

async function sendReaction(emoji) {
  clearError();
  touchSession();
  const target = primaryReactionTarget();
  if (!target?.target_type || !target?.target_id || !localPlayerId) return;
  const payload = {
    player_id: localPlayerId,
    emoji: String(emoji || "").trim(),
    target_type: String(target.target_type),
    target_id: String(target.target_id),
  };
  if (!payload.emoji) return;
  await apiRequest(`/api/rooms/${localRoomCode}/reaction`, payload);
}

function primaryReactionTarget() {
  if (!roomState || !["discussion", "overtime"].includes(roomState.state)) return null;

  const banners = roomState.association_banners || [];
  if (banners.length) {
    const banner = banners[banners.length - 1];
    if (banner?.id) {
      return {
        target_type: "chat_association",
        target_id: banner.id,
        subject_player_id: banner.player_id,
      };
    }
  }

  const phaseData = roomState.state === "overtime" ? roomState.overtime : roomState.discussion;
  const currentId = phaseData?.current_player_id;
  if (!currentId) return null;

  const currentPlayer = roomState.players.find((player) => player.id === currentId);
  if (currentPlayer?.play_mode !== "live") return null;

  return {
    target_type: "live_player",
    target_id: currentId,
    subject_player_id: currentId,
  };
}

function canSendReactions() {
  return Boolean(primaryReactionTarget());
}

async function startNewRound() {
  clearError();
  touchSession();
  hasRevealedPrivateCard = false;
  resetRevealSequence();
  clearAssociationSentFeedback();
  lastPlayersListPhase = "";
  await apiRequest(`/api/rooms/${localRoomCode}/new-round`, { player_id: localPlayerId });
}

function promptRestartRoom() {
  showConfirmAction("Resetovati sobu i vratiti je na postavke?", () => resetRoom(), false);
}

async function resetRoom() {
  clearError();
  touchSession();
  hasRevealedPrivateCard = false;
  resetRevealSequence();
  associationDraft = "";
  clearAssociationSentFeedback();
  sessionStorage.removeItem("varalica_association_draft");
  await apiRequest(`/api/rooms/${localRoomCode}/reset`, { player_id: localPlayerId });
}

function clearAssociationSentFeedback() {
  associationSentFeedbackUntil = 0;
  associationSendInFlight = false;
}

async function kickPlayer(targetId) {
  clearError();
  touchSession();
  await apiRequest(`/api/rooms/${localRoomCode}/kick`, { player_id: localPlayerId, target_id: targetId });
}

async function transferHost(targetId) {
  clearError();
  touchSession();
  await apiRequest(`/api/rooms/${localRoomCode}/transfer-host`, { player_id: localPlayerId, target_id: targetId });
}

async function leaveRoom() {
  clearError();
  hideModal(leaveModal);
  isExplicitlyLeavingRoom = true;
  shouldReconnectSocket = false;
  if (localRoomCode && localPlayerId) {
    await apiRequest(`/api/rooms/${localRoomCode}/leave`, { player_id: localPlayerId });
  }
  if (socket) socket.close();
  localStorage.removeItem("varalica_room_code");
  localStorage.removeItem("varalica_player_id");
  localStorage.removeItem("varalica_last_active_at");
  sessionStorage.clear();
  localRoomCode = "";
  localPlayerId = "";
  roomState = null;
  lastPlayersListPhase = "";
  roomView.classList.add("hidden");
  setupView.classList.remove("hidden");
  applyRoomPanelCollapse();
  window.history.replaceState({}, "", "/");
}

async function startOvertime() {
  clearError();
  touchSession();
  await apiRequest(`/api/rooms/${localRoomCode}/start-overtime`, { player_id: localPlayerId });
}

async function revealResults() {
  clearError();
  touchSession();
  await apiRequest(`/api/rooms/${localRoomCode}/reveal`, { player_id: localPlayerId });
}

function startRevealCountdown() {
  resetRevealSequence();
  if (!roomState?.results || !resultVaralice(roomState.results).length) return;
  const roundKey = finalResultRoundKey();
  if (hasCompletedRevealAnimation(roundKey)) {
    revealSequence = {
      active: false,
      phase: "complete",
      countdown: 0,
      complete: true,
      showReplay: true,
    };
    finalResultSceneState = {
      roundKey,
      mode: "compact",
      timer: null,
    };
    return;
  }

  const reducedMotion = prefersReducedMotion();
  const numberDuration = reducedMotion ? 280 : REVEAL_COUNTDOWN_STEP_MS;
  const afterOnePause = reducedMotion ? 80 : 180;
  const flyingDuration = reducedMotion ? 220 : REVEAL_FLYING_MS;
  const blackoutDuration = reducedMotion ? 120 : REVEAL_BLACKOUT_MS;
  const replayDelay = 2000;

  revealSequence = {
    active: true,
    phase: "countdown_5",
    countdown: 5,
    complete: false,
    showReplay: false,
  };
  lastRenderedRevealPhase = "";

  const isCurrentUserVaralica = isViewerVaralica(roomState.results);
  if (isCurrentUserVaralica && navigator.vibrate) {
    navigator.vibrate([120, 80, 200]);
  }

  const setRevealPhase = (phase, countdown = 0) => {
    if (!roomState || roomState.state !== "results") return;
    revealSequence = {
      active: phase !== "complete",
      phase,
      countdown,
      complete: phase === "complete",
      showReplay: false,
    };
    render();
  };

  setRevealPhase("countdown_5", 5);
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("countdown_4", 4), numberDuration));
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("countdown_3", 3), numberDuration * 2));
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("countdown_2", 2), numberDuration * 3));
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("countdown_1", 1), numberDuration * 4));
  const flyingAt = numberDuration * 5 + afterOnePause;
  const blackoutAt = flyingAt + flyingDuration;
  const completeAt = blackoutAt + blackoutDuration;
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("flying_card"), flyingAt));
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("fade_black"), blackoutAt));
  revealSequenceTimers.push(setTimeout(() => {
    setRevealPhase("complete");
  }, completeAt));
  revealSequenceTimers.push(setTimeout(() => {
    revealSequence = { ...revealSequence, showReplay: true };
    render();
  }, completeAt + replayDelay));
}

function revealAnimationStorageKey(roundKey = finalResultRoundKey()) {
  return roundKey ? `varalica_reveal_seen:${localPlayerId || "viewer"}:${roundKey}` : "";
}

function hasCompletedRevealAnimation(roundKey = finalResultRoundKey()) {
  const key = revealAnimationStorageKey(roundKey);
  return Boolean(key && localStorage.getItem(key) === "true");
}

function markRevealAnimationComplete(roundKey = finalResultRoundKey()) {
  const key = revealAnimationStorageKey(roundKey);
  if (key) localStorage.setItem(key, "true");
}

function prefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function resetRevealSequence() {
  revealSequenceTimers.forEach((timer) => clearTimeout(timer));
  revealSequenceTimers = [];
  lastRenderedRevealPhase = "";
  revealSequence = {
    active: false,
    phase: "complete",
    countdown: 0,
    complete: false,
    showReplay: false,
  };
  resetFinalResultSceneState();
}

function resetFinalResultSceneState() {
  if (finalResultSceneState.timer) {
    clearTimeout(finalResultSceneState.timer);
  }
  finalResultSceneState = {
    roundKey: "",
    mode: "fullscreen",
    timer: null,
  };
}

function finalResultRoundKey() {
  if (!roomState || roomState.state !== "results") return "";
  const varalicaIds = resultVaralice(roomState.results || {})
    .map((player) => player.id)
    .join(",");
  return `${roomState.room_code || ""}:${roomState.round_number || 1}:${varalicaIds}:${roomState.results?.was_varalica_caught === true}`;
}

function ensureFinalResultSceneTransition() {
  const roundKey = finalResultRoundKey();
  if (!roundKey) return "fullscreen";

  if (finalResultSceneState.roundKey !== roundKey) {
    if (finalResultSceneState.timer) {
      clearTimeout(finalResultSceneState.timer);
    }
    finalResultSceneState = {
      roundKey,
      mode: "fullscreen",
      timer: null,
    };
  }

  if (finalResultSceneState.mode === "fullscreen" && !finalResultSceneState.timer) {
    const minimizeDelay = prefersReducedMotion() ? 600 : FINAL_RESULT_FULLSCREEN_MS;
    finalResultSceneState.timer = setTimeout(() => {
      if (roomState?.state !== "results" || finalResultRoundKey() !== roundKey) {
        resetFinalResultSceneState();
        return;
      }
      markRevealAnimationComplete(roundKey);
      finalResultSceneState = {
        ...finalResultSceneState,
        mode: "compact",
        timer: null,
      };
      render();
    }, minimizeDelay);
  }

  return finalResultSceneState.mode;
}

function expireOldSession() {
  const lastActiveAt = Number(localStorage.getItem("varalica_last_active_at") || 0);
  const hasSession = Boolean(localStorage.getItem("varalica_room_code") || localStorage.getItem("varalica_player_id"));
  if (hasSession && (!lastActiveAt || Date.now() - lastActiveAt > SESSION_MAX_AGE_MS)) {
    clearStoredSession();
  }
}

function touchSession() {
  if (localStorage.getItem("varalica_room_code") || localStorage.getItem("varalica_player_id")) {
    localStorage.setItem("varalica_last_active_at", String(Date.now()));
  }
}

function clearStoredSession() {
  localStorage.removeItem("varalica_room_code");
  localStorage.removeItem("varalica_player_id");
  localStorage.removeItem("varalica_last_active_at");
}

function isExpiredRoomDetail(detail) {
  const message = String(detail || "").toLowerCase();
  return message.includes("istekla") || message.includes("ne postoji");
}

function showValidInviteUI(code) {
  setCinematicRevealActive(false);
  expiredRoomView.classList.add("hidden");
  setupView.classList.remove("hidden");
  roomView.classList.add("hidden");
  homeButton.classList.remove("hidden");
  roomCodeInput.value = code;
  inviteNotice.textContent = `Pridruzuješ se sobi ${code}. Unesi ime i klikni “Pridruzi se”.`;
  inviteNotice.classList.remove("hidden");
  createRoomButton.classList.add("hidden");
  clearError();
  updateJoinButtons();
}

function showExpiredRoomUI(code) {
  setCinematicRevealActive(false);
  shouldReconnectSocket = false;
  stopHeartbeat();
  if (socket) socket.close();
  clearStoredSession();
  inviteRoomCode = "";
  localRoomCode = "";
  localPlayerId = "";
  roomState = null;

  setupView.classList.add("hidden");
  roomView.classList.add("hidden");
  expiredRoomView.classList.remove("hidden");
  homeButton.classList.remove("hidden");
  inviteNotice.classList.add("hidden");
  connectionStatus.classList.add("hidden");
  clearError();

  setConnectionMode("disconnected");
  applyRoomPanelCollapse();
}

function goToHome() {
  setCinematicRevealActive(false);
  shouldReconnectSocket = false;
  stopHeartbeat();
  if (socket) socket.close();
  clearStoredSession();
  inviteRoomCode = "";
  localRoomCode = "";
  localPlayerId = "";
  roomState = null;

  expiredRoomView.classList.add("hidden");
  setupView.classList.remove("hidden");
  roomView.classList.add("hidden");
  homeButton.classList.remove("hidden");
  inviteNotice.classList.add("hidden");
  roomCodeInput.value = "";
  createRoomButton.classList.remove("hidden");
  connectionStatus.classList.add("hidden");
  clearError();
  updateJoinButtons();
  window.history.replaceState({}, "", "/");
  setConnectionMode("disconnected");
  applyRoomPanelCollapse();
}

function handleExpiredRoom() {
  const code = localRoomCode || inviteRoomCode || roomCodeInput.value.trim().toUpperCase();
  showExpiredRoomUI(code);
  window.history.replaceState({}, "", "/");
}

function handleKicked(message) {
  shouldReconnectSocket = false;
  stopHeartbeat();
  if (socket) socket.close();
  clearStoredSession();
  sessionStorage.clear();
  localRoomCode = "";
  localPlayerId = "";
  roomState = null;
  roomView.classList.add("hidden");
  setupView.classList.remove("hidden");
  inviteNotice.classList.add("hidden");
  createRoomButton.classList.remove("hidden");
  updateJoinButtons();
  window.history.replaceState({}, "", "/");
  setConnectionMode("disconnected");
  applyRoomPanelCollapse();
  showToast(message, "error");
}

async function validateRoomExists(roomCode) {
  try {
    const response = await fetch(`/api/rooms/${roomCode}/status`);
    if (!response.ok) return false;
    return true;
  } catch {
    return false;
  }
}

function renderAvatarGrid() {
  avatarGrid.innerHTML = AVATARS.map(
    (avatar) => `
      <button
        class="avatar-option ${avatar === selectedAvatar ? "selected" : ""}"
        type="button"
        data-avatar="${escapeHtml(avatar)}"
        aria-label="Avatar ${escapeHtml(avatar)}"
      >
        ${escapeHtml(avatar)}
      </button>
    `,
  ).join("");

  avatarGrid.querySelectorAll(".avatar-option").forEach((button) => {
    button.addEventListener("click", () => {
      selectedAvatar = button.dataset.avatar;
      localStorage.setItem("varalica_avatar", selectedAvatar);
      renderAvatarGrid();
    });
  });
}

function playerNameHtml(player) {
  const avatar = player?.avatar || "🎲";
  const name = player?.name || "Nepoznato";
  return `<span class="player-avatar">${escapeHtml(avatar)}</span><span>${escapeHtml(name)}</span>`;
}

function playerNameText(player) {
  const avatar = player?.avatar || "🎲";
  const name = player?.name || "Nepoznato";
  return `${avatar} ${name}`;
}

function inviteOrigin() {
  const { hostname, origin, port, protocol } = window.location;
  const host = (hostname || "").toLowerCase();

  if (host === "varalica.autolovac.space" || host === "91.98.83.121") {
    return PRODUCTION_ORIGIN;
  }
  if (!host || host === "0.0.0.0") {
    return PRODUCTION_ORIGIN;
  }
  if (host === "127.0.0.1") {
    const portSuffix = port ? `:${port}` : "";
    return `${protocol}//localhost${portSuffix}`;
  }
  return origin;
}

function isValidInviteUrl(url) {
  if (!url || typeof url !== "string") return false;
  const trimmed = url.trim();
  if (!trimmed || trimmed.includes("undefined") || trimmed.includes("null")) return false;
  try {
    const parsed = new URL(trimmed);
    if (!/^https?:$/.test(parsed.protocol)) return false;
    const host = parsed.hostname.toLowerCase();
    if (!host || host === "0.0.0.0" || host === "127.0.0.1") return false;
    const roomMatch = parsed.pathname.match(/^\/room\/([A-Z0-9]{5})$/i);
    if (!roomMatch) return false;
    return true;
  } catch {
    return false;
  }
}

function inviteLink() {
  const code = (localRoomCode || roomState?.room_code || "").trim().toUpperCase();
  if (!code) return "";
  const inviteUrl = `${inviteOrigin()}/room/${encodeURIComponent(code)}`;
  return isValidInviteUrl(inviteUrl) ? inviteUrl : "";
}

function isAssociationInputFocused() {
  return document.activeElement?.id === "associationInput";
}

function currentTurnPlayerId() {
  return roomState?.discussion?.current_player_id || roomState?.overtime?.current_player_id || "";
}

function updateAssociationComposerState() {
  const input = document.querySelector("#associationInput");
  const button = document.querySelector("#sendAssociationButton");
  if (!input || !button) return;
  const me = roomState.players.find((player) => player.id === roomState.viewer_id);
  const isMyTurn = Boolean(me && me.id === currentTurnPlayerId());
  const showingSent = Date.now() < associationSentFeedbackUntil;
  if (input.value !== associationDraft && !isAssociationInputFocused()) {
    input.value = associationDraft;
  }
  if (showingSent) {
    button.textContent = "Poslano";
    button.disabled = true;
    button.dataset.canSend = "false";
    return;
  }
  button.textContent = "Pošalji";
  button.dataset.canSend = isMyTurn ? "true" : "false";
  button.disabled = !isMyTurn || input.value.trim().length === 0 || associationSendInFlight;
}

function hasDiscussionShell() {
  if (roomState.state === "discussion") {
    return Boolean(document.querySelector(".discussion-card #discussionMonitorPanel"));
  }
  if (roomState.state === "overtime") {
    return Boolean(document.querySelector(".overtime-card #discussionMonitorPanel"));
  }
  return false;
}

function discussionMonitorContext() {
  const isHost = roomState.viewer_id === roomState.host_id;
  const data = roomState.state === "overtime" ? roomState.overtime : roomState.discussion;
  if (
    pendingNextPlayerTurnId
    && pendingNextPlayerStartedAt
    && Date.now() - pendingNextPlayerStartedAt > 5000
  ) {
    clearPendingNextPlayer();
  }
  const me = roomState.players.find((player) => player.id === roomState.viewer_id);
  const canAdvanceTurn = Boolean(isHost || (me && data && me.id === data.current_player_id));
  const isCurrentChatPlayer = Boolean(
    me && data && me.id === data.current_player_id && me.play_mode === "chat",
  );
  const showNextButton = canAdvanceTurn && !isCurrentChatPlayer;
  const isNextPending = Boolean(data?.current_player_id && pendingNextPlayerTurnId === data.current_player_id);
  return {
    isHost,
    data,
    me,
    canAdvanceTurn,
    showNextButton,
    isNextPending,
    nextLockLeft: nextPlayerLockSecondsLeft(),
  };
}

function syncDiscussionTimerWarning(remainingSeconds) {
  const timerBox = document.querySelector("#discussionTimerBox");
  const timerValue = document.querySelector("#discussionTimerValue");
  const warn = Number(remainingSeconds) <= 15;
  const data = roomState?.state === "overtime" ? roomState.overtime : roomState?.discussion;
  const votingReady = Boolean(data?.voting_unlocked);
  timerBox?.classList.toggle("timer-warning", warn);
  timerBox?.classList.toggle("timer-voting-ready", votingReady);
  timerValue?.classList.toggle("timer-warning", warn);
  timerValue?.classList.toggle("timer-voting-ready", votingReady);
}

function renderHostVotingButtonHtml(voteLocked) {
  return `<button id="openFinalVotingButton" class="discussion-host-vote-button" type="button" ${voteLocked ? "disabled" : ""} title="${voteLocked ? "Glasanje još nije otključano" : "Otvori finalno glasanje"}">Otvori glasanje</button>`;
}

function nextPlayerButtonLabel(nextLockLeft, isPending = false) {
  if (isPending) return "Sljedeći...";
  return nextLockLeft > 0 ? `Sljedeći (${nextLockLeft})` : "Sljedeći igrač";
}

function nextPlayerButtonTitle(nextLockLeft, isPending = false) {
  if (isPending) return "Prebacivanje igrača je u toku";
  return nextLockLeft > 0 ? `Dostupno za ${nextLockLeft}s` : "Prebaci na sljedećeg igrača";
}

function renderNextPlayerButtonHtml(nextLockLeft, isPending = false) {
  const disabled = nextLockLeft > 0 || isPending;
  return `<button id="nextPlayerButton" class="discussion-next-button" type="button" ${disabled ? "disabled" : ""} title="${nextPlayerButtonTitle(nextLockLeft, isPending)}">${nextPlayerButtonLabel(nextLockLeft, isPending)}</button>`;
}

function syncDiscussionMonitorActions() {
  const ctx = discussionMonitorContext();
  if (!ctx.data) return;

  syncDiscussionTimerWarning(ctx.data.remaining_seconds);

  const openButton = document.querySelector("#openFinalVotingButton");
  if (openButton && ctx.isHost) {
    openButton.disabled = !ctx.data.voting_unlocked;
  }

  const nextSlot = document.querySelector("#discussionNextAction");
  if (!nextSlot) return;

  if (!ctx.showNextButton) {
    nextSlot.classList.add("hidden");
    nextSlot.innerHTML = "";
    return;
  }

  nextSlot.classList.remove("hidden");
  let nextButton = nextSlot.querySelector("#nextPlayerButton");
  if (!nextButton) {
    nextSlot.innerHTML = renderNextPlayerButtonHtml(ctx.nextLockLeft, ctx.isNextPending);
    bindDiscussionActions(ctx.canAdvanceTurn);
    return;
  }

  nextButton.disabled = ctx.nextLockLeft > 0 || ctx.isNextPending;
  nextButton.textContent = nextPlayerButtonLabel(ctx.nextLockLeft, ctx.isNextPending);
  nextButton.title = nextPlayerButtonTitle(ctx.nextLockLeft, ctx.isNextPending);
}

function updateDiscussionShellInPlace() {
  const timerValue = document.querySelector("#discussionTimerValue");
  const currentName = document.querySelector("#currentPlayerName");
  const data = roomState.state === "overtime" ? roomState.overtime : roomState.discussion;
  if (!data || !timerValue) return false;

  const currentPlayer = roomState.players.find((player) => player.id === data.current_player_id);
  timerValue.textContent = formatSeconds(data.remaining_seconds);
  if (currentName) currentName.textContent = playerNameText(currentPlayer);
  syncDiscussionMonitorActions();
  updateAssociationComposerState();
  syncAssociationOverlayDock(roomState.association_banners);
  syncActiveTargetReactions();
  syncReactionButtonsEnabled();
  return true;
}

function associationBannerStackKey(banners) {
  return (banners || []).map((banner) => `${banner.id}:${banner.expires_at}`).join("|");
}

function associationOverlayCardMarkup(banner) {
  return `
    <p class="association-overlay-name">${escapeHtml(banner.player_name || "Nepoznato")}</p>
    <p class="association-overlay-word">${escapeHtml(banner.text)}</p>
  `;
}

function createAssociationOverlayCard(banner, { animate = false } = {}) {
  const element = document.createElement("div");
  element.className = animate ? "association-overlay-card association-overlay-enter" : "association-overlay-card";
  element.dataset.bannerId = banner.id;
  element.dataset.expiresAt = String(banner.expires_at);
  element.innerHTML = associationOverlayCardMarkup(banner);
  if (animate) {
    element.addEventListener(
      "animationend",
      () => {
        element.classList.remove("association-overlay-enter");
      },
      { once: true },
    );
  }
  return element;
}

function updateAssociationOverlayCard(element, banner) {
  element.dataset.expiresAt = String(banner.expires_at);
  const nameEl = element.querySelector(".association-overlay-name");
  const wordEl = element.querySelector(".association-overlay-word");
  const nameText = banner.player_name || "Nepoznato";
  const wordText = banner.text || "";
  if (nameEl && nameEl.textContent !== nameText) nameEl.textContent = nameText;
  if (wordEl && wordEl.textContent !== wordText) wordEl.textContent = wordText;
}

function syncAssociationOverlayDock(banners) {
  const dock = associationOverlayDock;
  if (!dock) return;

  if (!roomState || !["discussion", "overtime"].includes(roomState.state)) {
    dock.classList.add("hidden");
    dock.replaceChildren();
    lastAssociationBannerStackKey = "";
    syncActiveTargetReactions();
    return;
  }

  const bannerList = banners || [];
  if (!bannerList.length) {
    dock.classList.add("hidden");
    dock.replaceChildren();
    lastAssociationBannerStackKey = "";
    syncActiveTargetReactions();
    return;
  }

  dock.classList.remove("hidden");
  const idsKey = associationBannerStackKey(bannerList);
  if (idsKey === lastAssociationBannerStackKey && dock.querySelector(".association-overlay-slot")) {
    syncActiveTargetReactions();
    return;
  }

  let leftSlot = dock.querySelector(".association-overlay-left");
  let rightSlot = dock.querySelector(".association-overlay-right");
  if (!leftSlot || !rightSlot) {
    dock.replaceChildren();
    leftSlot = document.createElement("div");
    leftSlot.className = "association-overlay-slot association-overlay-left";
    rightSlot = document.createElement("div");
    rightSlot.className = "association-overlay-slot association-overlay-right";
    dock.append(leftSlot, rightSlot);
  }

  const existingById = new Map();
  dock.querySelectorAll(".association-overlay-card").forEach((element) => {
    existingById.set(element.dataset.bannerId, element);
  });

  const nextIds = new Set(bannerList.map((banner) => banner.id));
  existingById.forEach((element, id) => {
    if (!nextIds.has(id)) {
      element.remove();
    }
  });

  bannerList.forEach((banner, index) => {
    const slot = index % 2 === 0 ? leftSlot : rightSlot;
    const slotIndex = Math.floor(index / 2);
    let element = dock.querySelector(`[data-banner-id="${banner.id}"]`);
    const isNew = !element;
    if (isNew) {
      element = createAssociationOverlayCard(banner, { animate: true });
    } else {
      updateAssociationOverlayCard(element, banner);
    }

    if (element.parentElement !== slot || slot.children[slotIndex] !== element) {
      slot.insertBefore(element, slot.children[slotIndex] || null);
    }
  });

  leftSlot.querySelectorAll(".association-overlay-card").forEach((element) => {
    if (!nextIds.has(element.dataset.bannerId)) element.remove();
  });
  rightSlot.querySelectorAll(".association-overlay-card").forEach((element) => {
    if (!nextIds.has(element.dataset.bannerId)) element.remove();
  });

  lastAssociationBannerStackKey = idsKey;
  syncActiveTargetReactions();
}

function activeTargetReactionKey(reaction) {
  if (!reaction) return "";
  if (reaction.identity) return String(reaction.identity);
  return `${reaction.target_type}:${reaction.target_id}:${reaction.sender_player_id}:${reaction.emoji}:${reaction.created_at}:${reaction.repulse_at || ""}`;
}

function syncReactionTargetCluster(container, reactions) {
  if (!container) return;

  const reactionList = reactions || [];
  let cluster = container.querySelector(".reaction-target-cluster");
  if (!reactionList.length) {
    cluster?.remove();
    container.querySelectorAll(":scope > .reaction-target-pop").forEach((element) => element.remove());
    return;
  }

  if (!cluster) {
    cluster = document.createElement("span");
    cluster.className = "reaction-target-cluster";
    cluster.setAttribute("aria-label", "Reakcije na aktivni cilj");
    container.appendChild(cluster);
  }

  const desiredKeys = reactionList.map((reaction) => activeTargetReactionKey(reaction));
  const desiredKeySet = new Set(desiredKeys);
  cluster.querySelectorAll(".reaction-target-pop").forEach((element) => {
    if (!desiredKeySet.has(element.dataset.reactionKey)) {
      element.remove();
    }
  });

  reactionList.forEach((reaction, index) => {
    const key = activeTargetReactionKey(reaction);
    let bubble = cluster.querySelector(`.reaction-target-pop[data-reaction-key="${CSS.escape(key)}"]`);
    const repulseKey = String(reaction.repulse_at || "");
    if (bubble && bubble.dataset.reactionKey === key && bubble.dataset.repulseAt === repulseKey) {
      return;
    }

    if (!bubble) {
      bubble = document.createElement("span");
      bubble.className = "reaction-target-pop";
      cluster.appendChild(bubble);
    }

    bubble.dataset.reactionKey = key;
    bubble.dataset.repulseAt = repulseKey;
    bubble.textContent = reaction.emoji;

    const referenceNode = cluster.children[index] || null;
    if (cluster.children[index] !== bubble) {
      cluster.insertBefore(bubble, referenceNode);
    }

    bubble.classList.remove("reaction-target-repulse");
    void bubble.offsetWidth;
    bubble.classList.add("reaction-target-repulse");
  });
}

function syncActiveTargetReactions() {
  const reactions = roomState?.active_target_reactions?.length
    ? roomState.active_target_reactions
    : roomState?.active_target_reaction
      ? [roomState.active_target_reaction]
      : [];
  const grouped = new Map();

  for (const reaction of reactions) {
    const groupKey = `${reaction.target_type}:${reaction.target_id}`;
    if (!grouped.has(groupKey)) grouped.set(groupKey, []);
    grouped.get(groupKey).push(reaction);
  }

  for (const list of grouped.values()) {
    list.sort((left, right) => (left.created_at || 0) - (right.created_at || 0));
  }

  const liveHost = document.querySelector(".reaction-target-host");
  const liveKey = [...grouped.keys()].find((key) => key.startsWith("live_player:"));
  syncReactionTargetCluster(liveHost, liveKey ? grouped.get(liveKey) : []);

  document.querySelectorAll(".association-overlay-card").forEach((card) => {
    const groupKey = `chat_association:${card.dataset.bannerId}`;
    syncReactionTargetCluster(card, grouped.get(groupKey) || []);
  });

  const activeContainers = new Set();
  if (liveHost && liveKey) activeContainers.add(liveHost);
  document.querySelectorAll(".association-overlay-card").forEach((card) => {
    const groupKey = `chat_association:${card.dataset.bannerId}`;
    if (grouped.has(groupKey)) activeContainers.add(card);
  });

  document.querySelectorAll(".reaction-target-cluster").forEach((cluster) => {
    const container = cluster.parentElement;
    if (!activeContainers.has(container)) {
      cluster.remove();
    }
  });
}

function renderDiscussionMonitorPanel(currentPlayer, phaseLabel, remainingSeconds, ctx) {
  const timerWarning = remainingSeconds <= 15 ? " timer-warning" : "";
  const votingReady = ctx.data?.voting_unlocked ? " timer-voting-ready" : "";
  const phaseText = phaseLabel ? `<span>${escapeHtml(phaseLabel)}</span>` : "";
  const hostVoting = ctx.isHost
    ? renderHostVotingButtonHtml(!ctx.data.voting_unlocked)
    : "";
  const nextAction = ctx.showNextButton
    ? `<div id="discussionNextAction" class="discussion-next-action">${renderNextPlayerButtonHtml(ctx.nextLockLeft, ctx.isNextPending)}</div>`
    : `<div id="discussionNextAction" class="discussion-next-action hidden"></div>`;

  return `
    <div id="discussionMonitorPanel" class="discussion-monitor-panel">
      <div id="discussionMonitorHeader" class="discussion-monitor-top-row">
        <div class="current-player-card compact-current-player reaction-target-host">
          <p class="eyebrow">Trenutni igrač</p>
          <p id="currentPlayerName" class="current-player-name">${escapeHtml(playerNameText(currentPlayer))}</p>
        </div>
        <div class="discussion-timer-column">
          <div id="discussionTimerBox" class="timer-box compact-timer compact-timer-inline${timerWarning}${votingReady}">
            ${phaseText}
            <strong id="discussionTimerValue" class="${`${timerWarning}${votingReady}`.trim()}">${formatSeconds(remainingSeconds)}</strong>
          </div>
          ${hostVoting}
        </div>
      </div>
      ${nextAction}
    </div>
  `;
}

function render() {
  if (!roomState) {
    setCinematicRevealActive(false);
    return;
  }
  setCinematicRevealActive(isCinematicRevealActive());
  roomCodeDisplay.textContent = roomState.room_code;
  roundDisplay.textContent = `Runda ${roomState.round_number || 1}`;
  const spectatorCount = roomState.players.filter((player) => player.is_spectator).length;
  const activePlayerCount = Math.max(0, Number(roomState.player_count || 0) - spectatorCount);
  playerCountBadge.textContent = spectatorCount > 0
    ? `Igrači: ${activePlayerCount}/${roomState.max_players} · Posmatrači: ${spectatorCount}`
    : `Igrači: ${activePlayerCount}/${roomState.max_players}`;
  resetRoomButton.classList.add("hidden");
  renderModeToggle();
  applyRoomPanelCollapse();
  renderHostPanel();
  renderPlayers();

  if (!["discussion", "overtime"].includes(roomState.state)) {
    clearPendingNextPlayer();
    syncAssociationOverlayDock([]);
  }

  if (roomState.state === "lobby") {
    renderLobby();
    return;
  }

  if (roomState.state === "reveal") {
    renderReveal();
    return;
  }

  if (roomState.state === "discussion") {
    if (hasDiscussionShell() && updateDiscussionShellInPlace()) return;
    renderDiscussion();
    return;
  }

  if (roomState.state === "ready_for_final_voting") {
    renderReadyForFinalVoting();
    return;
  }

  if (roomState.state === "final_voting") {
    renderFinalVoting();
    return;
  }

  if (roomState.state === "overtime") {
    if (hasDiscussionShell() && updateDiscussionShellInPlace()) return;
    renderOvertime();
    return;
  }

  if (roomState.state === "overtime_voting") {
    renderFinalVoting();
    return;
  }

  if (roomState.state === "voting_complete") {
    renderVotingComplete();
    return;
  }

  if (roomState.state === "results") {
    renderResults();
  }
}

function renderHostPanel() {
  const isHost = roomState.viewer_id === roomState.host_id;
  hostPanel.classList.toggle("hidden", !isHost);
  if (!isHost) {
    hostPanelActions.innerHTML = "";
    return;
  }

  const roundHasStarted = roomState.state !== "lobby";
  const actions = roundHasStarted ? [`<button id="hostResetRoomButton" class="small replay">Resetuj sobu</button>`] : [];
  if (roomState.state === "reveal" || (roomState.state === "discussion" && roomState.change_word_available)) {
    const secondsLeft = roomState.state === "discussion" ? Number(roomState.change_word_seconds_left || 0) : 0;
    const helper = roomState.state === "discussion" && secondsLeft > 0
      ? `<p class="helper-text">Dostupno još ${secondsLeft}s</p>`
      : "";
    actions.unshift(`
      <div class="host-helper">
        <button id="hostChangeWordButton" class="small secondary">Promijeni riječ</button>
        ${helper}
      </div>
    `);
  }
  if (roomState.state === "discussion" && roomState.discussion) {
    actions.unshift(`<button id="hostOpenVotingButton" class="small" ${roomState.discussion.voting_unlocked ? "" : "disabled"}>Otvori glasanje</button>`);
  }
  if (roomState.state === "overtime" && roomState.overtime?.voting_unlocked) {
    actions.unshift(`<button id="hostOpenVotingButton" class="small">Otvori glasanje</button>`);
  }
  if (roomState.state === "ready_for_final_voting") {
    actions.unshift(`<button id="hostOpenVotingButton" class="small">Otvori glasanje</button>`);
  }
  const transferTargets = roomState.players.filter((player) => player.id !== roomState.viewer_id);
  if (transferTargets.length > 0) {
    actions.push(`
      <select id="transferHostSelect" class="small-select" aria-label="Prenesi hosta">
        <option value="">Prenesi hosta</option>
        ${transferTargets.map((player) => `<option value="${escapeHtml(player.id)}">${escapeHtml(playerNameText(player))}</option>`).join("")}
      </select>
    `);
  }

  hostPanelActions.innerHTML = actions.join("");
  document.querySelector("#hostResetRoomButton")?.addEventListener("click", promptRestartRoom);
  document.querySelector("#hostChangeWordButton")?.addEventListener("click", changeWord);
  document.querySelector("#hostOpenVotingButton")?.addEventListener("click", openFinalVoting);
  document.querySelector("#transferHostSelect")?.addEventListener("change", (event) => {
    const targetId = event.target.value;
    const target = roomState.players.find((player) => player.id === targetId);
    if (!target) return;
    showConfirmAction(`Da li zelis prenijeti hosta na ${playerNameText(target)}?`, () => transferHost(targetId), false);
    event.target.value = "";
  });
}

function renderLobby() {
  const isHost = roomState.viewer_id === roomState.host_id;
  const playableCount = Number(roomState.active_playable_player_count || roomState.player_count || 0);
  const canStart = isHost && playableCount >= roomState.min_players;
  const categories = roomState.categories || ["Sve kategorije"];
  const durationOptions = roomState.allowed_discussion_seconds || [120, 180, 300];
  const allowedVaralicaCounts = roomState.allowed_varalica_counts || [1];
  selectedCategory = roomState.selected_category || selectedCategory;
  selectedDiscussionSeconds = roomState.discussion_duration_seconds || selectedDiscussionSeconds;
  if (allowedVaralicaCounts.includes(roomState.selected_varalica_count)) {
    selectedVaralicaCount = roomState.selected_varalica_count;
    localStorage.setItem("varalica_count", String(selectedVaralicaCount));
  }
  if (!allowedVaralicaCounts.includes(selectedVaralicaCount)) {
    selectedVaralicaCount = 1;
    localStorage.setItem("varalica_count", "1");
  }
  if (!categories.includes(selectedCategory)) {
    selectedCategory = "Sve kategorije";
    localStorage.setItem("varalica_selected_category", selectedCategory);
  }
  if (!durationOptions.includes(selectedDiscussionSeconds)) {
    selectedDiscussionSeconds = roomState.discussion_duration_seconds || 120;
  }
  phaseContent.innerHTML = `
    <div class="phase-card">
      <h2>Lobby</h2>
      <p class="helper-text">Podijeli kod sobe ili link. Runda moze poceti kad su tu najmanje 4 igraca.</p>
      ${
        isHost
          ? `<div class="category-control">
              <label for="categorySelect">Kategorija</label>
              <select id="categorySelect">
                ${categories
                  .map(
                    (category) => `<option value="${escapeHtml(category)}" ${category === selectedCategory ? "selected" : ""}>${escapeHtml(category)}</option>`,
                  )
                  .join("")}
              </select>
            </div>
            <div class="category-control">
              <label for="durationSelect">Vrijeme diskusije</label>
              <select id="durationSelect">
                ${durationOptions
                  .map(
                    (seconds) => `<option value="${seconds}" ${seconds === selectedDiscussionSeconds ? "selected" : ""}>${seconds / 60} min</option>`,
                  )
                  .join("")}
              </select>
            </div>
            <div class="category-control">
              <label for="varalicaCountSelect">Broj Varalica</label>
              <select id="varalicaCountSelect">
                <option value="1" ${selectedVaralicaCount === 1 ? "selected" : ""}>1 Varalica</option>
                <option value="2" ${selectedVaralicaCount === 2 ? "selected" : ""} ${allowedVaralicaCounts.includes(2) ? "" : "disabled"}>2 Varalice</option>
              </select>
              ${allowedVaralicaCounts.includes(2) ? "" : `<p class="helper-text">2 Varalice dostupne su od 7 igrača.</p>`}
            </div>
            <button id="startRoundButton" ${canStart ? "" : "disabled"}>
              ${canStart ? "Pokreni rundu" : "Potrebna su najmanje 4 igraca"}
            </button>`
          : `<p class="helper-text">Host pokrece rundu.</p>`
      }
    </div>
  `;
  const categorySelect = document.querySelector("#categorySelect");
  if (categorySelect) {
    categorySelect.addEventListener("change", () => {
      selectedCategory = categorySelect.value;
      localStorage.setItem("varalica_selected_category", selectedCategory);
    });
  }
  const durationSelect = document.querySelector("#durationSelect");
  if (durationSelect) {
    durationSelect.addEventListener("change", () => {
      selectedDiscussionSeconds = Number(durationSelect.value);
      localStorage.setItem("varalica_discussion_seconds", String(selectedDiscussionSeconds));
    });
  }
  const varalicaCountSelect = document.querySelector("#varalicaCountSelect");
  if (varalicaCountSelect) {
    varalicaCountSelect.addEventListener("change", () => {
      selectedVaralicaCount = Number(varalicaCountSelect.value) === 2 ? 2 : 1;
      localStorage.setItem("varalica_count", String(selectedVaralicaCount));
    });
  }
  const startButton = document.querySelector("#startRoundButton");
  if (startButton) startButton.addEventListener("click", startRound);
}

function revealStatusForPlayer(player) {
  if (player.confirmed) {
    return { label: "Spreman", className: "ready" };
  }
  if (player.viewed_secret) {
    return { label: "Pregleda", className: "viewing" };
  }
  return { label: "Nije vidio", className: "waiting" };
}

function syncRevealCardStateFromRoom() {
  if (roomState?.state !== "reveal") return;
  const me = roomState.players.find((player) => player.id === localPlayerId);
  if (me?.viewed_secret || me?.confirmed) {
    hasRevealedPrivateCard = true;
  }
}

function syncRevealStatusBadge(row, player) {
  const meta = row.querySelector(".player-meta");
  if (!meta) return;

  const shouldShow = roomState.state === "reveal" && player.is_active_round_player;
  const existing = meta.querySelector(".badge.reveal-status");
  if (!shouldShow) {
    existing?.remove();
    return;
  }

  const status = revealStatusForPlayer(player);
  const statusKey = `${status.className}:${status.label}`;
  if (existing && existing.dataset.revealStatusKey === statusKey) return;

  existing?.remove();
  meta.insertAdjacentHTML(
    "afterbegin",
    `<span class="badge reveal-status ${status.className}" data-reveal-status-key="${statusKey}">${status.label}</span>`,
  );
}

function clearRevealStatusBadges(row) {
  row.querySelectorAll(".player-meta .badge.reveal-status").forEach((badge) => badge.remove());
}

function renderReveal() {
  const privateInfo = roomState.private;
  const me = roomState.players.find((player) => player.id === roomState.viewer_id);
  syncRevealCardStateFromRoom();
  const alreadyConfirmed = Boolean(me?.confirmed);
  if (me?.viewed_secret) {
    hasRevealedPrivateCard = true;
  } else if (me && !me.confirmed) {
    hasRevealedPrivateCard = false;
  }

  if (roomState.all_confirmed) {
    phaseContent.innerHTML = `
      <div class="phase-card">
        <h2>Svi su spremni</h2>
        <p class="helper-text">Diskusija se pokrece automatski.</p>
      </div>
    `;
    return;
  }

  if (!privateInfo) {
    phaseContent.innerHTML = `
      <div class="phase-card">
        <h2>Otkrivanje</h2>
        ${
          roomState.viewer_is_spectator
            ? spectatorNoticeHtml()
            : `<p class="helper-text">Cekamo podatke za ovu rundu.</p>`
        }
      </div>
    `;
    return;
  }

  if (alreadyConfirmed) {
    phaseContent.innerHTML = `
      <div class="phase-card private-card-phase private-card-phase-locked">
        <h2>Tvoja tajna kartica</h2>
        <p class="helper-text">Kartica je potvrđena i zaključana.</p>
        <div class="private-card-closed-static" aria-hidden="true">
          <img class="private-card-closed-img" src="${escapeHtml(PRIVATE_CARD_CLOSED_URL)}" alt="" decoding="async" />
        </div>
        <button id="confirmSeenButton" class="private-card-confirm-button" type="button" disabled>Potvrđeno</button>
        <p class="helper-text">Diskusija ne moze poceti dok svi aktivni igraci ne potvrde.</p>
      </div>
    `;
    return;
  }

  if (!hasRevealedPrivateCard) {
    phaseContent.innerHTML = `
      <div class="phase-card private-card-phase private-card-phase-closed">
        <h2>Tvoja tajna kartica</h2>
        <p class="helper-text">Provjeri je na svom telefonu i ne pokazuj drugim igracima.</p>
        <button id="showWordButton" class="private-card-closed-button" type="button" aria-label="Dodirni kartu">
          <img class="private-card-closed-img" src="${escapeHtml(PRIVATE_CARD_CLOSED_URL)}" alt="" aria-hidden="true" decoding="async" />
        </button>
        <p class="private-card-tap-label">Dodirni kartu</p>
      </div>
    `;
    document.querySelector("#showWordButton").addEventListener("click", async () => {
      const result = await markSecretViewed();
      if (!result) return;
      hasRevealedPrivateCard = true;
      renderReveal();
    });
    return;
  }

  const isVaralica = privateInfo.role === "varalica";
  const openCardUrl = isVaralica ? PRIVATE_CARD_OPEN_VARALICA_URL : PRIVATE_CARD_OPEN_NORMAL_URL;
  const secretHtml = isVaralica
    ? `<div class="private-card-secret private-card-secret-varalica">
         <p class="private-card-secret-title">Ti si Varalica</p>
         <p class="private-card-secret-label">Smjernica</p>
         <p class="private-card-secret-hint">${escapeHtml(privateInfo.hint || "Pokušaj da se uklopiš.")}</p>
       </div>`
    : `<div class="private-card-secret private-card-secret-word">
         <p class="private-card-secret-kicker">Tvoja riječ</p>
         <p class="private-card-secret-title">${escapeHtml(privateInfo.word.hr)}</p>
       </div>`;

  phaseContent.innerHTML = `
    <div class="phase-card private-card-phase private-card-phase-open">
      <h2>Tvoja tajna kartica</h2>
      <div class="private-card-open-stage ${isVaralica ? "is-varalica" : "is-normal"}">
        <img class="private-card-open-img" src="${escapeHtml(openCardUrl)}" alt="" aria-hidden="true" decoding="async" />
        <div class="private-card-text-panel">
          ${secretHtml}
        </div>
      </div>
      <button id="confirmSeenButton" class="private-card-confirm-button" type="button">Video sam kartu</button>
      <p class="helper-text">Diskusija ne moze poceti dok svi aktivni igraci ne potvrde.</p>
    </div>
  `;

  document.querySelector("#confirmSeenButton")?.addEventListener("click", confirmSeen);
}

function bindDiscussionActions(canAdvanceTurn) {
  const nextButton = document.querySelector("#nextPlayerButton");
  if (nextButton && canAdvanceTurn && nextButton.dataset.bound !== "true") {
    nextButton.dataset.bound = "true";
    nextButton.addEventListener("click", nextPlayer);
  }
  const openButton = document.querySelector("#openFinalVotingButton");
  if (openButton && openButton.dataset.bound !== "true") {
    openButton.dataset.bound = "true";
    openButton.addEventListener("click", openFinalVoting);
  }
}

function renderDiscussion() {
  const ctx = discussionMonitorContext();
  const discussion = roomState.discussion;
  const currentPlayer = roomState.players.find((player) => player.id === discussion.current_player_id);

  phaseContent.innerHTML = `
    <div class="phase-card discussion-card">
      ${roomState.viewer_is_spectator ? spectatorNoticeHtml() : ""}
      <div class="discussion-monitor-layout">
        ${renderReactionColumn("left", REACTION_EMOJIS_LEFT)}
        <div class="discussion-monitor-body">
          ${renderDiscussionMonitorPanel(currentPlayer, "Diskusija", discussion.remaining_seconds, ctx)}
          ${renderAssociationComposer(discussion.current_player_id)}
        </div>
        ${renderReactionColumn("right", REACTION_EMOJIS_RIGHT)}
      </div>
    </div>
  `;

  bindDiscussionActions(ctx.canAdvanceTurn);
  bindAssociationComposer();
  lastAssociationBannerStackKey = associationBannerStackKey(roomState.association_banners);
  syncAssociationOverlayDock(roomState.association_banners);
  syncActiveTargetReactions();
  syncReactionButtonsEnabled();
}

function renderReadyForFinalVoting() {
  const isHost = roomState.viewer_id === roomState.host_id;
  phaseContent.innerHTML = `
    <div class="phase-card">
      <h2>Svi igrači su spremni za glasanje.</h2>
      <p class="helper-text">Host sada moze otvoriti finalno glasanje.</p>
      ${
        isHost
          ? `<button id="openFinalVotingButton">Otvori glasanje</button>`
          : ""
      }
    </div>
  `;

  const openButton = document.querySelector("#openFinalVotingButton");
  if (openButton) openButton.addEventListener("click", openFinalVoting);
}

function renderOvertime() {
  const ctx = discussionMonitorContext();
  const overtime = roomState.overtime;
  const currentPlayer = roomState.players.find((player) => player.id === overtime.current_player_id);

  phaseContent.innerHTML = `
    <div class="phase-card overtime-card">
      <p class="overtime-compact-title">PRODUŽETAK — Glasanje je nerešeno</p>
      ${roomState.viewer_is_spectator ? spectatorNoticeHtml() : ""}
      <div class="discussion-monitor-layout">
        ${renderReactionColumn("left", REACTION_EMOJIS_LEFT)}
        <div class="discussion-monitor-body">
          ${renderDiscussionMonitorPanel(currentPlayer, "", overtime.remaining_seconds, ctx)}
          ${renderAssociationComposer(overtime.current_player_id)}
        </div>
        ${renderReactionColumn("right", REACTION_EMOJIS_RIGHT)}
      </div>
    </div>
  `;

  bindDiscussionActions(ctx.canAdvanceTurn);
  bindAssociationComposer();
  lastAssociationBannerStackKey = associationBannerStackKey(roomState.association_banners);
  syncAssociationOverlayDock(roomState.association_banners);
  syncActiveTargetReactions();
  syncReactionButtonsEnabled();
}

function renderAssociationComposer(currentPlayerId) {
  const me = roomState.players.find((player) => player.id === roomState.viewer_id);
  if (me?.play_mode !== "chat") return "";
  const isMyTurn = me.id === currentPlayerId;
  const draft = escapeHtml(associationDraft);
  return `
    <div class="association-composer">
      <label for="associationInput">Tvoja asocijacija</label>
      <div class="association-input-row">
        <input id="associationInput" maxlength="80" autocomplete="off" placeholder="npr. nesto za kuhinju" value="${draft}" />
        <button id="sendAssociationButton" class="small" data-can-send="${isMyTurn ? "true" : "false"}" ${isMyTurn ? "" : "disabled"}>Pošalji</button>
      </div>
    </div>
  `;
}

function renderReactionColumn(side, emojis) {
  if (!emojis.length) return "";
  const enabled = canSendReactions();
  const buttons = emojis
    .map(
      (emoji) =>
        `<button class="reaction-button" type="button" data-reaction-emoji="${escapeHtml(emoji)}" aria-label="Reakcija ${escapeHtml(emoji)}" ${enabled ? "" : "disabled"}>${escapeHtml(emoji)}</button>`,
    )
    .join("");
  return `<div class="reaction-row reaction-row-${side}" aria-label="Reakcije">${buttons}</div>`;
}

function syncReactionButtonsEnabled() {
  const enabled = canSendReactions();
  document.querySelectorAll("[data-reaction-emoji]").forEach((button) => {
    button.disabled = !enabled;
  });
}

function bindAssociationComposer() {
  const input = document.querySelector("#associationInput");
  const button = document.querySelector("#sendAssociationButton");
  if (!input || !button) return;
  const updateButton = () => {
    associationDraft = input.value.slice(0, 80);
    sessionStorage.setItem("varalica_association_draft", associationDraft);
    updateAssociationComposerState();
  };
  input.addEventListener("input", updateButton);
  button.addEventListener("click", sendAssociation);
  updateAssociationComposerState();
}

function renderVotingChecklist(players) {
  return `
    <div class="voting-checklist" aria-label="Status glasanja">
      ${players
        .map((player) => {
          const mark = player.has_voted ? "✓" : "";
          const stateClass = player.has_voted ? "voted" : "pending";
          const label = player.has_voted ? "Glasao/la" : "Još nije glasao/la";
          return `
            <div class="voting-check-item ${stateClass}">
              <span class="vote-check-box" aria-label="${label}">${mark}</span>
              <span class="inline-player">${playerNameHtml(player)}</span>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function spectatorNoticeHtml() {
  const message = roomState?.spectator_message || "Ušao si kao posmatrač. Igraš od sledeće runde.";
  return `
    <div class="spectator-notice">
      <strong>Posmatrač</strong>
      <span>${escapeHtml(message)}</span>
    </div>
  `;
}

function renderFinalVoting() {
  const me = roomState.players.find((player) => player.id === roomState.viewer_id);
  const isSpectator = Boolean(roomState.viewer_is_spectator || (me && !me.is_active_round_player));
  const hasVoted = Boolean(me?.has_voted);
  const activePlayers = roomState.players.filter((player) => player.is_active_round_player && player.id !== roomState.viewer_id);
  const activeRoundPlayers = roomState.players.filter((player) => player.is_active_round_player);
  const votedCount = activeRoundPlayers.filter((player) => player.has_voted).length;
  const isOvertimeVote = roomState.state === "overtime_voting";
  const requiredTargets = roomState.required_vote_targets || 1;

  if (isSpectator) {
    phaseContent.innerHTML = `
      <div class="phase-card voting-phase-card">
        <h2>${isOvertimeVote ? "Glasanje nakon produzetka" : "Finalno glasanje"}</h2>
        ${spectatorNoticeHtml()}
        <div class="vote-progress-private">
          <strong>${votedCount}/${activeRoundPlayers.length}</strong>
          <span>igrača glasalo</span>
        </div>
        ${renderVotingChecklist(activeRoundPlayers)}
      </div>
    `;
    return;
  }

  phaseContent.innerHTML = `
    <div class="phase-card voting-phase-card">
      <h2>${isOvertimeVote ? "Glasanje nakon produzetka" : "Finalno glasanje"}</h2>
      <p class="helper-text">
        ${requiredTargets === 2 ? "Odaberi 2 igrača za koje misliš da su Varalice." : "Odaberi igrača za kojeg misliš da je Varalica."}
        Glasovi se ne otkrivaju dok svi ne glasaju.
      </p>
      <p class="helper-text">Ne mozes glasati za sebe.</p>
      <div class="vote-progress-private">
        <strong>${votedCount}/${activeRoundPlayers.length}</strong>
        <span>igrača glasalo</span>
      </div>
      ${renderVotingChecklist(activeRoundPlayers)}
      ${requiredTargets === 2 && !hasVoted ? `<p id="voteSelectionCounter" class="helper-text">Izabrano: 0/2</p>` : ""}
      <div class="vote-list">
        ${activePlayers
          .map(
            (player) => `
              <div class="vote-option ${requiredTargets === 2 ? "selectable-vote-option" : ""}" data-select-target-id="${escapeHtml(player.id)}">
                <div>
                  <strong class="inline-player">${playerNameHtml(player)}</strong>
                  ${player.id === roomState.viewer_id ? `<span class="helper-text">Ti</span>` : ""}
                </div>
                <button class="small vote-button" data-target-id="${escapeHtml(player.id)}" ${hasVoted ? "disabled" : ""}>
                  ${requiredTargets === 2 ? "Odaberi" : "Glasaj"}
                </button>
              </div>
            `,
          )
          .join("")}
      </div>
      ${requiredTargets === 2 && !hasVoted ? `<button id="submitMultiVoteButton" disabled>Potvrdi izbor</button>` : ""}
      <p class="helper-text">
        ${hasVoted ? "Tvoj glas je zaprimljen. Cekamo ostale igrace." : "Mozes glasati samo jednom."}
      </p>
    </div>
  `;

  if (!hasVoted && requiredTargets === 1) {
    document.querySelectorAll(".vote-button").forEach((button) => {
      button.addEventListener("click", () => submitFinalVote(button.dataset.targetId));
    });
  }
  if (!hasVoted && requiredTargets === 2) {
    const selectedTargets = new Set();
    const counter = document.querySelector("#voteSelectionCounter");
    const submitButton = document.querySelector("#submitMultiVoteButton");
    const updateSelection = () => {
      document.querySelectorAll("[data-select-target-id]").forEach((row) => {
        const targetId = row.dataset.selectTargetId;
        const selected = selectedTargets.has(targetId);
        row.classList.toggle("selected", selected);
        const button = row.querySelector(".vote-button");
        if (button) button.textContent = selected ? "Izabrano" : "Odaberi";
      });
      if (counter) counter.textContent = `Izabrano: ${selectedTargets.size}/2`;
      if (submitButton) submitButton.disabled = selectedTargets.size !== 2;
    };
    document.querySelectorAll(".vote-button").forEach((button) => {
      button.addEventListener("click", () => {
        const targetId = button.dataset.targetId;
        if (selectedTargets.has(targetId)) {
          selectedTargets.delete(targetId);
        } else if (selectedTargets.size < 2) {
          selectedTargets.add(targetId);
        }
        updateSelection();
      });
    });
    submitButton?.addEventListener("click", () => submitFinalVote([...selectedTargets]));
    updateSelection();
  }
}

function renderVotingComplete() {
  const isHost = roomState.viewer_id === roomState.host_id;
  const voting = roomState.voting_complete;
  if (voting.is_tie) {
    if (voting.can_reveal) {
      phaseContent.innerHTML = `
        <div class="phase-card overtime-card">
          <h2>Glasanje je nerešeno.</h2>
          <p class="helper-text">Produžeci su završeni. Host može prikazati Varalicu.</p>
          ${isHost ? `<button id="revealResultsButton">Prikaži Varalicu</button>` : `<p class="helper-text">Čeka se da host prikaže Varalicu.</p>`}
        </div>
      `;
      const revealButton = document.querySelector("#revealResultsButton");
      if (revealButton) revealButton.addEventListener("click", revealResults);
      return;
    }
    phaseContent.innerHTML = `
      <div class="phase-card overtime-card">
        <h2>Glasanje je nerešeno.</h2>
        <p class="helper-text">Varalica se ne otkriva. Diskusija se produžava za 30 sekundi.</p>
      </div>
    `;
    return;
  }
  phaseContent.innerHTML = `
    <div class="phase-card">
      <h2>Glasanje je završeno</h2>
      <p class="helper-text">
        ${isHost ? "Prikaži Varalicu kada su svi spremni da vide rezultat." : "Čeka se da host prikaže Varalicu."}
      </p>
      ${
        voting.can_overtime
          ? `<div class="overtime-card">
              <h2>Glasanje je neriješeno.</h2>
              <p class="helper-text">Diskusija se produžava za 30 sekundi.</p>
              ${isHost ? `<button id="startOvertimeButton">Produži igru 30 sekundi</button>` : ""}
            </div>`
          : ""
      }
      ${isHost ? `<button id="revealResultsButton">Prikaži Varalicu</button>` : ""}
    </div>
  `;

  const overtimeButton = document.querySelector("#startOvertimeButton");
  if (overtimeButton) overtimeButton.addEventListener("click", startOvertime);

  const revealButton = document.querySelector("#revealResultsButton");
  if (revealButton) revealButton.addEventListener("click", revealResults);
}

function finalOutcomeTheme(results) {
  const wasCaught = results.was_varalica_caught === true;
  const isCurrentUserVaralica = isViewerVaralica(results);
  if (wasCaught && isCurrentUserVaralica) return "impostor-caught-red";
  if (wasCaught && !isCurrentUserVaralica) return "players-win-green";
  if (!wasCaught && isCurrentUserVaralica) return "impostor-win-green";
  return "players-lost-red";
}

function resultVaralice(results) {
  return Array.isArray(results.varalice) && results.varalice.length ? results.varalice : [results.varalica].filter(Boolean);
}

function isViewerVaralica(results) {
  return resultVaralice(results).some((player) => player.id === roomState.viewer_id);
}

function varaliceNameText(results) {
  return resultVaralice(results).map((player) => playerNameText(player)).join(", ");
}

function revealTheme(results, phase = "complete") {
  const countdownPhases = new Set(["overlay_intro", "countdown_5", "countdown_4", "countdown_3", "countdown_2", "countdown_1"]);
  if (countdownPhases.has(phase)) return "danger-red-for-all";
  return finalOutcomeTheme(results);
}

function revealStatusLabel(results) {
  if (results.was_varalica_caught === true) {
    return isViewerVaralica(results) ? "PROVALJENA" : "OTKRIVENA";
  }
  return "PREŽIVJELA";
}

function revealStatusClass(results) {
  if (results.was_varalica_caught === true) {
    return isViewerVaralica(results) ? "status-caught" : "status-exposed";
  }
  return "status-survived";
}

function revealOutcomeTitle(results) {
  if (results.was_varalica_caught === true) {
    return isViewerVaralica(results) ? "PROVALJENA" : "OTKRIVENA";
  }
  return "PREŽIVJELA";
}

function revealOutcomeSubtitle(results) {
  const isCurrentUserVaralica = isViewerVaralica(results);
  if (results.was_varalica_caught === true) {
    return isCurrentUserVaralica ? "Manipulacija nije uspjela." : "Igrači su pronašli Varalicu.";
  }
  return isCurrentUserVaralica ? "Varalica je preživjela." : "Igrači nisu uspjeli otkriti Varalicu.";
}

function impostorAvatarHtml() {
  return `
    <div class="impostor-avatar-asset">
      <img
        class="impostor-neon-ring-img"
        src="${escapeHtml(IMPOSTOR_REVEAL_RING_URL)}"
        alt=""
        aria-hidden="true"
        loading="eager"
        decoding="async"
      >
      <div
        class="impostor-reveal-avatar-fallback"
        aria-hidden="true"
      >
        <div class="impostor-hood">
          <div class="impostor-finger"></div>
        </div>
      </div>
    </div>
  `;
}

function renderVaralicaNamesHtml(results, { animate = false } = {}) {
  const names = resultVaralice(results);
  const animateClass = animate ? " impostor-name-reveal" : "";
  if (!names.length) {
    return `<h2 class="impostor-nickname${animateClass}">Nepoznato</h2>`;
  }
  if (names.length === 1) {
    const label = playerNameText(names[0]);
    return `<h2 class="impostor-nickname${animateClass}" title="${escapeHtml(label)}">${escapeHtml(label)}</h2>`;
  }
  return `
    <div class="impostor-nickname-stack">
      ${names.map((player) => {
        const label = playerNameText(player);
        return `<h2 class="impostor-nickname${animateClass}" title="${escapeHtml(label)}">${escapeHtml(label)}</h2>`;
      }).join("")}
    </div>
  `;
}

function isCountdownRevealPhase(phase) {
  return /^countdown_\d$/.test(phase) || phase === "overlay_intro";
}

function isRevealTransitionPhase(phase) {
  return isCountdownRevealPhase(phase) || phase === "flying_card" || phase === "fade_black";
}

function finalResultHeadline(results) {
  return results.was_varalica_caught === true ? "VARALICA JE UHVAĆENA" : "VARALICA JE PREŽIVJELA";
}

function patchImpostorRevealCountdown() {
  const stage = document.querySelector("#impostorRevealStage");
  if (!stage || stage.dataset.revealPhase !== revealSequence.phase) return false;
  const countdownEl = stage.querySelector(".impostor-countdown");
  if (countdownEl && revealSequence.countdown) {
    countdownEl.textContent = String(revealSequence.countdown);
  }
  return true;
}

function renderImpostorReveal(results) {
  const phase = revealSequence.phase;
  if (lastRenderedRevealPhase === phase && patchImpostorRevealCountdown()) {
    return;
  }
  lastRenderedRevealPhase = phase;

  const theme = revealTheme(results, phase);
  const isCountdown = isCountdownRevealPhase(phase);
  const showStatus = phase === "status_reveal" || phase === "name_reveal" || phase === "subtitle_reveal";
  const showPretitle = phase === "name_reveal" || phase === "subtitle_reveal";
  const showName = phase === "name_reveal" || phase === "subtitle_reveal";
  const showSubtitle = phase === "subtitle_reveal";
  const isImpact = phase === "countdown_1" || phase === "name_reveal";
  const statusLabel = revealStatusLabel(results);
  const statusClass = revealStatusClass(results);
  const subtitle = revealOutcomeSubtitle(results);

  phaseContent.innerHTML = `
    <div
      id="impostorRevealStage"
      class="impostor-reveal-stage ${escapeHtml(theme)} ${escapeHtml(phase)} ${isImpact ? "impact" : ""}"
      data-reveal-phase="${escapeHtml(phase)}"
    >
      <div class="impostor-reveal-vignette" aria-hidden="true"></div>
      <div class="impostor-reveal-card">
        <div class="impostor-avatar-column">
          <div class="impostor-avatar-wrap">
            ${impostorAvatarHtml()}
            <img
              class="impostor-scanlines-overlay"
              src="${escapeHtml(IMPOSTOR_REVEAL_SCANLINES_URL)}"
              alt=""
              aria-hidden="true"
            >
            <div class="impostor-glitch-lines" aria-hidden="true"></div>
          </div>
          ${isCountdown && revealSequence.countdown ? `<div class="impostor-countdown">${revealSequence.countdown}</div>` : ""}
        </div>
        <div class="impostor-reveal-copy impostor-reveal-copy-front">
          ${showStatus ? `<p class="impostor-status-label ${escapeHtml(statusClass)}">${escapeHtml(statusLabel)}</p>` : ""}
          ${showPretitle ? `<p class="impostor-pretitle impostor-pretitle-game">VARALICA JE...</p>` : ""}
          ${showName ? `<div class="impostor-name-reveal-wrap">${showName && phase === "name_reveal" ? '<span class="impostor-name-smoke" aria-hidden="true"></span>' : ""}${renderVaralicaNamesHtml(results, { animate: phase === "name_reveal" })}</div>` : ""}
          ${showSubtitle ? `<p class="impostor-subtitle impostor-subtitle-reveal">${escapeHtml(subtitle)}</p>` : ""}
        </div>
      </div>
    </div>
  `;
}

function renderRevealCountdownTransition() {
  const phase = revealSequence.phase;
  const isCountdown = isCountdownRevealPhase(phase);
  const isImpact = phase === "countdown_1" || phase === "flying_card";
  const showFlyingCard = phase === "flying_card";
  const isBlackout = phase === "fade_black";

  phaseContent.innerHTML = `
    <div
      id="revealCountdownStage"
      class="reveal-countdown-overlay ${escapeHtml(phase)} ${isImpact ? "is-impact" : ""} ${isBlackout ? "is-blackout" : ""}"
      data-reveal-phase="${escapeHtml(phase)}"
      aria-live="polite"
    >
      <div class="reveal-countdown-backdrop" aria-hidden="true"></div>
      <div class="reveal-countdown-fade-black" aria-hidden="true"></div>
      <div class="reveal-countdown-scene">
        <img
          class="reveal-countdown-base"
          src="${escapeHtml(REVEAL_COUNTDOWN_BASE_URL)}"
          alt=""
          aria-hidden="true"
          loading="eager"
          decoding="async"
          onerror="this.closest('.reveal-countdown-overlay').classList.add('image-failed')"
        >
        <div class="reveal-countdown-light" aria-hidden="true"></div>
        ${
          isCountdown && revealSequence.countdown
            ? `<div class="reveal-countdown-number" aria-label="${revealSequence.countdown}">${revealSequence.countdown}</div>`
            : ""
        }
        ${
          showFlyingCard
            ? `<img class="reveal-flying-card" src="${escapeHtml(REVEAL_FLYING_CARD_URL)}" alt="" aria-hidden="true" decoding="async">`
            : ""
        }
      </div>
    </div>
  `;
}

function renderResultRevealHero(results, displayMode = "fullscreen") {
  const theme = finalOutcomeTheme(results);
  const wasCaught = results.was_varalica_caught === true;
  const sceneUrl = wasCaught ? RESULT_CAUGHT_SCENE_URL : RESULT_SURVIVED_SCENE_URL;
  const sceneClass = wasCaught ? "final-result-scene-caught" : "final-result-scene-survived";
  const overlayClass = wasCaught ? "result-overlay-red" : "result-overlay-green";
  const headline = finalResultHeadline(results);
  const isCompact = displayMode === "compact";

  if (isCompact) {
    return `
      <div class="final-result-overlay final-result-compact ${escapeHtml(theme)} ${escapeHtml(sceneClass)} ${escapeHtml(overlayClass)}">
        <div class="final-result-mini-scene">
          <img
            class="final-result-mini-scene-img"
            src="${escapeHtml(sceneUrl)}"
            alt=""
            aria-hidden="true"
            decoding="async"
          >
        </div>
        <p class="final-result-varalica-name">${escapeHtml(varaliceNameText(results))}</p>
      </div>
    `;
  }

  return `
    <div class="final-result-overlay final-result-fullscreen ${escapeHtml(theme)} ${escapeHtml(sceneClass)} ${escapeHtml(overlayClass)}">
      <div class="final-result-fullscreen-scene">
        <img
          class="final-result-scene-img"
          src="${escapeHtml(sceneUrl)}"
          alt=""
          aria-hidden="true"
          decoding="async"
        >
        <div class="final-result-color-wash" aria-hidden="true"></div>
        <div class="final-result-smoke" aria-hidden="true"></div>
        <div class="final-result-status-block">
          <h2 class="final-result-title">${escapeHtml(headline)}</h2>
        </div>
      </div>
    </div>
  `;
}

function isCinematicRevealActive() {
  if (roomState?.state !== "results") return false;
  if (revealSequence.active && isRevealTransitionPhase(revealSequence.phase)) return true;
  return finalResultSceneState.roundKey === finalResultRoundKey() && finalResultSceneState.mode === "fullscreen";
}

function setCinematicRevealActive(active) {
  roomView.classList.toggle("cinematic-reveal-active", active);
  document.body.classList.toggle("cinematic-reveal-active", active);
}

function renderResults() {
  const isHost = roomState.viewer_id === roomState.host_id;
  const results = roomState.results;
  if (revealSequence.active && isRevealTransitionPhase(revealSequence.phase)) {
    renderRevealCountdownTransition();
    setCinematicRevealActive(true);
    return;
  }
  const finalResultDisplayMode = ensureFinalResultSceneTransition();
  setCinematicRevealActive(finalResultDisplayMode === "fullscreen");
  const voteRows = results.vote_summary
    .map(
      (item) => `
        <div class="result-row">
          <span class="inline-player">${playerNameHtml(item)}</span>
          <strong>${item.votes}</strong>
        </div>
      `,
    )
    .join("");
  const individualVoteRows = results.individual_votes
    .map(
      (item) => {
        const targets = Array.isArray(item.targets) && item.targets.length
          ? item.targets.map((target) => `${target.target_avatar || "🎲"} ${target.target_name}`).join(", ")
          : `${item.target_avatar || "🎲"} ${item.target_name || ""}`;
        return `
          <div class="result-row">
            <span>${escapeHtml(item.voter_avatar || "🎲")} ${escapeHtml(item.voter_name)} → ${escapeHtml(targets)}</span>
          </div>
        `;
      },
    )
    .join("");
  const scoreboardRows = (roomState.scoreboard || [])
    .filter((item) => item.discoveries > 0 || item.survivals > 0)
    .map(
      (item) => `
        <div class="score-row">
          <span>${escapeHtml(playerNameText(item))}</span>
          <strong>${item.discoveries} pronasao/la</strong>
          <strong>${item.survivals} prezivio/la</strong>
        </div>
      `,
    )
    .join("");
  const correctGuessers = (results.correct_guessers || [])
    .map((player) => escapeHtml(playerNameText(player)))
    .join(", ");

  const varalicaSummaryLabel = (results.varalice || []).length > 1 ? "Varalice su bile" : "Varalica je bio/la";

  phaseContent.innerHTML = `
    <div class="phase-card results-card results-card-${escapeHtml(finalResultDisplayMode)}">
      ${renderResultRevealHero(results, finalResultDisplayMode)}
      ${roomState.viewer_is_spectator ? spectatorNoticeHtml() : ""}
      <h2 class="vote-statistics-title">Statistika glasanja</h2>
      <p class="big-result varalica-summary">
        <span class="varalica-summary-label">${varalicaSummaryLabel}:</span>
        <span class="varalica-summary-name">${escapeHtml(varaliceNameText(results))}</span>
      </p>
      <p class="word-result">Riječ je bila: ${escapeHtml(results.word.hr)} (${escapeHtml(results.word.sr)})</p>
      <p class="outcome-text">${escapeHtml(results.outcome)}</p>
      <p class="helper-text">
        ${correctGuessers ? `Tacno pogodili: ${correctGuessers}` : "Niko nije tacno pogodio Varalicu."}
      </p>
      <div class="result-list">
        ${voteRows}
      </div>
      <h2>Ko je za koga glasao</h2>
      <div class="result-list">
        ${individualVoteRows}
      </div>
      ${
        scoreboardRows
          ? `<h2>Mini scoreboard</h2>
             <div class="scoreboard-list">${scoreboardRows}</div>`
          : ""
      }
      ${
        isHost && revealSequence.showReplay
          ? `<button id="newRoundButton" class="replay">Nova runda</button>`
          : `<p class="helper-text">${isHost ? "Nova runda ce biti dostupna za trenutak." : "Host moze pokrenuti novu rundu."}</p>`
      }
    </div>
  `;

  const newRoundButton = document.querySelector("#newRoundButton");
  if (newRoundButton) newRoundButton.addEventListener("click", startNewRound);
}

function playerReactionKey(reaction) {
  if (!reaction) return "";
  if (reaction.identity) return String(reaction.identity);
  return `${reaction.emoji}:${reaction.created_at}`;
}

function orderedRoomPlayers() {
  return [...(roomState?.players || [])].sort((left, right) => {
    const leftSpectator = Boolean(left.is_spectator);
    const rightSpectator = Boolean(right.is_spectator);
    if (leftSpectator !== rightSpectator) {
      return leftSpectator ? 1 : -1;
    }
    return 0;
  });
}

function renderPlayerReactionCluster(reactions) {
  const list = reactions || [];
  if (!list.length) return "";
  const bubbles = list
    .map(
      (reaction) =>
        `<span class="reaction-pop" data-reaction-key="${escapeHtml(playerReactionKey(reaction))}" aria-label="Reakcija">${escapeHtml(reaction.emoji)}</span>`,
    )
    .join("");
  return `<span class="reaction-pop-cluster">${bubbles}</span>`;
}

function syncPlayerReactionBubbles(inlinePlayer, reactions) {
  if (!inlinePlayer) return;

  const reactionList = (reactions || []).slice().sort((left, right) => (left.created_at || 0) - (right.created_at || 0));
  inlinePlayer.querySelectorAll(":scope > .reaction-pop").forEach((element) => element.remove());

  let cluster = inlinePlayer.querySelector(".reaction-pop-cluster");
  if (!reactionList.length) {
    cluster?.remove();
    return;
  }

  if (!cluster) {
    cluster = document.createElement("span");
    cluster.className = "reaction-pop-cluster";
    inlinePlayer.appendChild(cluster);
  }

  const desiredKeys = reactionList.map((reaction) => playerReactionKey(reaction));
  const desiredKeySet = new Set(desiredKeys);
  cluster.querySelectorAll(".reaction-pop").forEach((element) => {
    if (!desiredKeySet.has(element.dataset.reactionKey)) {
      element.remove();
    }
  });

  reactionList.forEach((reaction, index) => {
    const key = playerReactionKey(reaction);
    let bubble = cluster.querySelector(`.reaction-pop[data-reaction-key="${CSS.escape(key)}"]`);
    if (bubble && bubble.dataset.reactionKey === key && bubble.textContent === reaction.emoji) {
      if (cluster.children[index] !== bubble) {
        cluster.insertBefore(bubble, cluster.children[index] || null);
      }
      return;
    }

    if (!bubble) {
      bubble = document.createElement("span");
      bubble.className = "reaction-pop";
      bubble.setAttribute("aria-label", "Reakcija");
      cluster.appendChild(bubble);
    }

    bubble.dataset.reactionKey = key;
    bubble.textContent = reaction.emoji;
    if (cluster.children[index] !== bubble) {
      cluster.insertBefore(bubble, cluster.children[index] || null);
    }

    bubble.classList.remove("reaction-pop-repulse");
    void bubble.offsetWidth;
    bubble.classList.add("reaction-pop-repulse");
  });
}

function patchRevealPlayersInPlace() {
  if (roomState.state !== "reveal") return false;
  const rows = [...playersList.querySelectorAll(".player-row")];
  const players = orderedRoomPlayers();
  if (rows.length === 0 || rows.length !== players.length) return false;
  if (rows.some((row, index) => row.dataset.playerId !== players[index].id)) return false;

  players.forEach((player, index) => {
    const row = rows[index];
    if (!row) return;
    row.dataset.playerId = player.id;
    row.classList.toggle("is-spectator", Boolean(player.is_spectator));
    row.classList.toggle("is-current", Boolean(player.is_current && !player.is_spectator));
    syncRevealStatusBadge(row, player);
  });
  return true;
}

function patchDiscussionPlayersInPlace() {
  if (roomState.state !== "discussion" && roomState.state !== "overtime") return false;
  const rows = [...playersList.querySelectorAll(".player-row")];
  const players = orderedRoomPlayers();
  if (rows.length === 0 || rows.length !== players.length) return false;
  if (rows.some((row, index) => row.dataset.playerId !== players[index].id)) return false;

  players.forEach((player, index) => {
    const row = rows[index];
    row.classList.toggle("is-spectator", Boolean(player.is_spectator));
    row.classList.toggle("is-current", Boolean(player.is_current && !player.is_spectator));
    clearRevealStatusBadges(row);
    syncPlayerReactionBubbles(
      row.querySelector(".inline-player"),
      player.reactions?.length ? player.reactions : player.reaction ? [player.reaction] : [],
    );

    const nameBlock = row.querySelector(".player-name");
    let associationEl = row.querySelector(".association-bubble");
    if (player.association) {
      const associationText = player.association.text || "";
      if (!associationEl) {
        nameBlock?.insertAdjacentHTML("beforeend", `<div class="association-bubble">${escapeHtml(associationText)}</div>`);
      } else if (associationEl.textContent !== associationText) {
        associationEl.textContent = associationText;
      }
    } else {
      associationEl?.remove();
    }
  });
  return true;
}

function renderPlayers() {
  const phase = roomState.state;
  let patched = false;
  if (phase === lastPlayersListPhase) {
    if (phase === "discussion" || phase === "overtime") {
      patched = patchDiscussionPlayersInPlace();
    } else if (phase === "reveal") {
      patched = patchRevealPlayersInPlace();
    }
  }
  if (patched) return;
  lastPlayersListPhase = phase;

  playersList.innerHTML = "";
  const orderedPlayers = orderedRoomPlayers();

  for (const player of orderedPlayers) {
    const row = document.createElement("div");
    row.className = "player-row";
    row.dataset.playerId = player.id;
    if (player.is_spectator) {
      row.classList.add("is-spectator");
    }
    if (player.is_current && !player.is_spectator) {
      row.classList.add("is-current");
    }

    const revealStatus = revealStatusForPlayer(player);
    const connectionLabels = {
      active: "Active",
      away: "Away",
      idle: "Idle",
      offline: "Offline",
    };
    const connectionStatusLabel = connectionLabels[player.connection_status] || "Offline";
    const disconnectedLabel = "";
    const connectedLabel = "";
    const isViewerHost = roomState.viewer_id === roomState.host_id;
    const hostLabel = player.is_host ? `<span class="badge host-badge" title="Host">👑</span>` : "";
    const currentLabel = "";
    const spectatorLabel = player.is_spectator
      ? `<span class="badge spectator-badge">Posmatrač</span><span class="badge spectator-waiting-badge">Igraš od sledeće runde</span>`
      : "";
    const voteLabel = player.requested_vote ? `<span class="badge vote-requested">Trazi glasanje</span>` : "";
    const associationBubble = player.association
      ? `<div class="association-bubble">${escapeHtml(player.association.text)}</div>`
      : "";
    const playerReactions = player.reactions?.length ? player.reactions : player.reaction ? [player.reaction] : [];
    const reactionCluster = renderPlayerReactionCluster(playerReactions);

    row.innerHTML = `
      <div class="player-name">
        <span class="inline-player">
          <span class="status-dot ${escapeHtml(player.connection_status || "offline")}" title="${connectionStatusLabel}"></span>
          ${playerNameHtml(player)}
          ${reactionCluster}
        </span>
        ${associationBubble}
      </div>
      <div class="player-meta">
        ${hostLabel}
        ${spectatorLabel}
        ${currentLabel}
        ${voteLabel}
        ${disconnectedLabel}
        ${connectedLabel}
        ${
          phase === "reveal" && player.is_active_round_player
            ? `<span class="badge reveal-status ${revealStatus.className}" data-reveal-status-key="${revealStatus.className}:${revealStatus.label}">${revealStatus.label}</span>`
            : ""
        }
        ${
          isViewerHost && player.id !== roomState.viewer_id
            ? `<button class="kick-x-button" data-kick-id="${escapeHtml(player.id)}" title="Izbaci igrača" aria-label="Izbaci igrača">×</button>`
            : ""
        }
      </div>
    `;
    playersList.appendChild(row);
  }

  document.querySelectorAll("[data-kick-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.dataset.kickId;
      showConfirmAction("Da li sigurno zelis izbaciti ovog igraca?", () => kickPlayer(targetId));
    });
  });
}

async function copyRoomLink() {
  const link = inviteLink();
  try {
    await navigator.clipboard.writeText(link);
    copyLinkButton.textContent = "Kopirano";
    setTimeout(() => {
      copyLinkButton.textContent = "Kopiraj link";
    }, 1200);
  } catch {
    showError(link);
  }
}

async function copyRoomCode() {
  try {
    await navigator.clipboard.writeText(localRoomCode);
    copyCodeButton.textContent = "Kod kopiran";
    setTimeout(() => {
      copyCodeButton.textContent = "Kopiraj kod";
    }, 1200);
  } catch {
    showError(localRoomCode);
  }
}

function toggleQrPanel() {
  const inviteUrl = inviteLink();
  if (!inviteUrl) {
    showError("QR link nije spreman. Pokušaj ponovo.");
    return;
  }
  if (!qrPanel.classList.contains("hidden")) {
    qrPanel.classList.add("hidden");
    showQrButton.textContent = "QR";
    return;
  }

  qrPanel.innerHTML = `
    <div class="qr-code-card">
      <div id="roomQrCode" class="qr-code-box" aria-label="QR kod za ulazak u sobu"></div>
    </div>
  `;
  console.log("QR invite URL:", inviteUrl);
  const qrContainer = document.querySelector("#roomQrCode");
  qrContainer.innerHTML = "";
  try {
    if (typeof window.QRCode !== "function") {
      throw new Error("QR library not loaded");
    }
    new window.QRCode(qrContainer, {
      text: inviteUrl,
      width: 328,
      height: 328,
      colorDark: "#000000",
      colorLight: "#ffffff",
      correctLevel: window.QRCode.CorrectLevel.M,
    });
    qrContainer.removeAttribute("title");
    qrContainer.querySelectorAll("canvas, img").forEach((node) => {
      node.removeAttribute("title");
    });
    qrPanel.classList.remove("hidden");
    showQrButton.textContent = "Sakrij QR";
  } catch (error) {
    console.error("QR generation failed:", error);
    showError("QR kod nije mogao biti generisan. Koristi Kopiraj link.");
    qrPanel.innerHTML = "";
    qrPanel.classList.add("hidden");
  }
}

async function apiRequest(url, body) {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) {
      showError(data.detail || "Doslo je do greske.");
      return null;
    }
    return data;
  } catch {
    showError("Nije moguce spojiti se na server.");
    return null;
  }
}

function clearError() {
  errorBox.classList.add("hidden");
  errorBox.textContent = "";
}

function showError(message) {
  errorBox.classList.remove("hidden");
  errorBox.textContent = message;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatSeconds(totalSeconds) {
  const safeSeconds = Math.max(0, Number(totalSeconds) || 0);
  const minutes = Math.floor(safeSeconds / 60);
  const seconds = safeSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

async function bootstrapRoomSession() {
  if (localRoomCode && localPlayerId && (!inviteRoomCode || inviteRoomCode === localRoomCode)) {
    const exists = await validateRoomExists(localRoomCode);
    if (!exists) {
      showExpiredRoomUI(localRoomCode);
      window.history.replaceState({}, "", "/");
      return;
    }
    setupView.classList.add("hidden");
    expiredRoomView.classList.add("hidden");
    roomView.classList.remove("hidden");
    connectionStatus.classList.remove("hidden");
    applyRoomPanelCollapse();
    connectSocket();
    return;
  }

  if (inviteRoomCode) {
    const code = inviteRoomCode;
    const exists = await validateRoomExists(code);
    if (!exists) {
      showExpiredRoomUI(code);
      return;
    }
    showValidInviteUI(code);
  }
}

bootstrapRoomSession();
