/**
 * VoiceAgent Widget — embeddable voice chat widget
 *
 * Usage:
 *   <script src="https://yourdomain.com/widget.js"></script>
 *   <script>
 *     VoiceAgentWidget.init({
 *       agentId: "agent-uuid-here",
 *       apiUrl: "https://api.yourdomain.com",
 *       position: "bottom-right",
 *       theme: "dark"
 *     });
 *   </script>
 */
(function () {
  "use strict";

  var VERSION = "1.0.0";
  var DEFAULTS = {
    agentId: "",
    apiUrl: "",
    position: "bottom-right",
    theme: "dark",
    language: "en",
    title: "Voice Assistant",
    subtitle: "Click to start a conversation",
    primaryColor: "#3b82f6",
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  };

  var state = {
    config: null,
    isOpen: false,
    isRecording: false,
    isLoading: false,
    sessionId: null,
    messages: [],
    mediaRecorder: null,
    audioChunks: [],
  };

  function generateSessionId() {
    return "sess-" + Date.now().toString(36) + "-" + Math.random().toString(36).substr(2, 9);
  }

  function loadSession() {
    try {
      var saved = localStorage.getItem("voiceagent_session");
      if (saved) {
        var data = JSON.parse(saved);
        if (data.agentId === state.config.agentId) {
          state.sessionId = data.sessionId;
          state.messages = data.messages || [];
          return true;
        }
      }
    } catch (e) {}
    return false;
  }

  function saveSession() {
    try {
      localStorage.setItem("voiceagent_session", JSON.stringify({
        agentId: state.config.agentId,
        sessionId: state.sessionId,
        messages: state.messages,
      }));
    } catch (e) {}
  }

  function createStyles() {
    var c = state.config;
    var css = [
      ".va-widget * { box-sizing: border-box; margin: 0; padding: 0; }",
      ".va-widget { position: fixed; z-index: 2147483647; font-family: " + c.fontFamily + "; }",
      ".va-widget.va-bottom-right { bottom: 20px; right: 20px; }",
      ".va-widget.va-bottom-left { bottom: 20px; left: 20px; }",
      ".va-bubble { width: 60px; height: 60px; border-radius: 50%; background: " + c.primaryColor + "; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.25); transition: transform 0.2s, box-shadow 0.2s; }",
      ".va-bubble:hover { transform: scale(1.1); box-shadow: 0 6px 20px rgba(0,0,0,0.35); }",
      ".va-bubble svg { width: 28px; height: 28px; fill: #fff; }",
      ".va-panel { position: absolute; bottom: 70px; width: 380px; max-height: 520px; border-radius: 16px; overflow: hidden; display: none; flex-direction: column; box-shadow: 0 8px 32px rgba(0,0,0,0.2); }",
      ".va-panel.va-open { display: flex; }",
      ".va-panel.va-dark { background: #1e1e2e; color: #e0e0e0; }",
      ".va-panel.va-light { background: #ffffff; color: #333; }",
      ".va-panel.va-bottom-right { right: 0; }",
      ".va-panel.va-bottom-left { left: 0; }",
      ".va-header { padding: 16px 20px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); }",
      ".va-dark .va-header { background: #2a2a3e; }",
      ".va-light .va-header { background: #f8f9fa; border-bottom: 1px solid #e9ecef; }",
      ".va-header-dot { width: 10px; height: 10px; border-radius: 50%; background: #22c55e; }",
      ".va-header-text h3 { font-size: 14px; font-weight: 600; }",
      ".va-header-text p { font-size: 11px; opacity: 0.6; }",
      ".va-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 10px; max-height: 340px; min-height: 200px; }",
      ".va-msg { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.5; word-wrap: break-word; }",
      ".va-msg.va-user { align-self: flex-end; background: " + c.primaryColor + "; color: #fff; border-bottom-right-radius: 4px; }",
      ".va-msg.va-agent { align-self: flex-start; border-bottom-left-radius: 4px; }",
      ".va-dark .va-msg.va-agent { background: #2a2a3e; }",
      ".va-light .va-msg.va-agent { background: #f1f3f5; }",
      ".va-controls { padding: 12px 16px; display: flex; align-items: center; gap: 10px; border-top: 1px solid rgba(255,255,255,0.1); }",
      ".va-dark .va-controls { background: #2a2a3e; }",
      ".va-light .va-controls { background: #f8f9fa; border-top: 1px solid #e9ecef; }",
      ".va-mic-btn { width: 48px; height: 48px; border-radius: 50%; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s, transform 0.1s; }",
      ".va-mic-btn.va-idle { background: " + c.primaryColor + "; }",
      ".va-mic-btn.va-recording { background: #ef4444; animation: va-pulse 1s infinite; }",
      ".va-mic-btn:active { transform: scale(0.95); }",
      ".va-mic-btn svg { width: 22px; height: 22px; fill: #fff; }",
      ".va-input-area { flex: 1; display: flex; align-items: center; gap: 8px; }",
      ".va-input-area input { flex: 1; padding: 10px 14px; border-radius: 10px; border: none; font-size: 13px; outline: none; }",
      ".va-dark .va-input-area input { background: #1e1e2e; color: #e0e0e0; border: 1px solid #444; }",
      ".va-light .va-input-area input { background: #fff; color: #333; border: 1px solid #ddd; }",
      ".va-send-btn { width: 36px; height: 36px; border-radius: 50%; border: none; background: " + c.primaryColor + "; cursor: pointer; display: flex; align-items: center; justify-content: center; }",
      ".va-send-btn svg { width: 16px; height: 16px; fill: #fff; }",
      ".va-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }",
      ".va-volume-bar { height: 3px; background: rgba(255,255,255,0.2); border-radius: 2px; margin: 0 16px 8px; overflow: hidden; }",
      ".va-volume-fill { height: 100%; background: #22c55e; width: 0%; transition: width 0.1s; }",
      ".va-typing { font-size: 12px; opacity: 0.5; padding: 4px 16px 0; }",
      ".va-footer { padding: 8px 16px; text-align: center; font-size: 10px; opacity: 0.4; }",
      ".va-close-btn { position: absolute; top: 12px; right: 12px; width: 24px; height: 24px; border: none; background: none; cursor: pointer; opacity: 0.5; font-size: 18px; color: inherit; display: flex; align-items: center; justify-content: center; }",
      ".va-close-btn:hover { opacity: 1; }",
      ".va-keyboard-hint { font-size: 10px; opacity: 0.4; text-align: center; padding: 0 0 4px; }",
      "@keyframes va-pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); } 50% { box-shadow: 0 0 0 12px rgba(239,68,68,0); } }",
    ].join("\n");
    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);
  }

  function svgIcon(type) {
    var icons = {
      mic: '<svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>',
      send: '<svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>',
      chat: '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>',
    };
    return icons[type] || "";
  }

  function buildWidget() {
    var c = state.config;
    var posClass = "va-" + c.position;
    var themeClass = "va-" + c.theme;

    var container = document.createElement("div");
    container.className = "va-widget " + posClass;
    container.id = "voiceagent-widget";

    var bubble = document.createElement("div");
    bubble.className = "va-bubble";
    bubble.innerHTML = svgIcon("chat");
    bubble.setAttribute("aria-label", "Open voice assistant");
    bubble.addEventListener("click", togglePanel);

    var panel = document.createElement("div");
    panel.className = "va-panel " + themeClass + " " + posClass;
    panel.id = "va-panel";

    var header = document.createElement("div");
    header.className = "va-header";
    header.innerHTML = '<div class="va-header-dot"></div>' +
      '<div class="va-header-text"><h3>' + c.title + '</h3><p>' + c.subtitle + '</p></div>' +
      '<button class="va-close-btn" aria-label="Close">&times;</button>';
    header.querySelector(".va-close-btn").addEventListener("click", togglePanel);

    var messages = document.createElement("div");
    messages.className = "va-messages";
    messages.id = "va-messages";

    var volumeBar = document.createElement("div");
    volumeBar.className = "va-volume-bar";
    volumeBar.innerHTML = '<div class="va-volume-fill" id="va-volume-fill"></div>';

    var typing = document.createElement("div");
    typing.className = "va-typing";
    typing.id = "va-typing";
    typing.textContent = "";
    typing.style.display = "none";

    var controls = document.createElement("div");
    controls.className = "va-controls";

    var micBtn = document.createElement("button");
    micBtn.className = "va-mic-btn va-idle";
    micBtn.id = "va-mic-btn";
    micBtn.innerHTML = svgIcon("mic");
    micBtn.setAttribute("aria-label", "Record voice");
    micBtn.addEventListener("click", toggleRecording);

    var inputArea = document.createElement("div");
    inputArea.className = "va-input-area";

    var textInput = document.createElement("input");
    textInput.type = "text";
    textInput.placeholder = "Type a message...";
    textInput.id = "va-text-input";
    textInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendTextMessage();
      }
    });

    var sendBtn = document.createElement("button");
    sendBtn.className = "va-send-btn";
    sendBtn.innerHTML = svgIcon("send");
    sendBtn.setAttribute("aria-label", "Send message");
    sendBtn.addEventListener("click", sendTextMessage);

    inputArea.appendChild(textInput);
    inputArea.appendChild(sendBtn);
    controls.appendChild(micBtn);
    controls.appendChild(inputArea);

    var hint = document.createElement("div");
    hint.className = "va-keyboard-hint";
    hint.textContent = "Space to record \u00B7 Enter to send";

    var footer = document.createElement("div");
    footer.className = "va-footer";
    footer.textContent = "Powered by AgentIQ Voice";

    panel.appendChild(header);
    panel.appendChild(messages);
    panel.appendChild(volumeBar);
    panel.appendChild(typing);
    panel.appendChild(controls);
    panel.appendChild(hint);
    panel.appendChild(footer);

    container.appendChild(bubble);
    container.appendChild(panel);
    document.body.appendChild(container);

    if (!loadSession()) {
      state.sessionId = generateSessionId();
      state.messages = [];
    }
    renderMessages();

    document.addEventListener("keydown", function (e) {
      if (e.code === "Space" && state.isOpen &&
          document.activeElement.tagName !== "INPUT" &&
          document.activeElement.tagName !== "TEXTAREA") {
        e.preventDefault();
        toggleRecording();
      }
    });
  }

  function togglePanel() {
    state.isOpen = !state.isOpen;
    var panel = document.getElementById("va-panel");
    if (panel) panel.classList.toggle("va-open", state.isOpen);
  }

  function renderMessages() {
    var container = document.getElementById("va-messages");
    if (!container) return;
    container.innerHTML = "";
    state.messages.forEach(function (msg) {
      var div = document.createElement("div");
      div.className = "va-msg " + (msg.role === "user" ? "va-user" : "va-agent");
      div.textContent = msg.text;
      container.appendChild(div);
    });
    container.scrollTop = container.scrollHeight;
  }

  function addMessage(role, text) {
    state.messages.push({ role: role, text: text, time: Date.now() });
    renderMessages();
    saveSession();
  }

  function showTyping(show) {
    var el = document.getElementById("va-typing");
    if (el) {
      el.style.display = show ? "block" : "none";
      el.textContent = show ? "Agent is typing..." : "";
    }
  }

  function toggleRecording() {
    if (state.isRecording) stopRecording();
    else startRecording();
  }

  function startRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      addMessage("agent", "Microphone access is not supported in this browser.");
      return;
    }
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      state.audioChunks = [];
      state.mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      state.mediaRecorder.ondataavailable = function (e) {
        if (e.data.size > 0) state.audioChunks.push(e.data);
      };
      state.mediaRecorder.onstop = function () {
        stream.getTracks().forEach(function (t) { t.stop(); });
        var blob = new Blob(state.audioChunks, { type: "audio/webm" });
        sendAudioMessage(blob);
      };
      state.mediaRecorder.start();
      state.isRecording = true;
      updateMicButton(true);
      startVolumeMonitor(stream);
    }).catch(function (err) {
      addMessage("agent", "Could not access microphone: " + err.message);
    });
  }

  function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
      state.mediaRecorder.stop();
      state.isRecording = false;
      updateMicButton(false);
    }
  }

  function updateMicButton(recording) {
    var btn = document.getElementById("va-mic-btn");
    if (btn) btn.className = "va-mic-btn " + (recording ? "va-recording" : "va-idle");
  }

  function startVolumeMonitor(stream) {
    var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    var source = audioCtx.createMediaStreamSource(stream);
    var analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    var dataArray = new Uint8Array(analyser.frequencyBinCount);
    var fill = document.getElementById("va-volume-fill");
    function update() {
      if (!state.isRecording) {
        if (fill) fill.style.width = "0%";
        audioCtx.close();
        return;
      }
      analyser.getByteFrequencyData(dataArray);
      var avg = dataArray.reduce(function (a, b) { return a + b; }, 0) / dataArray.length;
      var pct = Math.min(100, (avg / 128) * 100);
      if (fill) fill.style.width = pct + "%";
      requestAnimationFrame(update);
    }
    update();
  }

  function sendTextMessage() {
    var input = document.getElementById("va-text-input");
    if (!input) return;
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    addMessage("user", text);
    processText(text);
  }

  function sendAudioMessage(audioBlob) {
    state.isLoading = true;
    showTyping(true);
    var formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");
    formData.append("agent_id", state.config.agentId);
    formData.append("session_id", state.sessionId);
    formData.append("language", state.config.language);
    var url = state.config.apiUrl.replace(/\/$/, "") + "/api/v1/voice/process";
    fetch(url, { method: "POST", body: formData }).then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      var text = res.headers.get("X-Transcribed-Text") || "";
      var response = res.headers.get("X-Response-Text") || "";
      if (text) addMessage("user", text);
      if (response) addMessage("agent", response);
      return res.blob();
    }).then(function (blob) {
      playAudio(blob);
    }).catch(function (err) {
      addMessage("agent", "Error: " + err.message);
    }).finally(function () {
      state.isLoading = false;
      showTyping(false);
      saveSession();
    });
  }

  function processText(text) {
    state.isLoading = true;
    showTyping(true);
    var url = state.config.apiUrl.replace(/\/$/, "") + "/api/v1/webhook/agent/" + state.config.agentId;
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, session_id: state.sessionId, language: state.config.language }),
    }).then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    }).then(function (data) {
      var response = data.agent_response || data.response || "";
      if (response) addMessage("agent", response);
    }).catch(function (err) {
      addMessage("agent", "Error: " + err.message);
    }).finally(function () {
      state.isLoading = false;
      showTyping(false);
      saveSession();
    });
  }

  function playAudio(blob) {
    var url = URL.createObjectURL(blob);
    var audio = new Audio(url);
    audio.onended = function () { URL.revokeObjectURL(url); };
    audio.play().catch(function () {});
  }

  function init(opts) {
    state.config = {};
    for (var key in DEFAULTS) {
      state.config[key] = (opts && opts[key] !== undefined) ? opts[key] : DEFAULTS[key];
    }
    if (!state.config.agentId) {
      console.error("[VoiceAgentWidget] agentId is required");
      return;
    }
    createStyles();
    buildWidget();
    console.log("[VoiceAgentWidget] v" + VERSION + " initialized");
  }

  function destroy() {
    var el = document.getElementById("voiceagent-widget");
    if (el) el.remove();
    state.isOpen = false;
    state.isRecording = false;
  }

  window.VoiceAgentWidget = { init: init, destroy: destroy };
})();
