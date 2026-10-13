// Exercise voice state transitions without opening the user's microphone.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/js/assistant.js'), 'utf8');

function setup({supported = true, fetchImpl} = {}) {
  class Element {
    constructor() { this.listeners = {}; this.children = []; this.dataset = {}; this.value = ''; this.attrs = {}; this.disabled = false; }
    addEventListener(name, handler) { this.listeners[name] = handler; }
    emit(name, event = {}) { return this.listeners[name]?.({preventDefault() {}, ...event}); }
    setAttribute(name, value) { this.attrs[name] = value; }
    appendChild(item) { this.children.push(item); }
    replaceChildren() { this.children = []; }
    focus() {}
  }
  const elements = new Map();
  const get = (selector) => {
    if (!elements.has(selector)) elements.set(selector, new Element());
    return elements.get(selector);
  };
  const root = get('[data-assistant]');
  const prompts = ['Crocin', 'prescription', 'catalogue'].map((value) => {
    const item = get(`[data-prompt=${value}]`); item.dataset.prompt = value; return item;
  });
  root.querySelector = get;
  root.querySelectorAll = () => prompts;
  root.dataset.endpoint = '/chat/';
  root.dataset.reportUrl = '/reports/medicine-catalogue/';
  const form = get('[data-assistant-form]');
  form.querySelector = get; form.requestSubmit = () => form.emit('submit');
  get('[name=csrfmiddlewaretoken]').value = 'csrf-test';
  get('[data-language]').value = 'en-IN';
  get('#assistant-panel').hidden = false;
  const document = {querySelector: get, createElement: () => new Element(), addEventListener() {}};
  const sessions = [], spoken = [], requests = [];
  class Recognition {
    constructor() { sessions.push(this); }
    start() { this.started = true; }
    stop() { this.onend?.(); }
    abort() { this.aborted = true; this.onend?.(); }
  }
  const window = {
    isSecureContext: true, SpeechRecognition: supported ? Recognition : undefined,
    SpeechSynthesisUtterance: function(text) {this.text = text;},
    speechSynthesis: {cancel() {}, getVoices: () => [], speak(item) { spoken.push(item); item.onstart(); }},
    setTimeout, clearTimeout, addEventListener() {}
  };
  const fetch = async (url, options) => {
    requests.push({url, options});
    return fetchImpl ? fetchImpl(url, options) : {ok: true, status: 200, json: async () => ({reply: 'Catalogue result'})};
  };
  vm.runInNewContext(source, {document, window, SpeechSynthesisUtterance: window.SpeechSynthesisUtterance, AbortController, fetch});
  return {get, sessions, requests, spoken};
}

test('unsupported voice leaves text chat usable', async () => {
  const f = setup({supported: false});
  assert.equal(f.get('[data-mic]').disabled, true);
  assert.match(f.get('[data-status]').textContent, /isn't supported/);
  f.get('[data-input]').value = 'Crocin';
  await f.get('[data-assistant-form]').emit('submit');
  assert.equal(f.requests.length, 1);
  assert.equal(f.get('[data-input]').disabled, false);
});

test('speech creates a reviewable transcript without sending it', async () => {
  const f = setup();
  f.get('[data-language]').value = 'hi-IN';
  f.get('[data-language]').emit('change');
  f.get('[data-mic]').emit('click');
  const session = f.sessions[0];
  assert.equal(session.lang, 'hi-IN');
  session.onresult({results: [[{transcript: 'पैरासिटामोल'}]]});
  session.onend();
  assert.equal(f.requests.length, 0);
  assert.equal(f.get('[data-input]').value, 'पैरासिटामोल');
  await f.get('[data-assistant-form]').emit('submit');
  assert.equal(JSON.parse(f.requests[0].options.body).language, 'hi-IN');
  assert.equal(f.requests[0].options.headers['X-CSRFToken'], 'csrf-test');
});

test('denied permission shows fallback and releases recording state', () => {
  const f = setup(); f.get('[data-mic]').emit('click');
  f.sessions[0].onerror({error: 'not-allowed'}); f.sessions[0].onend();
  assert.match(f.get('[data-status]').textContent, /denied/);
  assert.equal(f.get('[data-mic]').attrs['aria-pressed'], 'false');
  assert.equal(f.get('[data-input]').disabled, false);
});

test('closing aborts recording and ignores late transcript events', () => {
  const f = setup(); f.get('[data-mic]').emit('click');
  f.get('[data-assistant-close]').emit('click');
  f.sessions[0].onresult({results: [[{transcript: 'late recording'}]]});
  assert.equal(f.sessions[0].aborted, true);
  assert.equal(f.get('[data-input]').value, '');
  assert.equal(f.get('#assistant-panel').hidden, true);
});

test('clearing chat cancels pending replies without restoring old messages', async () => {
  let resolve;
  const f = setup({fetchImpl: () => new Promise((done) => {resolve = done;})});
  f.get('[data-input]').value = 'Crocin';
  const pending = f.get('[data-assistant-form]').emit('submit');
  f.get('[data-clear]').emit('click');
  resolve({ok: true, status: 200, json: async () => ({reply: 'stale reply'})});
  await pending;
  assert.equal(f.get('[data-messages]').children.length, 1);
  assert.equal(f.requests[0].options.signal.aborted, true);
  assert.equal(f.get('[data-input]').disabled, false);
});

test('read-aloud is opt-in and passes the chosen language to speech', async () => {
  const f = setup(); f.get('[data-input]').value = 'Crocin';
  await f.get('[data-assistant-form]').emit('submit');
  assert.equal(f.spoken.length, 0);
  f.get('[data-read-aloud]').checked = true;
  f.get('[data-language]').value = 'hi-IN';
  f.get('[data-input]').value = 'Crocin';
  await f.get('[data-assistant-form]').emit('submit');
  assert.equal(f.spoken[0].lang, 'hi-IN');
  assert.equal(f.get('[data-stop-audio]').disabled, false);
});

test('expired login preserves draft and gives a sign-in message', async () => {
  const f = setup({fetchImpl: async () => ({ok: false, status: 401})});
  f.get('[data-input]').value = 'Crocin';
  await f.get('[data-assistant-form]').emit('submit');
  assert.equal(f.get('[data-input]').value, 'Crocin');
  assert.match(f.get('[data-status]').textContent, /Sign in again/);
});

test('catalogue prompt opens only the trusted in-app report link', async () => {
  const f = setup({fetchImpl: async () => ({ok: true, status: 200, json: async () => ({reply: 'Catalogue summary', report_url: '/reports/medicine-catalogue/'})})});
  await f.get('[data-prompt=catalogue]').emit('click');
  // requestSubmit starts the async handler; allow its fetch/json steps to finish.
  await new Promise(setImmediate);
  assert.equal(JSON.parse(f.requests[0].options.body).message, 'medicine catalogue report');
  const reply = f.get('[data-messages]').children.at(-1);
  assert.equal(reply.children[0].href, '/reports/medicine-catalogue/');
});

test('unexpected external report link is not rendered', async () => {
  const f = setup({fetchImpl: async () => ({ok: true, status: 200, json: async () => ({reply: 'Catalogue summary', report_url: 'https://other.example/'})})});
  f.get('[data-input]').value = 'report';
  await f.get('[data-assistant-form]').emit('submit');
  assert.equal(f.get('[data-messages]').children.at(-1).children.length, 0);
});
