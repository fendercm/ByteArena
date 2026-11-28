import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const source = await readFile(new URL("../src/lib/bracket.js", import.meta.url), "utf8");
const { emptySlotLabel, getChampion } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);

test("empty slots use source round.position, never database IDs or input order", () => {
  const final = { id: 830, round: 3, position: 1, status: "scheduled" };
  const matches = [
    { id: 905, round: 2, position: 2, next_match_id: 830 },
    final,
    { id: 490, round: 2, position: 1, next_match_id: 830 },
  ];
  assert.equal(emptySlotLabel(final, 0, matches), "Победитель матча 2.1");
  assert.equal(emptySlotLabel(final, 1, matches), "Победитель матча 2.2");
});

test("missing source links fall back to single elimination round.position", () => {
  const match = { id: 70, round: 2, position: 2, status: "scheduled" };
  assert.equal(emptySlotLabel(match, 0, []), "Победитель матча 1.3");
  assert.equal(emptySlotLabel(match, 1, []), "Победитель матча 1.4");
});

test("bye is distinct from a future participant and has no fabricated score", () => {
  const match = { round: 1, position: 1, winner_id: 5, status: "finished" };
  assert.equal(emptySlotLabel(match, 1, []), "Проход без игры");
  assert.equal(emptySlotLabel({ ...match, status: "scheduled" }, 1, []), "Участник не определён");
});

const tournament = {
  status: "finished",
  teams: [
    { id: 5, name: "Champions" },
    { id: 9, name: "Semi winners" },
  ],
  matches: [
    { round: 3, status: "finished", next_match_id: null, winner_id: 5 },
    { round: 1, status: "finished", next_match_id: 410, winner_id: 9 },
  ],
};

test("champion comes from the final rather than the last match in the response", () => {
  assert.deepEqual(getChampion(tournament), { id: 5, name: "Champions" });
});

test("champion is not announced for running or unfinished tournaments", () => {
  assert.equal(getChampion({ ...tournament, status: "running" }), null);
  assert.equal(getChampion({ ...tournament, matches: [] }), null);
  assert.equal(
    getChampion({
      ...tournament,
      matches: [{ round: 3, status: "scheduled", next_match_id: null, winner_id: null }],
    }),
    null,
  );
});

test("missing team name still retains the champion's correct team link ID", () => {
  assert.deepEqual(getChampion({ ...tournament, teams: [] }), { id: 5, name: "Команда #5" });
});
