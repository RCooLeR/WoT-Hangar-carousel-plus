"use strict";

// Exercise only the narrow patched expressions, never the full client bundle.
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const stage = path.resolve(process.argv[2] || "build/stage");
const standard = "res/gui/gameface/_dist/production/mono/hangar/views/main/main.html/bundle.js";
const modes = ["comp7_light", "comp7", "frontline", "fun_random", "last_stand"];
const bundles = [standard, ...modes.map(mode =>
  `res/${mode}/gui/gameface/_dist/production/mono/lobby/views/hangar/hangar.html/bundle.js`)];

function one(source, pattern, label) {
  const matches = [...source.matchAll(pattern)];
  assert.strictEqual(matches.length, 1, `${label}: expected one expression, got ${matches.length}`);
  return matches[0].groups;
}

for (const relative of bundles) {
  const filename = path.join(stage, relative);
  const source = fs.readFileSync(filename, "utf8");
  const syntax = spawnSync(process.execPath, ["--check", filename], { encoding: "utf8" });
  assert.strictEqual(syntax.status, 0, `${relative}: ${syntax.stderr}`);

  const chunk = one(source,
    /(?<body>const e=\[\];for\(let t=0;t<(?<list>[\w$]+)\.length;t\+=(?<rows>[\w$]+)\)e\.push\(\k<list>\.slice\(t,t\+\k<rows>\)\);const a=e\.at\(-1\);if\(a\)for\(;a\.length<\k<rows>;\)a\.push\((?<empty>[\w$]+)\);return e)/g,
    `${relative} chunker`);
  const chunker = new Function(chunk.list, chunk.rows, chunk.empty, chunk.body);
  for (let rows = 1; rows <= 4; rows++) {
    for (let count = 0; count <= 35; count++) {
      const vehicles = Array.from({ length: count }, (_, id) => id + 1);
      const result = chunker(vehicles, rows, null);
      assert.strictEqual(result.length, Math.ceil(count / rows));
      assert(result.every(column => column.length === rows));
      assert.deepStrictEqual(result.flat().filter(value => value !== null), vehicles);
    }
  }

  const auto = one(source,
    /const hcpRows=(?<amount>hcpAmount|m)<=8\?1:\k<amount><=16\?2:\k<amount><=24\?3:4/g,
    `${relative} automatic thresholds`);
  const chooseRows = new Function(auto.amount,
    `return ${auto.amount}<=8?1:${auto.amount}<=16?2:${auto.amount}<=24?3:4`);
  for (const [count, expected] of [[1, 1], [8, 1], [9, 2], [16, 2], [17, 3], [24, 3], [25, 4], [366, 4]]) {
    assert.strictEqual(chooseRows(count), expected);
  }
  assert(source.includes("hcpAuto:!0})},200);return()=>clearTimeout(hcpTimer)"));
  assert(source.includes("m<=0)return;") || source.includes("hcpAmount<=0)return;"));
  one(source, /function\(e,t,a,s,n\)\{const (?<flag>[\w$]+)=1<s;function/g,
    `${relative} multi-row keyboard branch`);
  assert(!source.includes("totalElements:2==="));

  const sort = one(source,
    /\.sort\(\(e,t\)=>\{(?<body>const a=Number\(hcp.values\[e.id\]\?\?0\),s=Number\(hcp.values\[t.id\]\?\?0\);return a===s\?0:\(hcp.descending\?-1:1\)\*\(a-s\))\}/g,
    `${relative} comparator`);
  const compare = new Function("hcp", "e", "t", sort.body);
  const records = [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }];
  for (const [descending, expected] of [[false, [2, 4, 1, 3]], [true, [3, 1, 2, 4]]]) {
    const hcp = { values: { 1: 20, 2: 0, 3: 30, 4: 0 }, descending };
    assert.deepStrictEqual(records.slice().sort((a, b) => compare(hcp, a, b)).map(v => v.id), expected);
  }

  for (const anchor of ["vehicleCard-", "Card_content_", "FilterPopover_popover_", "FilterPopover_category_", "FilterPopover_scroll_"]) {
    assert(source.includes(anchor), `${relative}: DOM anchor changed: ${anchor}`);
  }
  process.stdout.write(`PASS ${relative}: syntax, 144 chunk cases, automatic rows, sorting, DOM anchors\n`);
}

const tooltip = path.join(stage, "res/gui/gameface/_dist/production/mono/hangar/views/vehicle_tooltip/vehicle_tooltip.html/bundle.js");
const tooltipSource = fs.readFileSync(tooltip, "utf8");
const tooltipSyntax = spawnSync(process.execPath, ["--check", tooltip], { encoding: "utf8" });
assert.strictEqual(tooltipSyntax.status, 0, tooltipSyntax.stderr);
assert(tooltipSource.includes("Tooltip_status_") && tooltipSource.includes("Tooltip_section_"));
process.stdout.write("PASS tooltip: syntax and DOM anchors\n");
