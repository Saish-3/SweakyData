// Frontend Application Logic for Gemma 4 Studio
document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const statusBadge = document.getElementById("statusBadge");
  const statusText = document.getElementById("statusText");
  const modelSelect = document.getElementById("modelSelect");
  const apiKeyBanner = document.getElementById("apiKeyBanner");
  const promptInput = document.getElementById("promptInput");
  const charCount = document.getElementById("charCount");
  const clearBtn = document.getElementById("clearBtn");
  const sendBtn = document.getElementById("sendBtn");
  const latencyTag = document.getElementById("latencyTag");
  const activeModelTag = document.getElementById("activeModelTag");
  const loadingState = document.getElementById("loadingState");
  const emptyState = document.getElementById("emptyState");
  const errorState = document.getElementById("errorState");
  const errorTitle = document.getElementById("errorTitle");
  const errorMessage = document.getElementById("errorMessage");
  const retryBtn = document.getElementById("retryBtn");
  const responseContent = document.getElementById("responseContent");
  const responseBody = document.getElementById("responseBody");
  const copyBtn = document.getElementById("copyBtn");
  const copyText = document.getElementById("copyText");
  const chipButtons = document.querySelectorAll(".chip-btn");

  let lastPrompt = "";

  // 1. Initial Status Check
  async function checkBackendStatus() {
    try {
      const res = await fetch("/api/status");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      statusBadge.classList.remove("checking", "ready", "warning", "error");

      if (data.api_key_configured) {
        statusBadge.classList.add("ready");
        statusText.textContent = "Gemma 4 Online";
        apiKeyBanner.classList.add("hidden");
      } else {
        statusBadge.classList.add("warning");
        statusText.textContent = "API Key Missing";
        apiKeyBanner.classList.remove("hidden");
      }

      if (data.default_model) {
        activeModelTag.textContent = data.default_model;
        if (modelSelect.querySelector(`option[value="${data.default_model}"]`)) {
          modelSelect.value = data.default_model;
        }
      }
    } catch (err) {
      statusBadge.classList.remove("checking", "ready", "warning");
      statusBadge.classList.add("error");
      statusText.textContent = "Backend Offline";
    }
  }

  // 2. Character Count and Auto-grow
  promptInput.addEventListener("input", () => {
    charCount.textContent = promptInput.value.length;
  });

  // 3. Clear Button
  clearBtn.addEventListener("click", () => {
    promptInput.value = "";
    charCount.textContent = "0";
    promptInput.focus();
  });

  // 4. Prompt Chips
  chipButtons.forEach((chip) => {
    chip.addEventListener("click", () => {
      const promptText = chip.getAttribute("data-prompt");
      if (promptText) {
        promptInput.value = promptText;
        charCount.textContent = promptText.length;
        promptInput.focus();
      }
    });
  });

  // 5. Model Selection Change
  modelSelect.addEventListener("change", () => {
    activeModelTag.textContent = modelSelect.value;
  });

  // 6. Keyboard Shortcut (Cmd+Enter or Ctrl+Enter)
  promptInput.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      executePrompt();
    }
  });

  sendBtn.addEventListener("click", () => executePrompt());
  retryBtn.addEventListener("click", () => {
    if (lastPrompt) {
      promptInput.value = lastPrompt;
      executePrompt();
    }
  });

  // 7. Execute Prompt Request
  async function executePrompt() {
    const prompt = promptInput.value.trim();
    if (!prompt) {
      promptInput.focus();
      return;
    }

    lastPrompt = prompt;
    const selectedModel = modelSelect.value;
    activeModelTag.textContent = selectedModel;

    // UI state: Loading
    setLoading(true);

    try {
      const startTime = performance.now();
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: prompt,
          model: selectedModel,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Server returned error (${response.status})`);
      }

      // Success
      renderResponse(data.response, data.latency_ms || Math.round(performance.now() - startTime));
    } catch (err) {
      renderError("Generation Failed", err.message);
    } finally {
      setLoading(false);
    }
  }

  function setLoading(isLoading) {
    sendBtn.disabled = isLoading;
    if (isLoading) {
      emptyState.classList.add("hidden");
      errorState.classList.add("hidden");
      responseContent.classList.add("hidden");
      loadingState.classList.remove("hidden");
    } else {
      loadingState.classList.add("hidden");
    }
  }

  function renderResponse(text, latency) {
    emptyState.classList.add("hidden");
    errorState.classList.add("hidden");
    responseContent.classList.remove("hidden");

    responseBody.textContent = text;

    if (latency) {
      latencyTag.textContent = `⚡ ${latency}ms`;
      latencyTag.classList.remove("hidden");
    }
  }

  function renderError(title, message) {
    emptyState.classList.add("hidden");
    responseContent.classList.add("hidden");
    errorState.classList.remove("hidden");

    errorTitle.textContent = title;
    errorMessage.textContent = message;
  }

  // 8. Copy to Clipboard
  copyBtn.addEventListener("click", async () => {
    const textToCopy = responseBody.textContent;
    if (!textToCopy) return;

    try {
      await navigator.clipboard.writeText(textToCopy);
      copyText.textContent = "Copied!";
      setTimeout(() => {
        copyText.textContent = "Copy";
      }, 2000);
    } catch (err) {
      copyText.textContent = "Failed";
    }
  });

  // Run initial check
  checkBackendStatus();
});
