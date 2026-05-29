const setupView = document.querySelector("#setupView");
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
const rulesModal = document.querySelector("#rulesModal");
const leaveModal = document.querySelector("#leaveModal");
const cancelLeaveButton = document.querySelector("#cancelLeaveButton");
const confirmLeaveButton = document.querySelector("#confirmLeaveButton");
const confirmActionModal = document.querySelector("#confirmActionModal");
const confirmActionText = document.querySelector("#confirmActionText");
const cancelActionButton = document.querySelector("#cancelActionButton");
const confirmActionButton = document.querySelector("#confirmActionButton");
const toastContainer = document.querySelector("#toastContainer");

const SESSION_MAX_AGE_MS = 15 * 60 * 1000;
const HEARTBEAT_INTERVAL_MS = 12000;
const PRODUCTION_ORIGIN = "https://varalica.autolovac.space";
const IMPOSTOR_REVEAL_AVATAR_URL = "/static/assets/Varalica_crveno.png";
const IMPOSTOR_REVEAL_RING_URL = "/static/assets/varalica_neon_ring.svg";
const IMPOSTOR_REVEAL_SMOKE_URL = "/static/assets/varalica_smoke_overlay.svg";
const IMPOSTOR_REVEAL_SCANLINES_URL = "/static/assets/varalica_glitch_scanlines.svg";
const AVATARS = [
  "😀", "😎", "🤓", "🥳", "😇", "🤠", "🐵", "🦊", "🐼", "🐸",
  "🐱", "🐶", "🦁", "🐯", "🦄", "🐧", "🐙", "🦖", "👽", "🤖",
  "🧙‍♂️", "🧙‍♀️", "🦸‍♂️", "🦸‍♀️", "🕵️‍♂️", "🕵️‍♀️", "👑", "🎭", "🎲", "🔥",
];

expireOldSession();

let roomState = null;
let socket = null;
let localRoomCode = localStorage.getItem("varalica_room_code") || "";
let localPlayerId = localStorage.getItem("varalica_player_id") || "";
let selectedAvatar = localStorage.getItem("varalica_avatar") || "";
let selectedCategory = localStorage.getItem("varalica_selected_category") || "Sve kategorije";
let selectedDiscussionSeconds = Number(localStorage.getItem("varalica_discussion_seconds") || 180);
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
let inviteRoomCode = "";
let reconnectTimer = null;
let heartbeatTimer = null;
let shouldReconnectSocket = true;
let connectionMode = "disconnected";
let hadSocketDisconnect = false;
let lastSeenEventId = "";
let currentTurnId = "";
let nextPlayerUnlockAt = 0;
let nextPlayerCountdownTimer = null;
let pendingConfirmAction = null;

const pathRoomMatch = window.location.pathname.match(/^\/room\/([A-Z0-9]{5})$/i);
if (pathRoomMatch) {
  inviteRoomCode = pathRoomMatch[1].toUpperCase();
  roomCodeInput.value = inviteRoomCode;
  inviteNotice.textContent = `Pridruzuješ se sobi ${inviteRoomCode}. Unesi ime i klikni “Pridruzi se”.`;
  inviteNotice.classList.remove("hidden");
  createRoomButton.classList.add("hidden");
}

createRoomButton.addEventListener("click", createRoom);
joinRoomButton.addEventListener("click", joinRoom);
copyCodeButton.addEventListener("click", copyRoomCode);
copyLinkButton.addEventListener("click", copyRoomLink);
showQrButton.addEventListener("click", toggleQrPanel);
resetRoomButton.addEventListener("click", resetRoom);
leaveRoomButton.addEventListener("click", showLeaveModal);
rulesButton.addEventListener("click", () => showModal(rulesModal));
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
clearAvatarButton.addEventListener("click", () => {
  selectedAvatar = "";
  localStorage.removeItem("varalica_avatar");
  renderAvatarGrid();
});
renderAvatarGrid();
setConnectionMode("disconnected");
touchSession();

