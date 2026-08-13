// SmartMeet AI Background Service Worker

let isRecording = false;
let currentMeetingTitle = "Google Meet Session";
let captionLineCount = 0;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "START_CAPTURE") {
    isRecording = true;
    captionLineCount = 0;
    currentMeetingTitle = message.title || "Live Meeting";
    chrome.storage.local.set({ isRecording: true, title: currentMeetingTitle });

    // Tell ALL meet.google.com tabs to start scraping
    chrome.tabs.query({ url: "https://meet.google.com/*" }, (tabs) => {
      tabs.forEach(tab => {
        chrome.tabs.sendMessage(tab.id, { action: "START_CAPTION_SCRAPE" }, () => {
          // Ignore errors for tabs where content script isn't loaded
          if (chrome.runtime.lastError) {
            console.log('[SmartMeet BG] Content script not ready on tab:', tab.id);
          }
        });
      });
    });

    sendResponse({ status: "started", title: currentMeetingTitle });

  } else if (message.action === "STOP_CAPTURE") {
    isRecording = false;
    chrome.storage.local.set({ isRecording: false });

    // Get captions from ALL meet tabs
    chrome.tabs.query({ url: "https://meet.google.com/*" }, (tabs) => {
      let allLines = [];
      let pending = tabs.length;

      if (pending === 0) {
        sendResponse({ status: "stopped", lines: [], line_count: 0 });
        return;
      }

      tabs.forEach(tab => {
        chrome.tabs.sendMessage(tab.id, { action: "STOP_CAPTION_SCRAPE" }, (res) => {
          if (res && res.lines) {
            allLines = allLines.concat(res.lines);
          }
          pending--;
          if (pending === 0) {
            const fullTranscript = allLines.join('\n');
            
            // Try to send to backend for processing
            fetch("http://127.0.0.1:8000/api/orchestrate", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                title: currentMeetingTitle + " (Google Meet Capture)",
                transcript: fullTranscript,
                mode: "extension"
              })
            })
            .then(r => r.json())
            .then(data => {
              sendResponse({ status: "processed", pipeline_result: data, line_count: allLines.length });
            })
            .catch(() => {
              sendResponse({ status: "captured", lines: allLines, line_count: allLines.length });
            });
          }
          
          if (chrome.runtime.lastError) {}
        });
      });
    });

    return true; // Keep channel open for async response

  } else if (message.action === "GET_STATUS") {
    sendResponse({ isRecording, title: currentMeetingTitle, lineCount: captionLineCount });

  } else if (message.action === "CAPTION_LINE") {
    // Individual line received from content script
    if (message.line) {
      captionLineCount++;
    }
    sendResponse({ status: "received", count: captionLineCount });
  }

  return true;
});
