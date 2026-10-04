// SmartMeet AI — Google Meet Caption Extractor v3
// Brute force: scans ALL visible text on page every second

(function() {
  if (window.__smartmeetLoaded) return;
  window.__smartmeetLoaded = true;

  console.log("[SmartMeet AI] ====== CONTENT SCRIPT LOADED ======");
  console.log("[SmartMeet AI] URL:", window.location.href);

  var seenTexts = new Set();
  var captionBuffer = [];
  var lineCount = 0;
  var scanning = true;

  // Listen for commands
  try {
    chrome.runtime.onMessage.addListener(function(message, sender, sendResponse) {
      console.log("[SmartMeet AI] Received message:", message.action);
      if (message.action === "START_CAPTION_SCRAPE") {
        scanning = true;
        captionBuffer = [];
        seenTexts = new Set();
        lineCount = 0;
        sendResponse({ status: "started" });
      } else if (message.action === "STOP_CAPTION_SCRAPE") {
        scanning = false;
        sendResponse({ status: "stopped", lines: captionBuffer.slice() });
      } else if (message.action === "GET_CAPTIONS") {
        var lines = captionBuffer.slice();
        captionBuffer = [];
        sendResponse({ lines: lines });
      }
      return true;
    });
  } catch (e) {
    console.log("[SmartMeet AI] Message listener error:", e);
  }

  // Main scanning loop — runs every 1 second
  setInterval(function() {
    if (!scanning) return;
    
    try {
      scanAllText();
    } catch (e) {
      console.warn("[SmartMeet AI] Scan error:", e);
    }
  }, 1000);

  function scanAllText() {
    // 1. Direct DOM Selector Scan for Google Meet Captions (100% High Precision)
    var domCaptionsFound = false;
    try {
      var captionBlocks = document.querySelectorAll('.T4LgNc, .aGsWq, [jsname="YSZttd"]');
      if (captionBlocks && captionBlocks.length > 0) {
        captionBlocks.forEach(function(block) {
          var spkElem = block.querySelector('.zsT3Me, [data-sender-name], .sub-title');
          var txtElem = block.querySelector('.iT2bBf, .VfPpkd-Bz112c-LgfdBc');
          var speaker = spkElem ? (spkElem.innerText || spkElem.textContent || "").trim() : "";
          var text = txtElem ? (txtElem.innerText || txtElem.textContent || "").trim() : "";

          if (text && text.length > 2) {
            var lineKey = (speaker || "Participant") + ": " + text;
            if (!seenTexts.has(lineKey)) {
              seenTexts.add(lineKey);
              domCaptionsFound = true;
              var cleanSpeaker = speaker || "Participant";
              captionBuffer.push(lineKey);
              lineCount++;
              sendToBackend(cleanSpeaker, text);
            }
          }
        });
      }
    } catch (err) {
      console.warn("[SmartMeet AI] DOM selector error:", err);
    }

    // 2. Fallback Page Text Scanner if specific DOM selectors are not active
    if (domCaptionsFound) return;

    var fullText = document.body.innerText || document.body.textContent || "";
    var allLines = fullText.split("\n");
    
    for (var i = 0; i < allLines.length; i++) {
      var line = allLines[i].trim();
      if (line.length < 5) continue;
      if (seenTexts.has(line)) continue;
      if (isGoogleMeetUI(line)) continue;
      
      var words = line.split(/\s+/);
      if (words.length < 2) continue;
      
      seenTexts.add(line);
      
      var speaker = "Participant";
      if (i > 0) {
        var prevLine = allLines[i - 1].trim();
        if (prevLine.length >= 2 && prevLine.length <= 35 && !isGoogleMeetUI(prevLine)) {
          speaker = prevLine;
          seenTexts.add(prevLine);
        }
      }
      
      var captionLine = speaker + ": " + line;
      captionBuffer.push(captionLine);
      lineCount++;
      
      console.log("[SmartMeet AI] ✅ LINE " + lineCount + ": " + captionLine);
      sendToBackend(speaker, line);
    }
  }

  function isGoogleMeetUI(text) {
    // Comprehensive list of Google Meet UI strings to skip
    var uiStrings = [
      "Meet", "Present now", "Raise hand", "Turn on", "Turn off",
      "Share screen", "Meeting details", "People", "Chat", "Activities",
      "Captions", "SmartMeet", "caption lines", "Capturing", "Start Tab",
      "Stop &", "Dashboard", "Important:", "for best", "Google Meet detected",
      "Ready to", "You're presenting", "Ask to join", "Admit", "Deny",
      "Pin", "Unpin", "Mute", "Remove", "View in", "Add others",
      "Contributors", "Meeting host", "Apply visual", "End call",
      "Cancel", "Settings", "What's new", "Reaction", "All Bookmarks",
      "Extensions", "More options", "Leave call", "participants",
      "Your meeting", "Check your", "camera", "microphone",
      "spp-", "meet.google", "Loading", "Joining", "Ready to join",
      "Open Dashboard", "Tab Capture", "Process Meeting",
      "Looks like you", "No one else", "waiting", "joining",
      "You've been removed", "call ended", "Rejoin",
      "google.com", "Chrome Web Store"
    ];
    
    for (var j = 0; j < uiStrings.length; j++) {
      if (text.indexOf(uiStrings[j]) !== -1) return true;
    }
    
    // Skip single words that are likely UI labels
    if (text.split(/\s+/).length === 1 && text.length < 15) return true;
    
    // Skip timestamps like "00:23"
    if (/^\d{1,2}:\d{2}/.test(text)) return true;
    
    return false;
  }

  function sendToBackend(speaker, text) {
    try {
      var xhr = new XMLHttpRequest();
      xhr.open("POST", "http://127.0.0.1:8000/api/live-captions", true);
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.send(JSON.stringify({
        speaker: speaker,
        text: text,
        timestamp: new Date().toISOString()
      }));
    } catch (e) {
      // Backend might not be running
    }
  }

  // Initial log to confirm script is active
  console.log("[SmartMeet AI] Scanner active. Monitoring for captions...");
  console.log("[SmartMeet AI] Page text length:", (document.body.innerText || "").length, "chars");
})();
