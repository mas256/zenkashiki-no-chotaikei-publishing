// Structural checks and exact finite checks for the learning-design revision.
// These finite calculations supplement the mathematical arguments in the text.
import { readFileSync, readdirSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

function assert(ok, message) { if (!ok) throw new Error(message); }
function gcd(a, b) {
  a = a < 0n ? -a : a; b = b < 0n ? -b : b;
  while (b) [a, b] = [b, a % b];
  return a;
}
function r(n, d = 1n) {
  n = BigInt(n); d = BigInt(d); assert(d !== 0n, "zero denominator");
  if (d < 0n) { n = -n; d = -d; }
  const g = gcd(n, d); return [n / g, d / g];
}
const add = (a,b) => r(a[0]*b[1]+b[0]*a[1],a[1]*b[1]);
const sub = (a,b) => add(a,[-b[0],b[1]]);
const mul = (a,b) => r(a[0]*b[0],a[1]*b[1]);
const div = (a,b) => r(a[0]*b[1],a[1]*b[0]);
const equal = (a,b) => a[0]===b[0] && a[1]===b[1];

function verifyMathematics() {
  let affine = 0, operationSteps = 0, vectorCases = 0;
  for (const p of [-2,-1,0,1,2]) for (const q of [-3,0,5]) for (const initial of [-4,0,5]) {
    let a = r(initial);
    for (let n=1; n<=15; n++) {
      const next = add(mul(r(p),a),r(q));
      if (p===0) assert(equal(next,r(q)), "p=0 branch");
      else if (p===1) assert(equal(sub(next,a),r(q)), "p=1 branch");
      else {
        const alpha = r(q,1-p);
        assert(equal(sub(next,alpha),mul(r(p),sub(a,alpha))), "fixed point shift");
      }
      a=next; affine++;
    }
  }
  let a1=1n, a2=r(2), a3=-2n;
  for (let n=1n; n<=50n; n++) {
    const next1=3n*a1+2n*n+1n;
    assert(next1+n+2n===3n*(a1+n+1n), "operation 1 shift");
    const next2=add(mul(r(n+2n,n),a2),r((n+1n)*(n+2n)));
    const b=div(a2,r(n)), nextB=div(next2,r(n+1n));
    assert(equal(nextB,add(mul(r(n+2n,n+1n),b),r(n+2n))), "operation 2 first candidate");
    const c=div(a2,r(n*(n+1n))),nextC=div(next2,r((n+1n)*(n+2n)));
    assert(equal(nextC,add(c,r(1))), "operation 2 normalization");
    assert(equal(a2,r(n*n*(n+1n))), "operation 2 general term");
    const next3=(2n**(2n*n+1n))*a3;
    assert(next3/(2n**((n+1n)*(n+1n)))===a3/(2n**(n*n)), "operation 3 normalization");
    assert(a3===-(2n**(n*n)) && a3<0n, "operation 3 general term and sign");
    a1=next1; a2=next2; a3=next3; operationSteps+=3;
  }
  for (const initial of [2n,0n,-2n]) {
    let a=initial;
    for (let n=0;n<8;n++) {
      assert(a===initial**(2n**BigInt(n)), "squaring recurrence");
      if (initial===2n) assert(a>0n,"positive log domain");
      if (initial===0n) assert(a===0n,"zero solution");
      if (initial===-2n && n>0) assert(a>0n,"positive after the first negative term");
      a*=a;
    }
  }
  for (let x=-10;x<=10;x++) for (let y=-10;y<=10;y++) {
    const c=r(x+y,2),d=r(x-y,2);
    assert(equal(add(c,d),r(x)) && equal(sub(c,d),r(y)), "vector decomposition");
    vectorCases++;
  }
  return { affineUpdates:affine, operationUpdates:operationSteps, vectorCases, logDomainCases:3 };
}

function stripComments(text) {
  return text.split("\n").map(line => {
    for (let i=0; i<line.length; i++) if (line[i]==="%") {
      let k=i-1,slashes=0;
      while (k>=0 && line[k--]==="\\") slashes++;
      if (slashes%2===0) return line.slice(0,i);
    }
    return line;
  }).join("\n");
}
// \BookImport{f-...} refers to the file whose first lines declare
// "% BOOK-FILE-ID: f-...". Build that index from the repository tree.
function bookFileIndex(root) {
  const index=new Map();
  for (const entry of readdirSync(root,{recursive:true,withFileTypes:true})) {
    if (!entry.isFile() || !entry.name.endsWith(".tex")) continue;
    const full=join(entry.parentPath ?? entry.path,entry.name);
    if (/(^|[\\/])(\.git|old|tmp|out|node_modules)([\\/]|$)/.test(full.slice(root.length))) continue;
    const id=readFileSync(full,"utf8").match(/^\uFEFF?%\s*BOOK-FILE-ID:\s*(f-[0-9a-f]+)/m)?.[1];
    if (id) index.set(id,full.slice(root.length).replace(/^[\\/]/,""));
  }
  return index;
}
export function verifyTeX(readText, pdfDestinations = null) {
  const files=new Map();
  const index=bookFileIndex(fileURLToPath(new URL("../",import.meta.url)));
  function visit(path) {
    if (files.has(path)) return;
    const raw=readText(path); const text=stripComments(raw); files.set(path,text);
    for (const m of text.matchAll(/\\input\{([^}]+)\}|\\BookImport\{([^}]+)\}/g)) {
      if (m[2]) { assert(index.has(m[2]),"unknown BookImport "+m[2]); visit(index.get(m[2])); continue; }
      const ref=m[1];
      visit(ref.startsWith("../") ? ref.slice(3) : "発展-new/"+ref);
    }
  }
  visit("発展-new/漸化式の超体系的解説.tex");
  const labels=new Set(),references=[],problemRefs=[],groups={};
  for (const [path,text] of files) {
    let depth=0,dollars=0;
    for (let i=0;i<text.length;i++) {
      if (text[i]==="\\") { i++; continue; }
      if (text[i]==="{") depth++;
      if (text[i]==="}") { depth--; assert(depth>=0,"unmatched brace in "+path); }
      if (text[i]==="$") dollars++;
    }
    assert(depth===0 && dollars%2===0,"unbalanced math or braces in "+path);
    const stack=[];
    for (const m of text.matchAll(/\\(begin|end)\{([^}]+)\}/g)) {
      if (m[1]==="begin") stack.push(m[2]);
      else assert(stack.pop()===m[2],"unbalanced environment in "+path);
    }
    assert(stack.length===0,"unclosed environment in "+path);
    const mathStack=[];
    for (const m of text.matchAll(/(?<!\\)\\([\[\]()])/g)) {
      if (m[1]==="[" || m[1]==="(") mathStack.push(m[1]);
      else assert(mathStack.pop()===(m[1]==="]" ? "[" : "("),"unbalanced math delimiter in "+path);
    }
    assert(mathStack.length===0,"unclosed math delimiter in "+path);
    for (const m of text.matchAll(/\\label\{([^}]+)\}/g)) {
      assert(!labels.has(m[1]),"duplicate label "+m[1]); labels.add(m[1]);
    }
    for (const m of text.matchAll(/\\(?:sectionref|chapterref|headingref|booknavref|ref)\*?\{([^}#]+)\}|\\hyperref\[([^]#]+)\]/g))
      references.push(m[1]||m[2]);
    for (const m of text.matchAll(/\\bookproblemref\{([^}#]+)\}\{(\d+)\}\{[^}]+\}/g))
      problemRefs.push({id:m[1],number:Number(m[2])});
    for (const m of text.matchAll(/\\begin\{enumerate\}\[([^\n]*)\]/g)) {
      const f=m[1].match(/\\bookitemlink\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}/);
      if (!f) continue;
      let depth=1,count=0,t;
      const tokens=/\\(begin|end)\{enumerate\}|\\item\b/g;
      tokens.lastIndex=m.index+m[0].length;
      while ((t=tokens.exec(text)) && depth) {
        if (t[1]==="begin") depth++;
        else if (t[1]==="end") depth--;
        else if (depth===1) count++;
      }
      const id=f[1],role=f[2]; groups[id]??={};
      const start=Number(m[1].match(/(?:^|,)\s*start\s*=\s*(\d+)/)?.[1] ?? 1);
      assert(start>0,"invalid first item number "+id+":"+role);
      groups[id][role]??=new Set();
      for (let number=start;number<start+count;number++) {
        assert(!groups[id][role].has(number),"duplicate item target "+id+":"+role+":"+number);
        groups[id][role].add(number);
      }
    }
  }
  for (const ref of references) assert(labels.has(ref),"missing heading reference "+ref);
  for (const ref of problemRefs)
    assert(groups[ref.id]?.problem?.has(ref.number),"missing problem reference "+ref.id+":"+ref.number);
  for (const [id,roles] of Object.entries(groups)) {
    assert(roles.problem,"missing problem list "+id);
    for (let number=1;number<=roles.problem.size;number++)
      assert(roles.problem.has(number),"non-contiguous problem numbers "+id);
    for (const [role,numbers] of Object.entries(roles))
      assert(numbers.size===roles.problem.size && [...numbers].every(number=>roles.problem.has(number)),
        "item number mismatch "+id+":"+role);
  }
  assert(groups["practice-basic"].problem.size===55,"standard exercise count changed");
  assert(groups["practice-advanced"].problem.size===10,"advanced exercise count changed");
  assert(groups["practice-bridge"].problem.size===10,"bridge exercise count changed");
  assert(groups["practice-entrance"].problem.size===10,"research exercise count changed");
  assert(groups["practice-special"].problem.size===15,"special exercise count changed");
  assert(groups["practice-gauss"].problem.size===3,"floor-function exercise count changed");
  // These question identities are used by the reading routes and comparisons.
  // Use the unstripped source comments to check stable question identities.
  const original=readText("発展-new/第3章 解法の選択と演習/sections/04_演習/subsections/02_標準.tex");
  const originals=original.slice(original.indexOf("\\subsubsection{問題}"),original.indexOf("\\subsubsection{方針}"));
  const questionIds=[...originals.matchAll(/^\s*% ([A-Z][1-5])\s*$/gm)].map(m=>m[1]);
  const expected={1:"Q1",2:"S1",3:"R1",4:"M1",5:"G1",6:"T1",7:"U1",8:"L1",9:"C1",10:"D1",11:"F1",17:"D2",19:"R2",20:"M2",23:"T3",24:"M3",25:"U3",26:"Q3",29:"L3",34:"S4",42:"R4"};
  for (const [number,id] of Object.entries(expected))
    assert(questionIds[Number(number)-1]===id,"reading route identity changed at standard "+number);
  const bridge=readText("発展-new/第3章 解法の選択と演習/sections/04_演習/subsections/04_発展入門.tex");
  const bridgeProblems=bridge.slice(bridge.indexOf("\\subsubsection{問題}"),bridge.indexOf("\\subsubsection{方針}"));
  const bridgeIds=[...bridgeProblems.matchAll(/^\s*% (B\d+):/gm)].map(m=>m[1]);
  assert(bridgeIds.join(",")===Array.from({length:10},(_,i)=>"B"+(i+1)).join(","),"bridge reading route identities changed");
  let pdfProblemDestinations=0;
  if (pdfDestinations) {
    for (const [id,roles] of Object.entries(groups)) for (const [role,numbers] of Object.entries(roles)) {
      for (const number of numbers) {
        const name="book:"+id+":"+role+":"+number;
        assert(pdfDestinations.has(name),"missing PDF problem destination "+name);
        pdfProblemDestinations++;
      }
    }
  }
  return { ...(pdfDestinations ? {pdfProblemDestinations} : {}), inputFiles:files.size,labels:labels.size,headingReferences:references.length,problemReferences:problemRefs.length,exerciseCount:Object.entries(groups).filter(([id])=>id.startsWith("practice-")).reduce((sum,[,roles])=>sum+roles.problem.size,0) };
}

if (process.argv[1] && fileURLToPath(import.meta.url)===resolve(process.argv[1])) {
const root=fileURLToPath(new URL("../",import.meta.url));
let pdfDestinations=null;
if (process.argv.includes("--pdf")) {
  const next=process.argv[process.argv.indexOf("--pdf")+1];
  const pdf=next && !next.startsWith("--") ? resolve(next) : join(root,"発展-new/漸化式の超体系的解説.pdf");
  const destinations=execFileSync("pdfinfo",["-dests",pdf],{encoding:"utf8"});
  pdfDestinations=new Set(destinations.match(/book:[a-z0-9-]+:[a-z]+(?::[0-9]+)?/g) || []);
}
const tex=verifyTeX(path=>readFileSync(join(root,path),"utf8"),pdfDestinations);
const math=verifyMathematics();
console.log(JSON.stringify({tex,math},null,2));
}
