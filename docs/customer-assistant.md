# Voice assistant

Available through **Voice assistant** on all signed-in app pages. Select
English or Hindi. Start the microphone, review the transcript, then send it.
Enable **Read replies aloud** for spoken replies. Stop audio, close, or leave the
page to stop playback; closing or hiding the page also stops the microphone.

The assistant uses deterministic catalogue lookup, not a generative AI model.
No API key or paid service is configured. It searches active medicine names and
generic names, shows prescription flags, and routes medical questions to a
pharmacist. A small alias dictionary supports common Hindi medicine names;
unrecognized names can be entered using the English name on the pack. Replies
do not claim live stock, prices, treatment suitability, or completed orders.
No store sales, supplier, or customer records are returned.

Ask for a **medicine catalogue report**, **show all medicines**, or **दवाओं की
रिपोर्ट** to get live catalogue counts and a link to the full signed-in report.
The report includes active and inactive records, a category breakdown, printable
layout, and a CSV download. The Medicines page also has a Catalogue report link.

Browser voice input uses `SpeechRecognition`/`webkitSpeechRecognition` and
output uses `speechSynthesis`. Support and installed Hindi voices vary by browser
and device. Microphone permission and localhost or HTTPS are required. Some
browsers send audio to their online speech provider, which may require internet.
The UI discloses this before starting voice input. The Django app receives only
the submitted transcript and does not persist chat history or audio. Conversation
messages stay in page memory and are cleared on navigation/reload or Clear chat.
Text entry stays available when speech support or permission is unavailable.

Reference: [MDN SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition).

Validation:

```powershell
py -3.13 manage.py test apps.core apps.accounts apps.medicines --noinput
node tests/assistant.test.cjs
```

The JavaScript tests simulate speech events, denied access, cancelled requests,
and read-aloud settings without capturing microphone audio. Real microphone
transcription and audible output must also be checked on the customer's browser.