async function createRoom() {
  clearError();
  const name = playerNameInput.value;
  const result = await apiRequest("/api/rooms", { name, avatar: selectedAvatar || null });
  if (!result) return;
  enterRoom(result.room_code, result.player_id, result.avatar);
}

async function joinRoom() {
  clearError();
  const name = playerNameInput.value;
  const code = roomCodeInput.value.trim().toUpperCase();
  if (!code) {
    showError("Unesi kod sobe.");
    return;
  }
  const result = await apiRequest(`/api/rooms/${code}/join`, { name, avatar: selectedAvatar || null });
  if (!result) return;
  enterRoom(result.room_code, result.player_id, result.avatar);
}

function enterRoom(roomCode, playerId, avatar) {
  localRoomCode = roomCode;
  localPlayerId = playerId;
  hasRevealedPrivateCard = false;
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
  connectSocket();
}

function setConnectionMode(mode) {
  connectionMode = mode;
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
    nextPlayerUnlockAt = Date.now() + 3000;
    scheduleNextPlayerCountdown();
  }
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
    if (roomState.state === "reveal" && previousState !== "reveal") {
      hasRevealedPrivateCard = false;
      resetRevealSequence();
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
      handleExpiredRoom();
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

async function startRound() {
  clearError();
  touchSession();
  hasRevealedPrivateCard = false;
  await apiRequest(`/api/rooms/${localRoomCode}/start`, {
    player_id: localPlayerId,
    category: selectedCategory,
    discussion_seconds: selectedDiscussionSeconds,
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
  await apiRequest(`/api/rooms/${localRoomCode}/next-player`, { player_id: localPlayerId });
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

async function submitFinalVote(targetId) {
  clearError();
  touchSession();
  await apiRequest(`/api/rooms/${localRoomCode}/vote`, {
    player_id: localPlayerId,
    target_id: targetId,
  });
}

async function startNewRound() {
  clearError();
  touchSession();
  hasRevealedPrivateCard = false;
  await apiRequest(`/api/rooms/${localRoomCode}/new-round`, { player_id: localPlayerId });
}

async function resetRoom() {
  clearError();
  touchSession();
  hasRevealedPrivateCard = false;
  await apiRequest(`/api/rooms/${localRoomCode}/reset`, { player_id: localPlayerId });
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
  if (localRoomCode && localPlayerId) {
    await apiRequest(`/api/rooms/${localRoomCode}/leave`, { player_id: localPlayerId });
  }
  shouldReconnectSocket = false;
  if (socket) socket.close();
  localStorage.removeItem("varalica_room_code");
  localStorage.removeItem("varalica_player_id");
  localStorage.removeItem("varalica_last_active_at");
  sessionStorage.clear();
  localRoomCode = "";
  localPlayerId = "";
  roomState = null;
  roomView.classList.add("hidden");
  setupView.classList.remove("hidden");
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
  if (!roomState?.results?.varalica) return;

  revealSequence = {
    active: true,
    phase: "overlay_intro",
    countdown: 0,
    complete: false,
    showReplay: false,
  };

  const isCurrentUserVaralica = roomState.viewer_id === roomState.results.varalica.id;
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

  setRevealPhase("overlay_intro");
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("countdown_4", 4), 300));
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("countdown_3", 3), 1300));
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("countdown_2", 2), 2300));
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("countdown_1", 1), 3300));
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("title_reveal"), 4600));
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("nickname_reveal"), 6300));
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("statistics_reveal"), 7000));
  revealSequenceTimers.push(setTimeout(() => setRevealPhase("complete"), 8300));
  revealSequenceTimers.push(setTimeout(() => {
    revealSequence = { ...revealSequence, showReplay: true };
    render();
  }, 10300));
}

