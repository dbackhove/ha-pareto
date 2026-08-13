// Builds the card into the integration, where Home Assistant serves it from.
// The output is committed: HACS ships the repository as it stands, so nobody
// downstream ever runs this.
import { build } from "esbuild";

await build({
  entryPoints: ["src/pareto-card.ts"],
  outfile: "../custom_components/pareto/www/pareto-card.js",
  bundle: true,
  minify: true,
  format: "iife",
  // Chromium 80, not the newest thing that parses locally. A deliberate,
  // conservative floor: this card ends up on wall panels and old tablets
  // whose WebView nobody updates, and the bundle is committed, so whatever
  // is built here is what every installation gets forever. 80 keeps `??`
  // and `?.` native and costs ~1.2 KB to transpile the rest.
  //
  // Not a fix for an observed crash. It was introduced as one -- a Fire HD
  // 10 was reported to be failing on the `??=` in an es2021 build -- but
  // that device turned out to run Chromium 148 and to handle es2021 fine.
  // The real fault was delivery, not syntax; see _async_register_card_resource.
  // The floor stayed because it is cheap, not because it was earning its
  // keep. See test/bundle-target.test.ts.
  target: ["chrome80", "safari14", "firefox78"],
  legalComments: "none",
  banner: {
    js: "/* Pareto card -- built from frontend/src, do not edit by hand. */",
  },
});
