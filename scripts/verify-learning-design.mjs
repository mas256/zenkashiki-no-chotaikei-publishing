// Structural checks and exact finite checks for the learning-design revision.
// These finite calculations supplement the mathematical arguments in the text.
import { readFileSync } from "node:fs";
import { join } from "node:path";
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
function verifyTeX(readText) {
  const files=new Map();
  function visit(path) {
    if (files.has(path)) return;
    const text=stripComments(readText(path)); files.set(path,text);
    for (const m of text.matchAll(/\\input\{([^}]+)\}/g)) {
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
    for (const m of text.matchAll(/\\label\{([^}]+)\}/g)) {
      assert(!labels.has(m[1]),"duplicate label "+m[1]); labels.add(m[1]);
    }
    for (const m of text.matchAll(/\\(?:sectionref|chapterref|headingref|ref)\*?\{([^}#]+)\}|\\hyperref\[([^]#]+)\]/g))
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
      assert(groups[id][role]===undefined,"duplicate item targets "+id+":"+role);
      groups[id][role]=count;
    }
  }
  for (const ref of references) assert(labels.has(ref),"missing heading reference "+ref);
  for (const ref of problemRefs)
    assert(groups[ref.id]?.problem>=ref.number && ref.number>0,"missing problem reference "+ref.id+":"+ref.number);
  for (const [id,roles] of Object.entries(groups))
    for (const [role,count] of Object.entries(roles))
      assert(count===roles.problem,"item count mismatch "+id+":"+role);
  assert(groups["practice-basic"].problem===55,"standard exercise count changed");
  assert(groups["practice-advanced"].problem===10,"advanced exercise count changed");
  assert(groups["practice-bridge"].problem===10,"bridge exercise count changed");
  assert(groups["practice-entrance"].problem===10,"research exercise count changed");
  // These question identities are used by the reading routes and comparisons.
  // Use the unstripped source comments to check stable question identities.
  const original=readText("発展-new/第4章 実際の解き方/03_実践演習/標準難易度.tex");
  const originals=original.slice(original.indexOf("\\subsubsection{問題}"),original.indexOf("\\subsubsection{方針}"));
  const questionIds=[...originals.matchAll(/^\s*% ([A-Z][1-5])\s*$/gm)].map(m=>m[1]);
  const expected={1:"Q1",2:"S1",3:"R1",4:"M1",5:"G1",6:"T1",7:"U1",8:"L1",9:"C1",10:"D1",11:"F1",17:"D2",19:"R2",20:"M2",23:"T3",24:"M3",25:"U3",26:"Q3",29:"L3",34:"S4",42:"R4"};
  for (const [number,id] of Object.entries(expected))
    assert(questionIds[Number(number)-1]===id,"reading route identity changed at standard "+number);
  const bridge=readText("発展-new/第4章 実際の解き方/03_実践演習/発展入門.tex");
  const bridgeProblems=bridge.slice(bridge.indexOf("\\subsubsection{問題}"),bridge.indexOf("\\subsubsection{方針}"));
  const bridgeIds=[...bridgeProblems.matchAll(/^\s*% (B\d+):/gm)].map(m=>m[1]);
  assert(bridgeIds.join(",")===Array.from({length:10},(_,i)=>"B"+(i+1)).join(","),"bridge reading route identities changed");
  return { inputFiles:files.size,labels:labels.size,headingReferences:references.length,problemReferences:problemRefs.length,exerciseCount:Object.entries(groups).filter(([id])=>id.startsWith("practice-")).reduce((sum,[,roles])=>sum+roles.problem,0) };
}

const root=fileURLToPath(new URL("../",import.meta.url));
const tex=verifyTeX(path=>readFileSync(join(root,path),"utf8"));
const math=verifyMathematics();
console.log(JSON.stringify({tex,math},null,2));
