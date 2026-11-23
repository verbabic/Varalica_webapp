import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const app = readFileSync(new URL("../static/app.js", import.meta.url), "utf8");
const css = readFileSync(new URL("../static/styles.css", import.meta.url), "utf8");
const i18n = readFileSync(new URL("../static/i18n.js", import.meta.url), "utf8");

assert.match(app, /data-suspicion-id/);
assert.match(app, /function syncSuspicionControl/);
assert.match(app, /function syncSuspicionBanner/);
assert.match(app, /function patchDiscussionPlayersInPlace/);
assert.match(app, /syncSuspicionControl\(row, player\)/);
assert.doesNotMatch(app, /suspicion\.no_change/);
assert.match(app, /event\.stopPropagation\(\)/);
assert.match(css, /\.suspicion-percent/);
assert.match(css, /max-width:\s*390px/);
for (const text of ["Tipuj Varalicu", "Na koga sumnjaš?", "Tippe auf den Betrüger", "Wen verdächtigst du?"]) {
  assert.ok(i18n.includes(text), text);
}

console.log("suspicion ui checks passed");
