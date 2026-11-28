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

test("GET /api/teams/:id returns the team profile", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/teams/12");
    assert.equal(options.credentials, "include");
    assert.equal(options.cache, "no-store");

    return Response.json({
      id: 12,
      name: "Team Alpha",
      captain: { id: 1, nickname: "Shadow" },
      members: [],
      tournaments: [],
    });
  };

  const team = await api.getTeam(12);

  assert.equal(team.id, 12);
  assert.equal(team.name, "Team Alpha");
  assert.equal(team.captain.nickname, "Shadow");
});

test("GET /api/tournaments/:id/teams returns tournament teams", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/tournaments/42/teams");
    assert.equal(options.credentials, "include");
    assert.equal(options.cache, "no-store");

    return Response.json({ items: [{ id: 12, name: "Team Alpha" }] });
  };

  const result = await api.getTournamentTeams(42);

  assert.equal(result.items.length, 1);
  assert.equal(result.items[0].id, 12);
  assert.equal(result.items[0].name, "Team Alpha");
});

test("GET /api/tournaments/:id/my-registration returns the user's registration", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/tournaments/42/my-registration");
    assert.equal(options.credentials, "include");
    assert.equal(options.cache, "no-store");

    return Response.json({ team_id: 12, status: "pending" });
  };

  const result = await api.getMyRegistration(42);

  assert.equal(result.team_id, 12);
  assert.equal(result.status, "pending");
});

test("GET registrations requests the organizer endpoint without cache", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/tournaments/5/registrations");
    assert.equal(options.credentials, "include");
    assert.equal(options.cache, "no-store");
    return Response.json({ items: [], total: 0 });
  };
  assert.deepEqual(await api.getRegistrations(5), { items: [], total: 0 });
});

test("PATCH registration sends the selected decision", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/registrations/12");
    assert.equal(options.method, "PATCH");
    assert.equal(options.credentials, "include");
    assert.deepEqual(JSON.parse(options.body), { status: "approved" });
    return Response.json({ id: 12, status: "approved" });
  };
  assert.equal((await api.decideRegistration(12, "approved")).status, "approved");
});

test("POST close-registration calls the tournament close endpoint", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/tournaments/5/close-registration");
    assert.equal(options.method, "POST");
    assert.equal(options.credentials, "include");
    return Response.json({ id: 5, status: "closed" });
  };
  assert.equal((await api.closeRegistration(5)).status, "closed");
});

test("match details use the requested ID, no cache and abort signal", async () => {
  const controller = new AbortController();
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/matches/42");
    assert.equal(options.cache, "no-store");
    assert.equal(options.signal, controller.signal);
    assert.equal(options.credentials, "include");
    return Response.json({ id: 42, score1: 0, score2: 13 });
  };
  assert.equal((await api.getMatch(42, controller.signal)).score1, 0);
});

test("match 404 remains distinct from network errors", async () => {
  globalThis.fetch = async () => Response.json({ detail: "Матч не найден" }, { status: 404 });
  await assert.rejects(
    api.getMatch(999),
    (error) => error instanceof ApiError && error.status === 404,
  );
});

test("POST /api/tournaments/:id/start starts a tournament", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/tournaments/42/start");
    assert.equal(options.method, "POST");
    assert.equal(options.credentials, "include");
    return Response.json({ id: 42, status: "running", matches: [] });
  };
  const result = await api.startTournament(42);
  assert.equal(result.status, "running");
});

test("POST /api/matches/:id/result saves or updates a match score", async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "/api/matches/17/result");
    assert.equal(options.method, "POST");
    assert.equal(options.credentials, "include");
    assert.deepEqual(JSON.parse(options.body), { score1: 13, score2: 9 });
    return Response.json({ id: 17, score1: 13, score2: 9, status: "finished" });
  };
  const result = await api.setMatchResult(17, { score1: 13, score2: 9 });
  assert.equal(result.score1, 13);
  assert.equal(result.status, "finished");
});
