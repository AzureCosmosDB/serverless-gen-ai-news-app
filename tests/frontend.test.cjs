const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

class Element {
    constructor() {
        this.children = [];
        this.handlers = {};
        this.attributes = {};
        this.value = "";
        this.disabled = false;
    }
    addEventListener(name, handler) { this.handlers[name] = handler; }
    appendChild(child) { this.children.push(child); child.parentNode = this; }
    removeChild(child) {
        const index = this.children.indexOf(child);
        assert.notEqual(index, -1);
        this.children.splice(index, 1);
        child.parentNode = null;
    }
    setAttribute(name, value) { this.attributes[name] = value; }
    removeAttribute(name) { delete this.attributes[name]; }
    focus() {}
}

function loadApp(fetch) {
    const elements = Object.fromEntries(
        ["chat-history", "user-input", "send-button"].map(id => [id, new Element()])
    );
    let ready;
    const document = {
        addEventListener(name, callback) { ready = callback; },
        getElementById(id) { return elements[id]; },
        createElement() { return new Element(); },
    };
    const context = vm.createContext({
        document, fetch, window: { location: { hostname: "localhost" } },
        console: { log() {}, error() {} },
    });
    vm.runInContext(fs.readFileSync(path.join(__dirname, "../static-web-app/app.js"), "utf8"), context);
    ready();
    return elements;
}

test("a local chat request reaches the local API and records a valid answer", async () => {
    let request;
    const elements = loadApp(async (url, options) => {
        request = { url, body: JSON.parse(options.body) };
        return { ok: true, json: async () => ({ response: "News answer", cached: false }) };
    });
    elements["user-input"].value = "Latest news";
    await elements["send-button"].handlers.click();
    assert.equal(request.url, "http://localhost:7071/api/query");
    assert.deepEqual(request.body, { message: "Latest news", chatHistory: [] });
    assert.equal(elements["chat-history"].children.length, 2);
    assert.equal(elements["chat-history"].children[1].innerHTML, "News answer");
    assert.equal(elements["send-button"].disabled, false);
    assert.equal(elements["user-input"].attributes.disabled, undefined);
});

for (const [name, fetch] of [
    ["HTTP failure", async () => ({ ok: false, status: 503, json: async () => ({ error: "unavailable" }) })],
    ["network failure", async () => { throw new Error("connection refused"); }],
    ["invalid JSON", async () => ({ ok: true, json: async () => { throw new SyntaxError("invalid JSON"); } })],
    ["missing answer", async () => ({ ok: true, json: async () => ({}) })],
]) {
    test(`${name} displays an error and allows the user to retry`, async () => {
        const elements = loadApp(fetch);
        elements["user-input"].value = "Latest news";
        await elements["send-button"].handlers.click();
        assert.equal(elements["chat-history"].children.length, 2);
        assert.match(elements["chat-history"].children[1].textContent, /try again/i);
        assert.equal(elements["send-button"].disabled, false);
        assert.equal(elements["user-input"].attributes.disabled, undefined);
    });
}
