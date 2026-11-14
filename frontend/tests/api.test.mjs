import { afterEach, test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

// Next.js загружает api.js как ESM; используем тот же исходник без изменения package type.
const source = await readFile(new URL("../src/lib/api.js", import.meta.url), "utf8");
const { api, ApiError, fieldErrors, formatDate } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);
const originalFetch = globalThis.fetch;
afterEach(() => {
  globalThis.fetch = originalFetch;
});

test("GET /api/me sends the cookie needed by the new backend", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/me");
    assert.equal(options.credentials, "include");
    return Response.json({ id: 7, nickname: "Shadow", avatar_url: null });
  };
  assert.equal((await api.getMe()).id, 7);
});

test("POST /api/tournaments sends the agreed fields and receives the generated ID", async () => {
  const data = {
    title: "Arena Cup",
    starts_at: "2099-11-14T16:00:00.000Z",
    max_teams: 8,
    rules: null,
  };
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/tournaments");
    assert.equal(options.method, "POST");
    assert.equal(options.headers["Content-Type"], "application/json");
    assert.equal(options.credentials, "include");
    assert.deepEqual(JSON.parse(options.body), data);
    assert.equal("organizer_id" in JSON.parse(options.body), false);
    return Response.json({ ...data, id: 42, status: "registration" }, { status: 201 });
  };
  assert.equal((await api.createTournament(data)).id, 42);
});

test("401 is preserved so the form can request a new login", async () => {
  globalThis.fetch = async () =>
    Response.json({ detail: "Сначала войдите через Discord" }, { status: 401 });
  await assert.rejects(
    api.createTournament({}),
    (error) => error instanceof ApiError && error.status === 401,
  );
});

test("FastAPI 422 locations map to the corresponding form fields", async () => {
  globalThis.fetch = async () =>
    Response.json(
      {
        detail: [
          { loc: ["body", "starts_at"], msg: "Value error, Дата турнира не может быть в прошлом" },
          { loc: ["body", "max_teams"], msg: "Input should be 4, 8 or 16" },
        ],
      },
      { status: 422 },
    );
  try {
    await api.createTournament({});
    assert.fail("Expected validation error");
  } catch (error) {
    assert.equal(error.status, 422);
    assert.deepEqual(Object.keys(fieldErrors(error)), ["starts_at", "max_teams"]);
  }
});

test("GET tournament uses the real ID and preserves a public 404", async () => {
  globalThis.fetch = async (url) => {
    assert.equal(url, "/api/tournaments/999");
    return Response.json({ detail: "Турнир не найден" }, { status: 404 });
  };
  await assert.rejects(
    api.getTournament(999),
    (error) => error.status === 404 && error.message === "Турнир не найден",
  );
});

test("logout accepts the backend's empty 204 response", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/auth/logout");
    assert.equal(options.method, "POST");
    assert.equal(options.credentials, "include");
    return new Response(null, { status: 204 });
  };
  assert.equal(await api.logout(), null);
});

test("a non-JSON proxy failure produces a useful error instead of a JSON exception", async () => {
  globalThis.fetch = async () => new Response("Bad Gateway", { status: 502 });
  await assert.rejects(
    api.getMe(),
    (error) =>
      error instanceof ApiError && error.status === 502 && error.message === "Сервер недоступен",
  );
});

test("UTC dates from the backend are displayed in Moscow time", () => {
  assert.match(formatDate("2099-11-14T16:00:00Z"), /19:00/);
  assert.match(formatDate("2099-11-14T16:00:00Z"), /14/);
});
