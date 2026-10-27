// Split example lists must preserve actual PDF item numbers, including failures
// where a repeated or missing target has the same total item count.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { verifyTeX } from "../scripts/verify-learning-design.mjs";

const root=fileURLToPath(new URL("../",import.meta.url));
const system="発展-new/第2章 漸化式の解法/sections/04_応用パターン/subsections/07_連立型.tex";
const read=path=>readFileSync(join(root,path),"utf8");
const original=read(system);
assert.equal((original.match(/start=2,label=/g) || []).length,4);
assert.equal(verifyTeX(read).exerciseCount,107);

const checkMutation=text=>verifyTeX(path=>path===system ? text : read(path));
assert.throws(()=>checkMutation(original.replace("start=2,label=","start=1,label=")),/duplicate item target/);
assert.throws(()=>checkMutation(original.replaceAll("start=2,label=","start=3,label=")),/non-contiguous problem numbers/);
const mismatched=original.replace(/start=2,(.*?\{example-system-1\}\{answer\})/,"start=3,$1");
assert.notEqual(mismatched,original);
assert.throws(()=>checkMutation(mismatched),/item number mismatch/);
console.log("Split example navigation verified: actual numbers, duplicate targets, gaps, and answer mismatches");

// Commentary may be sparse, but every answer still needs its route and number.
const standard="発展-new/第3章 解法の選択と演習/sections/04_演習/subsections/02_標準.tex";
const manuscript=read(standard);
const checkExerciseMutation=text=>verifyTeX(path=>path===standard ? text : read(path));
assert.throws(()=>checkExerciseMutation(manuscript.replace("\\textbf{チャートの経路：}","")),/one chart route/);
assert.throws(()=>checkExerciseMutation(manuscript.replace("\\textbf{チャートの経路：}","\\textbf{チャートの経路：}\\textbf{チャートの経路：}")),/one chart route/);
const orphan=manuscript.replace(/start=55,(.*?\{practice-basic\}\{solution\})/,"start=56,$1");
assert.notEqual(orphan,manuscript);
assert.throws(()=>checkExerciseMutation(orphan),/item number mismatch/);
const repeated=manuscript.replace(/start=19,(.*?\{practice-basic\}\{solution\})/,"start=16,$1");
assert.notEqual(repeated,manuscript);
assert.throws(()=>checkExerciseMutation(repeated),/duplicate item target/);
console.log("Exercise navigation verified: sparse commentary, missing/duplicate routes, orphan/duplicate commentary numbers");
