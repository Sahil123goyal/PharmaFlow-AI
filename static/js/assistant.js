/* Customer voice/chat: no background listening, audio upload or stored history. */
(function () {
  "use strict";
  const root = document.querySelector("[data-assistant]");
  if (!root) return;
  const get = (selector) => root.querySelector(selector);
  const panel = get("#assistant-panel"), toggle = get("[data-assistant-toggle]");
  const input = get("[data-input]"), form = get("[data-assistant-form]");
  const messages = get("[data-messages]"), status = get("[data-status]");
  const language = get("[data-language]"), mic = get("[data-mic]");
  const read = get("[data-read-aloud]"), stopAudio = get("[data-stop-audio]");
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const synthesis = window.speechSynthesis;
  let recognition = null, listening = false, controller = null, generation = 0;
  const copy = {
    "en-IN": {
      title: "Voice assistant", read: "Read replies aloud", clear: "Clear chat",
      mic: "Start microphone", listening: "Stop microphone", stop: "Stop audio",
      ready: "Ready. Type a medicine name or use the microphone.",
      unsupported: "Voice input isn't supported here. You can still type your question.",
      welcome: "Hello! I can find medicines and prescription flags in our catalogue. Say or type a medicine name to begin. Ask the pharmacist for medical advice.",
      placeholder: "Type a medicine name…", working: "Looking in the catalogue…",
      recording: "Listening… Speak a medicine name. Tap Stop when finished.",
      review: "Review the words in the message box, then press Send.",
      noSpeech: "No speech detected. Try again or type your question.",
      denied: "Microphone access was denied. Allow it in browser settings or type instead.",
      voiceError: "Voice input is unavailable. Check your microphone and connection, or type instead.",
      error: "I couldn't connect. Your message is still in the box; please try again.",
      session: "Your session has ended. Sign in again to use the assistant.",
      speaking: "Reading reply aloud…", speechError: "Audio couldn't play. Please read the reply above.",
      note: "Catalogue help, not medical advice. Voice may use your browser’s online speech service. Review the transcript before sending. Chat stays on this page only.",
      prescription: "Prescription help", find: "Find Crocin", report: "Catalogue report", openReport: "Open full catalogue report"
    },
    "hi-IN": {
      title: "वॉइस असिस्टेंट", read: "जवाब सुनें", clear: "चैट मिटाएं",
      mic: "माइक शुरू करें", listening: "माइक बंद करें", stop: "आवाज़ बंद करें",
      ready: "तैयार। दवा का नाम लिखें या माइक का उपयोग करें।",
      unsupported: "यहाँ आवाज़ से सवाल पूछना उपलब्ध नहीं है। आप सवाल लिख सकते हैं।",
      welcome: "नमस्ते! मैं सूची में दवा और प्रिस्क्रिप्शन की जानकारी खोज सकता हूँ। दवा का नाम बोलें या लिखें। चिकित्सा सलाह के लिए फार्मासिस्ट से बात करें।",
      placeholder: "दवा का नाम लिखें…", working: "दवा की सूची में खोज रहा हूँ…",
      recording: "सुन रहा हूँ… दवा का नाम बोलें। पूरा होने पर माइक बंद करें।",
      review: "लिखे गए शब्द जांचें, फिर भेजें बटन दबाएं।",
      noSpeech: "आवाज़ सुनाई नहीं दी। फिर कोशिश करें या सवाल लिखें।",
      denied: "माइक की अनुमति नहीं मिली। ब्राउज़र सेटिंग में अनुमति दें या सवाल लिखें।",
      voiceError: "आवाज़ से सवाल उपलब्ध नहीं है। माइक और इंटरनेट जांचें या सवाल लिखें।",
      error: "संपर्क नहीं हो सका। आपका सवाल बॉक्स में है; फिर कोशिश करें।",
      session: "आपका सत्र समाप्त हो गया। सहायक के लिए फिर साइन इन करें।",
      speaking: "जवाब पढ़ रहा हूँ…", speechError: "आवाज़ नहीं चल सकी। ऊपर लिखा जवाब पढ़ें।",
      note: "यह सूची की जानकारी है, चिकित्सा सलाह नहीं। आवाज़ के लिए ब्राउज़र की ऑनलाइन सेवा इस्तेमाल हो सकती है। भेजने से पहले शब्द जांचें। चैट केवल इस पेज पर रहती है।",
      prescription: "प्रिस्क्रिप्शन की मदद", find: "क्रोसिन खोजें", report: "दवाओं की रिपोर्ट", openReport: "दवाओं की पूरी रिपोर्ट खोलें"
    }
  };
  const words = () => copy[language.value];
  const ready = () => words()[Recognition && window.isSecureContext ? "ready" : "unsupported"];
  function add(text, role, lang = language.value) {
    const item = document.createElement("p");
    item.className = "chatbot__message chatbot__message--" + role;
    item.lang = lang; item.textContent = text;
    messages.appendChild(item);
    while (messages.children.length > 40) messages.firstElementChild.remove();
    messages.scrollTop = messages.scrollHeight;
    return item;
  }
  function stopSpeaking() {
    if (synthesis) synthesis.cancel();
    stopAudio.disabled = true;
  }
  function stopListening() {
    if (recognition) {
      const old = recognition; recognition = null; old.abort();
    }
    listening = false; mic.setAttribute("aria-pressed", "false");
    mic.textContent = words().mic;
  }
  function busy(value) {
    get("[data-send]").disabled = value;
    input.disabled = value;
    language.disabled = value;
    mic.disabled = value || !Recognition || !window.isSecureContext;
    root.querySelectorAll("[data-prompt]").forEach((button) => { button.disabled = value; });
    messages.setAttribute("aria-busy", String(value));
  }
  function cancelRequest() {
    generation += 1;
    if (controller) controller.abort();
    controller = null; busy(false);
  }
  function close() {
    stopListening(); stopSpeaking(); cancelRequest();
    panel.hidden = true; toggle.setAttribute("aria-expanded", "false"); toggle.focus();
  }
  function translate() {
    const t = words(); panel.lang = language.value;
    get("#assistant-title").textContent = t.title;
    get("[data-copy=read]").textContent = t.read;
    get("[data-clear]").textContent = t.clear;
    mic.textContent = t.mic; stopAudio.textContent = t.stop;
    input.placeholder = t.placeholder; get("[data-note]").textContent = t.note;
    get("[data-prompt=Crocin]").textContent = t.find;
    get("[data-prompt=prescription]").textContent = t.prescription;
    get("[data-prompt=catalogue]").textContent = t.report;
    get("[data-send]").setAttribute("aria-label", language.value === "hi-IN" ? "संदेश भेजें" : "Send message");
    status.textContent = ready();
  }
  function speak(text, lang) {
    if (!read.checked || !synthesis || panel.hidden) return;
    stopSpeaking();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    const voice = synthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith(lang.slice(0, 2)));
    if (voice) utterance.voice = voice;
    utterance.onstart = () => { stopAudio.disabled = false; status.textContent = words().speaking; };
    utterance.onend = () => { stopAudio.disabled = true; status.textContent = ready(); };
    utterance.onerror = (event) => {
      stopAudio.disabled = true;
      if (!['canceled', 'interrupted'].includes(event.error)) status.textContent = words().speechError;
    };
    stopAudio.disabled = false;
    synthesis.speak(utterance);
  }
  toggle.addEventListener("click", () => {
    if (!panel.hidden) { close(); return; }
    panel.hidden = false; toggle.setAttribute("aria-expanded", "true");
    status.textContent = ready(); input.focus();
  });
  get("[data-assistant-close]").addEventListener("click", close);
  root.addEventListener("keydown", (event) => { if (event.key === "Escape" && !panel.hidden) close(); });
  stopAudio.addEventListener("click", () => { stopSpeaking(); status.textContent = ready(); });
  read.disabled = !synthesis || !window.SpeechSynthesisUtterance;
  read.addEventListener("change", () => { if (!read.checked) { stopSpeaking(); status.textContent = ready(); } });
  language.addEventListener("change", () => { stopListening(); stopSpeaking(); translate(); add(words().welcome, "assistant"); });
  get("[data-clear]").addEventListener("click", () => {
    stopListening(); stopSpeaking(); cancelRequest(); messages.replaceChildren(); input.value = "";
    add(words().welcome, "assistant"); status.textContent = ready(); input.focus();
  });
  mic.addEventListener("click", () => {
    if (listening && recognition) { recognition.stop(); return; }
    if (!Recognition || controller) return;
    stopSpeaking();
    const session = new Recognition(); recognition = session;
    session.lang = language.value; session.interimResults = true; session.continuous = false;
    let resultReceived = false, failed = false;
    listening = true; mic.setAttribute("aria-pressed", "true"); mic.textContent = words().listening;
    status.textContent = words().recording;
    session.onresult = (event) => {
      if (recognition !== session) return;
      input.value = Array.from(event.results).map((result) => result[0].transcript).join(" ").slice(0, 500);
      resultReceived = true;
    };
    session.onerror = (event) => {
      if (recognition !== session) return;
      failed = true;
      status.textContent = words()[event.error === "not-allowed" || event.error === "service-not-allowed" ? "denied" : event.error === "no-speech" ? "noSpeech" : "voiceError"];
    };
    session.onend = () => {
      if (recognition !== session) return;
      recognition = null; listening = false; mic.setAttribute("aria-pressed", "false"); mic.textContent = words().mic;
      if (!failed) status.textContent = words()[resultReceived ? "review" : "noSpeech"];
      input.focus();
    };
    try { session.start(); } catch (error) { stopListening(); status.textContent = words().voiceError; }
  });
  root.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => {
    input.value = button.dataset.prompt === "catalogue" ? (language.value === "hi-IN" ? "दवाओं की रिपोर्ट" : "medicine catalogue report") : button.dataset.prompt === "prescription" ? (language.value === "hi-IN" ? "प्रिस्क्रिप्शन" : "prescription") : "Crocin";
    form.requestSubmit();
  }));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim(), lang = language.value;
    if (!message || message.length > 500 || controller) return;
    stopListening(); stopSpeaking();
    add(message, "user"); busy(true); status.textContent = words().working;
    const request = new AbortController(); controller = request;
    const current = ++generation;
    const timeout = window.setTimeout(() => request.abort(), 15000);
    try {
      const response = await fetch(root.dataset.endpoint, {
        method: "POST", credentials: "same-origin", signal: request.signal,
        headers: {"Content-Type": "application/json", "X-CSRFToken": form.querySelector('[name=csrfmiddlewaretoken]').value},
        body: JSON.stringify({message, language: lang})
      });
      if (current !== generation) return;
      if (response.status === 401 || response.status === 403) throw new Error("session");
      if (!response.ok) throw new Error("network");
      const data = await response.json();
      if (current !== generation) return;
      if (typeof data.reply !== "string") throw new Error("network");
      input.value = "";
      const reply = add(data.reply, "assistant", lang);
      if (data.report_url && data.report_url === root.dataset.reportUrl) {
        const link = document.createElement("a");
        link.href = root.dataset.reportUrl; link.className = "assistant-report-link";
        link.textContent = copy[lang].openReport; reply.appendChild(link);
        messages.scrollTop = messages.scrollHeight;
      }
      status.textContent = ready(); speak(data.reply, lang);
    } catch (error) {
      if (current === generation) { status.textContent = words()[error.message === "session" ? "session" : "error"]; }
    } finally {
      window.clearTimeout(timeout);
      if (current === generation) { controller = null; busy(false); if (!panel.hidden) input.focus(); }
    }
  });
  document.addEventListener("visibilitychange", () => { if (document.hidden) { stopListening(); stopSpeaking(); } });
  window.addEventListener("pagehide", () => { stopListening(); stopSpeaking(); cancelRequest(); });
  translate(); busy(false); add(words().welcome, "assistant");
})();
