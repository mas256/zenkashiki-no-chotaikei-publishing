// Split example lists must preserve actual PDF item numbers, including failures
// where a repeated or missing target has the same total item count.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { verifyTeX } from "../scripts/verify-learning-design.mjs";

const root=fileURLToPath(new URL("../",import.meta.url));
const system="発展-new/第3章 漸化式の解説/05_応用7パターン/07_連立型/連立型.tex";
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
