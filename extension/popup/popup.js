const toggleBtn = document.getElementById("toggleBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const tabInfo = document.getElementById("tabInfo");
const captionCountDiv = document.getElementById("captionCount");
const lineCountSpan = document.getElementById("lineCount");

let isRecording = false;
let pollInterval = null;
let activeTabId = null;

// Detect the active tab
try {
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    if (tabs && tabs[0]) {
      activeTabId = tabs[0].id;
      const url = tabs[0].url || "";
      const title = tabs[0].title || "Unknown Tab";
      if (url.includes("meet.google.com")) {
        tabInfo.textContent = "✅ Google Meet detected: " + title;
        tabInfo.style.color = "#059669";
      } else {
        tabInfo.textContent = "⚠️ Not on Google Meet. Open meet.google.com first.";
        tabInfo.style.color = "#dc2626";
      }
    }
  });
} catch (e) {
  tabInfo.textContent = "Tab detection unavailable";
}

// Check if already recording
try {
  chrome.storage.local.get(["isRecording", "captionCount"], function(result) {
    if (result && result.isRecording) {
      setRecordingUI();
      startCountPolling();
    }
    if (result && result.captionCount) {
      lineCountSpan.textContent = result.captionCount;
    }
  });
} catch (e) {}

// BUTTON CLICK
toggleBtn.addEventListener("click", function() {
  if (!isRecording) {
    startCapture();
  } else {
    stopCapture();
  }
});

function startCapture() {
  isRecording = true;
  setRecordingUI();

  chrome.storage.local.set({ isRecording: true, captionCount: 0 });

  // FORCE-INJECT the content script into the active tab
  // This is the key fix — no need to refresh the page!
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    if (!tabs || !tabs[0]) return;
    activeTabId = tabs[0].id;

    chrome.scripting.executeScript({
      target: { tabId: activeTabId },
      files: ["content.js"]
    }, function(results) {
      if (chrome.runtime.lastError) {
        console.log("Injection error:", chrome.runtime.lastError.message);
        // Try alternative: inject inline code directly
        injectInlineScript(activeTabId);
      } else {
        console.log("Content script injected successfully!");
        // Tell it to start
        setTimeout(function() {
          chrome.tabs.sendMessage(activeTabId, { action: "START_CAPTION_SCRAPE" }, function() {
            if (chrome.runtime.lastError) {
              console.log("Message error, trying inline inject...");
              injectInlineScript(activeTabId);
            }
          });
        }, 500);
      }
    });
  });

  // Also notify background
  try {
    chrome.runtime.sendMessage({ action: "START_CAPTURE", title: tabInfo.textContent });
  } catch (e) {}

  startCountPolling();
}

function injectInlineScript(tabId) {
  // Fallback: inject the caption scraping logic directly as inline code
  chrome.scripting.executeScript({
    target: { tabId: tabId },
    func: inlineCaptionScraper,
    world: "MAIN"
  }, function() {
    if (chrome.runtime.lastError) {
      console.log("Inline injection also failed:", chrome.runtime.lastError.message);
    } else {
      console.log("Inline caption scraper injected!");
    }
  });
}

// This function gets injected directly into the page
function inlineCaptionScraper() {
  if (window.__smartmeetRunning) return;
  window.__smartmeetRunning = true;
  
  console.log("[SmartMeet AI] Inline scraper active!");
  
  let seenTexts = new Set();
  let lineCount = 0;
  
  setInterval(function() {
    // Get ALL text on the page
    var fullText = document.body.innerText || "";
    var lines = fullText.split("\n").map(function(l) { return l.trim(); }).filter(function(l) { return l.length > 8; });
    
    lines.forEach(function(line) {
      if (seenTexts.has(line)) return;
      
      // Skip UI elements
      var skipWords = ["Meet", "Present", "Raise hand", "Turn on", "Turn off", "Share screen",
                       "Meeting details", "People", "Chat", "Activities", "Captions", "SmartMeet",
                       "caption lines", "Capturing", "Start Tab", "Stop &", "Dashboard",
                       "Important:", "for best", "Google Meet detected", "Ready to"];
      var isUI = false;
      for (var i = 0; i < skipWords.length; i++) {
        if (line.indexOf(skipWords[i]) !== -1) { isUI = true; break; }
      }
      if (isUI) return;
      
      // Check if this looks like spoken text (has multiple words, has punctuation)
      var wordCount = line.split(/\s+/).length;
      if (wordCount < 3) return;
      
      seenTexts.add(line);
      lineCount++;
      
      console.log("[SmartMeet AI] CAPTURED: " + line);
      
      // Send to backend
      try {
        fetch("http://127.0.0.1:8000/api/live-captions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ speaker: "Participant", text: line, timestamp: new Date().toISOString() })
        }).catch(function() {});
      } catch (e) {}
      
      // Store count in page for popup to read
      document.title = document.title.replace(/\[SM:\d+\]/, "") + "[SM:" + lineCount + "]";
    });
  }, 1000);
}

function stopCapture() {
  isRecording = false;
  setIdleUI();
  stopCountPolling();
  chrome.storage.local.set({ isRecording: false });

  try {
    chrome.runtime.sendMessage({ action: "STOP_CAPTURE" }, function(res) {
      if (res && res.line_count > 0) {
        alert("Captured " + res.line_count + " lines!\nCheck http://127.0.0.1:3000");
      }
    });
  } catch (e) {}
}

function startCountPolling() {
  if (pollInterval) return;
  captionCountDiv.style.display = "block";
  
  pollInterval = setInterval(function() {
    // Method 1: Ask background for count
    try {
      chrome.runtime.sendMessage({ action: "GET_STATUS" }, function(response) {
        if (chrome.runtime.lastError) return;
        if (response && response.lineCount > 0) {
          lineCountSpan.textContent = response.lineCount;
          chrome.storage.local.set({ captionCount: response.lineCount });
        }
      });
    } catch (e) {}
    
    // Method 2: Check the tab title for [SM:N] marker
    try {
      chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        if (tabs && tabs[0]) {
          var title = tabs[0].title || "";
          var match = title.match(/\[SM:(\d+)\]/);
          if (match) {
            var count = parseInt(match[1]);
            if (count > 0) {
              lineCountSpan.textContent = count;
            }
          }
        }
      });
    } catch (e) {}
  }, 2000);
}

function stopCountPolling() {
  captionCountDiv.style.display = "none";
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
}

function setRecordingUI() {
  isRecording = true;
  statusDot.className = "status-dot active";
  statusText.textContent = "Capturing live captions...";
  toggleBtn.textContent = "Stop & Process Meeting";
  toggleBtn.className = "btn btn-stop";
}

function setIdleUI() {
  isRecording = false;
  statusDot.className = "status-dot";
  statusText.textContent = "Ready to Capture";
  toggleBtn.textContent = "Start Tab Capture";
  toggleBtn.className = "btn btn-primary";
}
