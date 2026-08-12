// The committed bundle must stay inside the oldest browser we support.
//
// This exists because of a real failure. On an Amazon Fire HD 10 (11th gen,
// Fire OS 7 / Android API 30) the dashboard showed "Custom element doesn't
// exist: pareto-card" while the page around it rendered fine. The module had
// been fetched; it threw a SyntaxError while being evaluated, so
// customElements.define() never ran and Home Assistant fell back to its
// generic missing-card placeholder. The cause was build.mjs targeting es2021,
// which left 14 `??=`, one `||=` and one `&&=` in the output -- syntax that
// needs Chromium 85. The sibling integration ha-tinybreeze shipped the same
// defect from the same build config and carries the same guard.
//
// Why a test and not just a lower target: the bundle is built once and
// committed, so nothing downstream ever re-runs esbuild. A raised target
// ships straight to every installation. CI's `npm run build` +
// `git diff --exit-code` catches a *forgotten* rebuild, but passes happily on
// a *raised target* that was rebuilt and committed -- which is exactly how the
// Fire HD bug would come back.
//
// Why a string scan and not a parse: the CI runner's Node parses ES2021
// happily, so a parser-based check would never fail on its own. The tolerated
// floor is a policy decision, so it is written down here as one rather than
// inferred from whatever the toolchain happens to accept.
//
// The scan matches literal substrings, never regexes. `.at(` as a pattern is
// a substring here; as a regex it also matches `concat(` and `repeat(`, which
// is how an early hand-run of this check reported five Array.prototype.at
// calls in a bundle that had none.
//
// The scan assumes minified output (build.mjs sets minify: true), so the
// patterns below carry no spacing variants -- `static{`, never `static {`. If
// minification is ever turned off, these need to become spacing-tolerant.

import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const here = path.dirname(fileURLToPath(import.meta.url));
const BUNDLE_PATH = path.resolve(here, "../../custom_components/pareto/www/pareto-card.js");
const BUILD_SCRIPT_PATH = path.resolve(here, "../build.mjs");
const TSCONFIG_PATH = path.resolve(here, "../tsconfig.json");

// The floor. Chromium 80 is the binding constraint -- it is what the Fire HD
// class of device runs, and it keeps `??` and `?.` native (both landed in 80)
// while esbuild transpiles the newer operators away. Safari 14 and Firefox 78
// are the contemporaries of that Chromium. Raising any of these is a decision
// about which devices stop working, so it should be made deliberately, here.
const FLOOR = ["chrome80", "safari14", "firefox78"];
const FLOOR_CHROME = 80;

// ES2020 is what Chromium 80 implements, so tsconfig says the same thing
// build.mjs does -- see the runtime-API note below.
const FLOOR_ES_LIB = "ES2020";

interface Banned {
  /** Literal substring searched for in the minified bundle. */
  pattern: string;
  feature: string;
  /** First Chromium version to support it. */
  chrome: number;
  remedy: string;
}

// esbuild's `target` lowers SYNTAX. It cannot lower a RUNTIME API:
// `"".replaceAll()`, `[].at()` and `Object.hasOwn()` are ordinary property
// accesses, so esbuild passes them through untouched and they fail on an old
// WebView exactly as the operators did. Hence two kinds of entry below, with
// two kinds of remedy: syntax means the target was raised, an API means the
// source needs rewriting.
const LOWERED_BY_ESBUILD =
  "esbuild lowers this at the declared target, so its presence means the target in build.mjs was raised. Restore the floor and rebuild.";

function apiRemedy(alternative: string): string {
  return `esbuild cannot lower a runtime API. Rewrite the call in frontend/src (${alternative}) and rebuild.`;
}