function resetRevealSequence() {
  revealSequenceTimers.forEach((timer) => clearTimeout(timer));
  revealSequenceTimers = [];
  revealSequence = {
    active: false,
    phase: "complete",
    countdown: 0,
    complete: false,
    showReplay: false,
  };
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

function handleExpiredRoom() {
  shouldReconnectSocket = false;
  stopHeartbeat();
  if (socket) socket.close();
  clearStoredSession();
  localRoomCode = "";
  localPlayerId = "";
  roomState = null;
  roomView.classList.add("hidden");
  setupView.classList.remove("hidden");
  inviteNotice.classList.add("hidden");
  createRoomButton.classList.remove("hidden");
  window.history.replaceState({}, "", "/");
  setConnectionMode("disconnected");
  showToast("Soba je istekla", "error");
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
  window.history.replaceState({}, "", "/");
  setConnectionMode("disconnected");
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
  const { hostname, origin } = window.location;
  if (hostname === "varalica.autolovac.space" || hostname === "91.98.83.121") {
    return PRODUCTION_ORIGIN;
  }
  if (!hostname || hostname === "0.0.0.0") return PRODUCTION_ORIGIN;
  return origin;
}

function inviteLink() {
  const code = (localRoomCode || roomState?.room_code || "").trim().toUpperCase();
  if (!code) return "";
  return `${inviteOrigin()}/room/${encodeURIComponent(code)}`;
}

function render() {
  if (!roomState) return;
  roomCodeDisplay.textContent = roomState.room_code;
  roundDisplay.textContent = `Runda ${roomState.round_number || 1}`;
  playerCountBadge.textContent = `${roomState.player_count}/${roomState.max_players}`;
  resetRoomButton.classList.add("hidden");
  renderHostPanel();
  renderPlayers();

  if (roomState.state === "lobby") {
    renderLobby();
    return;
  }

  if (roomState.state === "reveal") {
    renderReveal();
    return;
  }

  if (roomState.state === "discussion") {
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
  const actions = roundHasStarted ? [`<button id="hostResetRoomButton" class="small danger">Resetuj sobu</button>`] : [];
  if (roomState.state === "reveal") {
    actions.unshift(`<button id="hostChangeWordButton" class="small secondary">Promijeni riječ</button>`);
  } else if (["discussion", "vote_request", "ready_for_final_voting", "final_voting", "overtime", "overtime_voting", "voting_complete", "results"].includes(roomState.state)) {
    actions.unshift(`
      <div class="host-helper">
        <button class="small secondary" disabled>Promijeni riječ</button>
        <p class="helper-text">Riječ se može promijeniti samo prije početka diskusije.</p>
      </div>
    `);
  }
  if (roomState.state === "discussion" && roomState.discussion) {
    actions.unshift(`<button id="hostOpenVotingButton" class="small" ${roomState.discussion.voting_unlocked ? "" : "disabled"}>Otvori glasanje</button>`);
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
  document.querySelector("#hostResetRoomButton")?.addEventListener("click", resetRoom);
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
  const canStart = isHost && roomState.player_count >= roomState.min_players;
  const categories = roomState.categories || ["Sve kategorije"];
  const durationOptions = roomState.allowed_discussion_seconds || [120, 180, 300];
  if (!categories.includes(selectedCategory)) {
    selectedCategory = roomState.selected_category || "Sve kategorije";
  }
  if (!durationOptions.includes(selectedDiscussionSeconds)) {
    selectedDiscussionSeconds = roomState.discussion_duration_seconds || 180;
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
  const startButton = document.querySelector("#startRoundButton");
  if (startButton) startButton.addEventListener("click", startRound);
}

function renderReveal() {
  const privateInfo = roomState.private;
  const me = roomState.players.find((player) => player.id === roomState.viewer_id);
  const alreadyConfirmed = Boolean(me?.confirmed);
  if (me && !me.viewed_secret && !me.confirmed) {
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
        <p class="helper-text">Cekamo podatke za ovu rundu.</p>
      </div>
    `;
    return;
  }

  if (!hasRevealedPrivateCard) {
    phaseContent.innerHTML = `
      <div class="phase-card">
        <h2>Tvoja tajna kartica</h2>
        <p class="helper-text">Provjeri je na svom telefonu i ne pokazuj drugim igracima.</p>
        <button id="showWordButton">Prikazi moju rijec</button>
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

  const secretHtml =
    privateInfo.role === "varalica"
      ? `<p class="big-message">Ti si Varalica</p>
         <div class="hint-box">
           <p class="eyebrow">Smjernica</p>
           <p>${escapeHtml(privateInfo.hint || "Slušaj druge igrače i pokušaj ostati uvjerljiv.")}</p>
           <span class="badge">Kategorija: ${escapeHtml(privateInfo.category || "Nepoznato")}</span>
         </div>`
      : `<p class="big-message">${escapeHtml(privateInfo.word.hr)} (${escapeHtml(privateInfo.word.sr)})</p>
         <p class="helper-text">Kategorija: ${escapeHtml(privateInfo.word.category)}</p>`;

  phaseContent.innerHTML = `
    <div class="phase-card">
      <h2>Tvoja tajna kartica</h2>
      ${secretHtml}
      <button id="confirmSeenButton" ${alreadyConfirmed ? "disabled" : ""}>
        ${alreadyConfirmed ? "Potvrdjeno" : "OK, vidio sam"}
      </button>
      <p class="helper-text">Diskusija ne moze poceti dok svi aktivni igraci ne potvrde.</p>
    </div>
  `;

  const confirmButton = document.querySelector("#confirmSeenButton");
  if (confirmButton && !alreadyConfirmed) {
    confirmButton.addEventListener("click", confirmSeen);
  }
}

function renderDiscussion() {
  const isHost = roomState.viewer_id === roomState.host_id;
  const discussion = roomState.discussion;
  const me = roomState.players.find((player) => player.id === roomState.viewer_id);
  const currentPlayer = roomState.players.find((player) => player.id === discussion.current_player_id);
  const canAdvanceTurn = isHost || me?.id === discussion.current_player_id;
  const nextLockLeft = nextPlayerLockSecondsLeft();
  const nextButtonHtml = canAdvanceTurn
    ? `<button id="nextPlayerButton" ${nextLockLeft > 0 ? "disabled" : ""}>Sljedeci igrac</button>
       ${nextLockLeft > 0 ? `<p class="helper-text">Dostupno za ${nextLockLeft}...</p>` : ""}`
    : `<p class="helper-text">Samo host ili trenutni igrac mogu prebaciti red.</p>`;
  const voteLocked = !discussion.voting_unlocked;
  const votingControl = voteLocked
    ? `<button disabled>Otvori glasanje</button>`
    : isHost
      ? `<button id="openFinalVotingButton">Otvori glasanje</button>`
      : `<button disabled>Host otvara glasanje</button>`;
  const votingHelper = voteLocked
    ? `Glasanje ce biti dostupno uskoro. Preostalo: ${formatSeconds(discussion.voting_seconds_left)}.`
    : "Host sada moze otvoriti glasanje.";

  phaseContent.innerHTML = `
    <div class="phase-card discussion-card">
      <div class="timer-box">
        <span>Diskusija</span>
        <strong>${formatSeconds(discussion.remaining_seconds)}</strong>
      </div>
      <div class="current-player-card">
        <p class="eyebrow">Trenutni igrac</p>
        <p class="current-player-name">${escapeHtml(playerNameText(currentPlayer))}</p>
      </div>
      ${
        isHost
          ? `<button id="nextPlayerButton">Sljedeći igrač</button>`
          : `<p class="helper-text">Samo host ili trenutni igrac mogu prebaciti red.</p>`
      }
      ${votingControl}
      <p class="helper-text">
        ${votingHelper}
      </p>
    </div>
  `;

  const nextButton = document.querySelector("#nextPlayerButton");
  if (!nextButton && canAdvanceTurn) {
    document.querySelector(".discussion-card")?.insertAdjacentHTML("beforeend", `<button id="nextPlayerButton">Sljedeci igrac</button>`);
  }
  const insertedNextButton = document.querySelector("#nextPlayerButton");
  if (insertedNextButton) {
    if (nextLockLeft > 0) {
      insertedNextButton.disabled = true;
      insertedNextButton.insertAdjacentHTML("afterend", `<p class="helper-text">Dostupno za ${nextLockLeft}...</p>`);
    } else {
      insertedNextButton.addEventListener("click", nextPlayer);
    }
  }

  const openButton = document.querySelector("#openFinalVotingButton");
  if (openButton) openButton.addEventListener("click", openFinalVoting);
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
          : `<p class="helper-text">Cekamo hosta da otvori glasanje.</p>`
      }
    </div>
  `;

  const openButton = document.querySelector("#openFinalVotingButton");
  if (openButton) openButton.addEventListener("click", openFinalVoting);
}

function renderOvertime() {
  const isHost = roomState.viewer_id === roomState.host_id;
  const overtime = roomState.overtime;
  const me = roomState.players.find((player) => player.id === roomState.viewer_id);
  const currentPlayer = roomState.players.find((player) => player.id === overtime.current_player_id);
  const canAdvanceTurn = isHost || me?.id === overtime.current_player_id;
  const nextLockLeft = nextPlayerLockSecondsLeft();

  if (!overtime.started) {
    phaseContent.innerHTML = `
      <div class="phase-card overtime-card">
        <p class="eyebrow">Produzetak</p>
        <h2>Glasanje je neriješeno.</h2>
        <p class="helper-text">Varalica se jos ne otkriva. Host moze produziti diskusiju za 60 sekundi.</p>
        ${
          isHost
            ? `<button id="startOvertimeButton">Produži igru 60 sekundi</button>`
            : `<p class="helper-text">Cekamo hosta da pokrene produzetak.</p>`
        }
      </div>
    `;
    const button = document.querySelector("#startOvertimeButton");
    if (button) button.addEventListener("click", startOvertime);
    return;
  }

  phaseContent.innerHTML = `
    <div class="phase-card overtime-card">
      <p class="eyebrow">Produzetak</p>
      <div class="timer-box">
        <span>Produzetak</span>
        <strong>${formatSeconds(overtime.remaining_seconds)}</strong>
      </div>
      <div class="current-player-card">
        <p class="eyebrow">Trenutni igrac</p>
        <p class="current-player-name">${escapeHtml(playerNameText(currentPlayer))}</p>
      </div>
      ${
        isHost
          ? `<button id="nextPlayerButton">Sljedeći igrač</button>`
          : `<p class="helper-text">Samo host ili trenutni igrac mogu prebaciti red.</p>`
      }
      <p class="helper-text">Nakon isteka vremena glasanje se automatski otvara ponovo.</p>
    </div>
  `;

  const nextButton = document.querySelector("#nextPlayerButton");
  if (!nextButton && canAdvanceTurn) {
    document.querySelector(".overtime-card")?.insertAdjacentHTML("beforeend", `<button id="nextPlayerButton">Sljedeci igrac</button>`);
  }
  const insertedNextButton = document.querySelector("#nextPlayerButton");
  if (insertedNextButton) {
    if (nextLockLeft > 0) {
      insertedNextButton.disabled = true;
      insertedNextButton.insertAdjacentHTML("afterend", `<p class="helper-text">Dostupno za ${nextLockLeft}...</p>`);
    } else {
      insertedNextButton.addEventListener("click", nextPlayer);
    }
  }
}

function renderFinalVoting() {
  const me = roomState.players.find((player) => player.id === roomState.viewer_id);
  const hasVoted = Boolean(me?.has_voted);
  const activePlayers = roomState.players.filter((player) => player.is_active_round_player && player.id !== roomState.viewer_id);
  const activeRoundPlayers = roomState.players.filter((player) => player.is_active_round_player);
  const votedCount = activeRoundPlayers.filter((player) => player.has_voted).length;
  const isOvertimeVote = roomState.state === "overtime_voting";

  phaseContent.innerHTML = `
    <div class="phase-card">
      <h2>${isOvertimeVote ? "Glasanje nakon produzetka" : "Finalno glasanje"}</h2>
      <p class="helper-text">
        Odaberi jednog igraca za kojeg mislis da je Varalica. Glasovi se ne otkrivaju dok svi ne glasaju.
      </p>
      <p class="helper-text">Ne mozes glasati za sebe.</p>
      <div class="vote-progress-private">
        <strong>${votedCount}/${activeRoundPlayers.length}</strong>
        <span>glasalo</span>
      </div>
      <div class="vote-list">
        ${activePlayers
          .map(
            (player) => `
              <div class="vote-option">
                <div>
                  <strong class="inline-player">${playerNameHtml(player)}</strong>
                  ${player.id === roomState.viewer_id ? `<span class="helper-text">Ti</span>` : ""}
                </div>
                <button class="small vote-button" data-target-id="${escapeHtml(player.id)}" ${hasVoted ? "disabled" : ""}>
                  Glasaj
                </button>
              </div>
            `,
          )
          .join("")}
      </div>
      <p class="helper-text">
        ${hasVoted ? "Tvoj glas je zaprimljen. Cekamo ostale igrace." : "Mozes glasati samo jednom."}
      </p>
    </div>
  `;

  if (!hasVoted) {
    document.querySelectorAll(".vote-button").forEach((button) => {
      button.addEventListener("click", () => submitFinalVote(button.dataset.targetId));
    });
  }
}

function renderVotingComplete() {
  const isHost = roomState.viewer_id === roomState.host_id;
  const voting = roomState.voting_complete;
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
              <p class="helper-text">Host može produžiti diskusiju za 60 sekundi ili odmah prikazati Varalicu.</p>
              ${isHost ? `<button id="startOvertimeButton">Produži igru 60 sekundi</button>` : ""}
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
  const isCurrentUserVaralica = roomState.viewer_id === results.varalica.id;
  if (wasCaught && isCurrentUserVaralica) return "impostor-caught-red";
  if (wasCaught && !isCurrentUserVaralica) return "players-win-green";
  if (!wasCaught && isCurrentUserVaralica) return "impostor-win-green";
  return "players-lost-red";
}

function revealTheme(results, phase = "complete") {
  const countdownPhases = new Set(["overlay_intro", "countdown_4", "countdown_3", "countdown_2", "countdown_1", "title_reveal"]);
  if (countdownPhases.has(phase)) return "danger-red-for-all";
  return finalOutcomeTheme(results);
}

function revealOutcomeTitle(results) {
  if (results.was_varalica_caught === true) {
    return roomState.viewer_id === results.varalica.id ? "PROVALJEN" : "OTKRIVEN";
  }
  return roomState.viewer_id === results.varalica.id ? "MAJSTOR MANIPULACIJE" : "VARALICA JE PREŽIVJELA";
}

function revealOutcomeSubtitle(results) {
  const isCurrentUserVaralica = roomState.viewer_id === results.varalica.id;
  if (results.was_varalica_caught === true) {
    return isCurrentUserVaralica ? "Manipulacija nije uspjela." : "Igrači su pronašli Varalicu.";
  }
  return isCurrentUserVaralica ? "Igrači moraju još pasulja da pojedu." : "Varalica vas je preveslala.";
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
      <img
        class="impostor-reveal-avatar-img"
        src="${escapeHtml(IMPOSTOR_REVEAL_AVATAR_URL)}"
        alt="Varalica avatar"
        loading="eager"
        decoding="async"
        onerror="this.closest('.impostor-avatar-asset').classList.add('image-failed')"
      >
      <div class="impostor-reveal-avatar-fallback" aria-hidden="true">
        <div class="impostor-hood">
          <div class="impostor-face">
            <span class="impostor-eye">&times;</span>
            <span class="impostor-eye">&times;</span>
          </div>
          <div class="impostor-finger"></div>
        </div>
      </div>
    </div>
  `;
}

function renderImpostorReveal(results) {
  const phase = revealSequence.phase;
  const theme = revealTheme(results, phase);
  const showTitle = phase === "title_reveal" || phase === "nickname_reveal" || phase === "statistics_reveal";
  const showName = phase === "nickname_reveal" || phase === "statistics_reveal";
  const isImpact = phase === "countdown_1" || phase === "nickname_reveal";
  const nickname = results.varalica?.name || "Nepoznato";
  const title = revealOutcomeTitle(results);
  const subtitle = revealOutcomeSubtitle(results);

  phaseContent.innerHTML = `
    <div class="impostor-reveal-stage ${escapeHtml(theme)} ${escapeHtml(phase)} ${isImpact ? "impact" : ""}">
      <div class="impostor-reveal-vignette"></div>
      <img
        class="impostor-smoke-overlay"
        src="${escapeHtml(IMPOSTOR_REVEAL_SMOKE_URL)}"
        alt=""
        aria-hidden="true"
      >
      <div class="impostor-reveal-card">
        <div class="impostor-avatar-wrap">
          ${impostorAvatarHtml()}
          <img
            class="impostor-scanlines-overlay"
            src="${escapeHtml(IMPOSTOR_REVEAL_SCANLINES_URL)}"
            alt=""
            aria-hidden="true"
          >
          <div class="impostor-glitch-lines" aria-hidden="true"></div>
          ${
            revealSequence.countdown
              ? `<div class="impostor-countdown">${revealSequence.countdown}</div>`
              : ""
          }
        </div>
        <div class="impostor-reveal-copy">
          ${showTitle ? `<p class="impostor-pretitle">VARALICA JE...</p>` : `<p class="impostor-pretitle ghost">OTKRIVANJE</p>`}
          ${showName ? `<h2 class="impostor-nickname" title="${escapeHtml(nickname)}">${escapeHtml(nickname)}</h2>` : ""}
          ${showName ? `<p class="impostor-outcome-title">${escapeHtml(title)}</p>` : ""}
          ${showName ? `<p class="impostor-subtitle">${escapeHtml(subtitle)}</p>` : ""}
        </div>
      </div>
    </div>
  `;
}

function renderResultRevealHero(results) {
  const theme = finalOutcomeTheme(results);
  const nickname = results.varalica?.name || "Nepoznato";
  return `
    <div class="result-reveal-hero ${escapeHtml(theme)}">
      <div class="result-reveal-avatar">
        ${impostorAvatarHtml()}
      </div>
      <div class="result-reveal-text">
        <p class="impostor-pretitle">VARALICA JE...</p>
        <h2 class="impostor-nickname" title="${escapeHtml(nickname)}">${escapeHtml(nickname)}</h2>
        <p class="impostor-outcome-title">${escapeHtml(revealOutcomeTitle(results))}</p>
        <p class="impostor-subtitle">${escapeHtml(revealOutcomeSubtitle(results))}</p>
      </div>
    </div>
  `;
}

function renderResults() {
  const isHost = roomState.viewer_id === roomState.host_id;
  const results = roomState.results;
  if (revealSequence.active && !revealSequence.complete) {
    renderImpostorReveal(results);
    return;
  }
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
      (item) => `
        <div class="result-row">
          <span>${escapeHtml(item.voter_avatar || "🎲")} ${escapeHtml(item.voter_name)} → ${escapeHtml(item.target_avatar || "🎲")} ${escapeHtml(item.target_name)}</span>
        </div>
      `,
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

  phaseContent.innerHTML = `
    <div class="phase-card results-card">
      ${renderResultRevealHero(results)}
      <h2>Statistika glasanja</h2>
      <p class="big-result">Varalica je bio/la: ${escapeHtml(playerNameText(results.varalica))}</p>
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
          ? `<button id="newRoundButton">Igraj ponovo</button>`
          : `<p class="helper-text">${isHost ? "Igraj ponovo ce biti dostupno za trenutak." : "Host moze pokrenuti novu rundu."}</p>`
      }
    </div>
  `;

  const newRoundButton = document.querySelector("#newRoundButton");
  if (newRoundButton) newRoundButton.addEventListener("click", startNewRound);
}

function renderPlayers() {
  playersList.innerHTML = "";
  for (const player of roomState.players) {
    const row = document.createElement("div");
    row.className = "player-row";
    if (player.is_current) {
      row.classList.add("is-current");
    }

    const statusLabel = player.confirmed ? "Spreman" : "Nije vidio";
    const statusClass = player.confirmed ? "ready" : "waiting";
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
    const hostLabel = player.is_host ? `<span class="badge">👑 Host</span>` : "";
    const currentLabel = player.is_current ? `<span class="badge active-turn">Na redu</span>` : "";
    const voteLabel = player.requested_vote ? `<span class="badge vote-requested">Trazi glasanje</span>` : "";
    const finalVoteLabel =
      (roomState.state === "final_voting" || roomState.state === "overtime_voting" || roomState.state === "voting_complete" || roomState.state === "results") && player.is_active_round_player
        ? `<span class="badge ${player.has_voted ? "ready" : "waiting"}">${player.has_voted ? "Glasao/la" : "Nije glasao/la"}</span>`
        : "";
    const voteTargetLabel = roomState.state === "results" && player.vote_target
      ? `<div class="vote-target-line"><span>Glasao/la za:</span> <strong>${escapeHtml(playerNameText(player.vote_target))}</strong></div>`
      : "";

    row.innerHTML = `
      <div class="player-name">
        <span class="inline-player">
          <span class="status-dot ${escapeHtml(player.connection_status || "offline")}" title="${connectionStatusLabel}"></span>
          ${playerNameHtml(player)}
        </span>
        ${voteTargetLabel}
      </div>
      <div class="player-meta">
        ${hostLabel}
        ${currentLabel}
        ${voteLabel}
        ${finalVoteLabel}
        ${disconnectedLabel}
        ${connectedLabel}
        ${
          roomState.state === "reveal"
            ? `<span class="badge ${statusClass}">${statusLabel}</span>`
            : ""
        }
        ${
          isViewerHost && player.id !== roomState.viewer_id
            ? `<button class="small danger player-action-button" data-kick-id="${escapeHtml(player.id)}">Izbaci</button>`
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
  const link = inviteLink();
  if (!link) {
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
    <p class="helper-text">Scan to join</p>
  `;
  console.log("QR invite URL:", link);
  const qrContainer = document.querySelector("#roomQrCode");
  qrContainer.innerHTML = "";
  new window.QRCode(qrContainer, {
    text: link,
    width: 328,
    height: 328,
    colorDark: "#000000",
    colorLight: "#ffffff",
    correctLevel: window.QRCode.CorrectLevel.M,
  });
  qrPanel.classList.remove("hidden");
  showQrButton.textContent = "Sakrij QR";
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
      handleExpiredRoom();
      return;
    }
    setupView.classList.add("hidden");
    roomView.classList.remove("hidden");
    connectSocket();
    return;
  }

  if (inviteRoomCode) {
    const exists = await validateRoomExists(inviteRoomCode);
    if (!exists) {
      clearStoredSession();
      inviteRoomCode = "";
      roomCodeInput.value = "";
      inviteNotice.classList.add("hidden");
      createRoomButton.classList.remove("hidden");
      window.history.replaceState({}, "", "/");
      showToast("Soba je istekla", "error");
    }
  }
}

bootstrapRoomSession();
