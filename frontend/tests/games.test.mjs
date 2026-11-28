import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const source = await readFile(new URL("../src/lib/games.js", import.meta.url), "utf8");
const { gameInfo, defaultGame } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`
);

test("known game has short name, full name and format", () => {
  assert.deepEqual(gameInfo("cs2"), { short: "CS2", name: "Counter-Strike 2", format: "5×5" });
  assert.equal(gameInfo(defaultGame).short, "CS2");
});

test("unknown game is shown as is instead of pretending to be CS2", () => {
  assert.deepEqual(gameInfo("dota2"), { short: "dota2", name: "dota2", format: "" });
  assert.deepEqual(gameInfo(undefined), { short: "", name: "", format: "" });
});