const BANNED: Banned[] = [
  { pattern: "??=", feature: "logical assignment (??=)", chrome: 85, remedy: LOWERED_BY_ESBUILD },
  { pattern: "||=", feature: "logical assignment (||=)", chrome: 85, remedy: LOWERED_BY_ESBUILD },
  { pattern: "&&=", feature: "logical assignment (&&=)", chrome: 85, remedy: LOWERED_BY_ESBUILD },
  {
    pattern: "static{",
    feature: "class static initialization block",
    chrome: 94,
    remedy: LOWERED_BY_ESBUILD,
  },
  {
    pattern: ".replaceAll(",
    feature: "String.prototype.replaceAll",
    chrome: 85,
    remedy: apiRemedy("split/join, or a regex with the g flag"),
  },
  {
    pattern: ".at(",
    feature: "Array.prototype.at / String.prototype.at",
    chrome: 92,
    remedy: apiRemedy("index arithmetic, e.g. a[a.length - 1]"),
  },
  {
    pattern: "Object.hasOwn",
    feature: "Object.hasOwn",
    chrome: 93,
    remedy: apiRemedy("Object.prototype.hasOwnProperty.call(o, k)"),
  },
  {
    pattern: ".findLast(",
    feature: "Array.prototype.findLast",
    chrome: 97,
    remedy: apiRemedy("a reverse loop, or slice().reverse().find()"),
  },
  {
    pattern: ".findLastIndex(",
    feature: "Array.prototype.findLastIndex",
    chrome: 97,
    remedy: apiRemedy("a reverse loop over the indices"),
  },
  {
    pattern: "structuredClone",
    feature: "structuredClone",
    chrome: 98,
    remedy: apiRemedy("JSON.parse(JSON.stringify(x)) for plain data"),
  },
  {
    pattern: ".toSorted(",
    feature: "Array.prototype.toSorted",
    chrome: 110,
    remedy: apiRemedy("slice().sort()"),
  },
  {
    pattern: ".toReversed(",
    feature: "Array.prototype.toReversed",
    chrome: 110,
    remedy: apiRemedy("slice().reverse()"),
  },
  {
    pattern: ".toSpliced(",
    feature: "Array.prototype.toSpliced",
    chrome: 110,
    remedy: apiRemedy("slice() followed by splice()"),
  },
  {
    // The one generic enough to catch an unrelated property named `with` some
    // day. If that happens it is a judgment call, not a mystery: confirm the
    // hit is not Array.prototype.with and drop this entry.
    pattern: ".with(",
    feature: "Array.prototype.with",
    chrome: 110,
    remedy: apiRemedy("slice() followed by assignment to the index"),
  },
  {
    pattern: "Object.groupBy",
    feature: "Object.groupBy",
    chrome: 117,
    remedy: apiRemedy("reduce() into a plain object"),
  },
  {
    pattern: "Map.groupBy",
    feature: "Map.groupBy",
    chrome: 117,
    remedy: apiRemedy("reduce() into a Map"),
  },
];

function readBundle(): string {
  // A clear message beats an ENOENT stack for whoever hits this on a checkout
  // where the card was never built.
  expect(
    existsSync(BUNDLE_PATH),
    `No bundle at ${BUNDLE_PATH}. Run \`npm run build\` in frontend/ first.`,
  ).toBe(true);
  return readFileSync(BUNDLE_PATH, "utf-8");
}

function countOccurrences(haystack: string, needle: string): number {
  return haystack.split(needle).length - 1;
}

describe("the committed bundle stays within the browser floor", () => {
  const bundle = readBundle();

  for (const { pattern, feature, chrome, remedy } of BANNED) {
    it(`ships no ${feature}`, () => {
      const count = countOccurrences(bundle, pattern);
      expect(
        count,
        `${feature} needs Chromium ${chrome}, but the card targets Chromium ${FLOOR_CHROME}. ` +
          `Found ${count} occurrence(s) of \`${pattern}\` in the committed bundle. ` +
          `On an older WebView the whole module throws a SyntaxError while being evaluated, ` +
          `customElements.define() never runs, and Home Assistant reports ` +
          `"Custom element doesn't exist: pareto-card". ${remedy}`,
      ).toBe(0);
    });
  }
});

describe("the floor is declared where the build reads it", () => {
  it("build.mjs targets the floor", () => {
    // Pinned so that raising the target in the config and rebuilding cannot
    // quietly move the goalposts while the bundle scan above keeps passing.
    const source = readFileSync(BUILD_SCRIPT_PATH, "utf-8");
    const match = source.match(/target:\s*(\[[^\]]*\]|"[^"]*")/);
    expect(match, "no `target:` setting found in build.mjs").not.toBeNull();

    const declared = [...match![1].matchAll(/"([^"]+)"/g)].map((m) => m[1]).sort();
    expect(
      declared,
      `build.mjs must target ${FLOOR.join(", ")}. A single "esXXXX" target is not enough: ` +
        `es2021 is what shipped the Fire HD bug.`,
    ).toEqual([...FLOOR].sort());
  });

  it("tsconfig.json caps the available runtime APIs at the same floor", () => {
    // The earlier of the two defences. With lib at ES2021, `"".replaceAll()`
    // typechecks, esbuild passes it through, and it reaches the bundle where
    // only the scan above would catch it. At ES2020, tsc rejects it outright.
    const tsconfig = JSON.parse(readFileSync(TSCONFIG_PATH, "utf-8")) as {
      compilerOptions: { target: string; lib: string[] };
    };
    expect(tsconfig.compilerOptions.target).toBe(FLOOR_ES_LIB);
    expect(
      tsconfig.compilerOptions.lib,
      `lib must start at ${FLOOR_ES_LIB}; a later lib re-enables runtime APIs that esbuild cannot lower.`,
    ).toContain(FLOOR_ES_LIB);
  });
});
