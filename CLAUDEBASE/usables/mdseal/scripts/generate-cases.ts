import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const root = join(import.meta.dir, "..", "tests", "fixtures", "cases");
const cases = [
  ["deescaped-display-brackets", "[ E = mc^2 ]", "\\\\[ E = mc^2 \\\\]", "MDSEAL_MATH_BRACKET_DELIMITER_DEESCAPED"],
  ["deescaped-paren-brackets", "( a^2 + b^2 = c^2 )", "\\\\( a^2 + b^2 = c^2 \\\\)", "MDSEAL_MATH_PAREN_DELIMITER_DEESCAPED"],
  ["inline-dollar-balance", "Inline math $E = mc^2 and text.", "Inline math $E = mc^2$ and text.", "MDSEAL_MATH_UNBALANCED_INLINE_DOLLAR"],
  ["unicode-minus", "Math $5 − 3$.", "Math $5 - 3$.", "MDSEAL_UNICODE_MINUS_IN_MATH"],
  ["code-fence-protected", "```ts\nconst x = 1;\n```", "```ts\nconst x = 1;\n```", "MDSEAL_FENCE_UNCLOSED"],
  ["inline-code-protected", "`$not math$`", "`$not math$`", ""],
  ["frontmatter-preserved", "---\ntitle: demo\n---\n$E = mc^2 and text.", "---\ntitle: demo\n---\n$E = mc^2 and text.", "MDSEAL_MATH_UNBALANCED_INLINE_DOLLAR"],
  ["html-block", "<div>$x$</div>", "<div>$x$</div>", ""],
  ["link-destination", "[x](https://example.com/$notmath)", "[x](https://example.com/$notmath)", ""],
  ["table-pipe", "| a | b |\n| $x|y$ | z |", "| a | b |\n| $x\\|y$ | z |", "MDSEAL_MATH_PIPE_IN_TABLE_CELL"],
  ["table-pipe-inside-math", "| Symbol | Formula |\n|---|---|\n| norm | $|x| = \\sqrt{x^2}$ |", "| Symbol | Formula |\n|---|---|\n| norm | $\\|x\\| = \\sqrt{x^2}$ |", "MDSEAL_MATH_PIPE_IN_TABLE_CELL"],
  ["smart-quotes", "Math “$x$”", "Math “$x$”", "MDSEAL_SMART_QUOTES_IN_MATH"],
  ["zero-width", "a\u200bb", "ab", "MDSEAL_ZERO_WIDTH_CHAR"],
  ["zero-width-inside-math", "Math $a\u200bb$", "Math $ab$", "MDSEAL_ZERO_WIDTH_CHAR"],
  ["bidi", "a\u202eb", "ab", "MDSEAL_BIDI_CONTROL_CHAR"],
  ["bidi-prose", "a\u202eb", "a\u202eb", "MDSEAL_BIDI_CONTROL_CHAR"],
  ["nbsp", "Math $a\u00a0b$", "Math $a b$", "MDSEAL_NBSP_IN_MATH"],
  ["soft-hyphen", "Math $a\u00adb$", "Math $ab$", "MDSEAL_SOFT_HYPHEN_IN_MATH"],
  ["fence-collision", "```md", "```md", "MDSEAL_FENCE_COLLISION"],
  ["display-indent", "- item\n  $$x^2$$", "- item\n  $$x^2$$", "MDSEAL_LIST_DISPLAY_MATH_INDENT"],
  ["list-display-indent", "- Explanation:\n\n\\[\nE = mc^2\n\\]\n\n- Next item", "- Explanation:\n\n\\[\nE = mc^2\n\\]\n\n- Next item", "MDSEAL_LIST_DISPLAY_MATH_INDENT"],
  ["blockquote-display", "> Claim:\n> $$\n> E = mc^2\n> $$", "> Claim:\n> $$\n> E = mc^2\n> $$", ""],
  ["html-entity", "Math $a &amp; b$", "Math $a & b$", "MDSEAL_MATH_HTML_ENTITY_IN_FORMULA"],
  ["image-equation", "![equation](./images/equation.png)", "![equation](./images/equation.png)", "MDSEAL_IMAGE_EQUATION_WITHOUT_ALT_LATEX"],
  ["image-hash", "![equation](./images/equation.png)", "![equation](./images/equation.png)", "MDSEAL_IMAGE_HASH_CHANGED"],
  ["paren-math", "\\( x+1 \\)", "\\( x+1 \\)", "MDSEAL_MATH_PAREN_DELIMITER_DEESCAPED"],
  ["trailing-escape", "x\\\\$", "x$", "MDSEAL_TRAILING_ESCAPE_BEFORE_DELIMITER"],
  ["backslash-collapse", "Math $\\\\alpha$", "Math $\\\\alpha$", "MDSEAL_MATH_BACKSLASH_COLLAPSED"],
  ["backslash-collapsed-inside-math", "Math $frac{a}{b}$", "Math $\\\\frac{a}{b}$", "MDSEAL_MATH_BACKSLASH_COLLAPSED"],
  ["blank-line-display", "$$\n\n x \n\n$$", "$$\n x \n$$", "MDSEAL_MATH_BLANK_LINE_IN_DISPLAY_BLOCK"],
  ["zone-unknown", "`$x$", "`$x$", ""],
  ["table-shape", "|a|b|\n|1|2|", "|a|b|\n|1|2|", ""],
  ["plain-text", "Nothing to fix.", "Nothing to fix.", ""],
  ["unicode-greek", "Math $α$", "Math $\\alpha$", "MDSEAL_UNICODE_GREEK_IN_MATH"],
  ["unicode-arrow", "Math $a → b$", "Math $a \\to b$", "MDSEAL_UNICODE_ARROWS_IN_MATH"],
  ["prime-ambiguous", "Math $x′$", "Math $x\\prime$", "MDSEAL_PRIME_SUBSTITUTION_AMBIGUITY"],
  ["object-replacement", "a�b", "ab", "MDSEAL_OBJECT_REPLACEMENT_CHAR"],
  ["replacement-char", "a�b", "ab", "MDSEAL_REPLACEMENT_CHAR"],
  ["math-fence", "```math\nx^2\n```", "```math\nx^2\n```", ""],
  ["github-backtick", "`x^2`", "`x^2`", ""],
  ["table-math-pipe-2", "| $a|b$ |", "| $a\\|b$ |", "MDSEAL_MATH_PIPE_IN_TABLE_CELL"],
  ["restore-lost-delimiter", "[ E = mc^2 ]", "\\\\[ E = mc^2 \\\\]", "MDSEAL_MATH_BRACKET_DELIMITER_DEESCAPED"],
  ["stale-image-hash", "![eq](./images/equation.png)", "![eq](./images/equation.png)", "MDSEAL_IMAGE_HASH_CHANGED"]
] as const;

const parserCases = [
  ["parser-stable-gfm-math", "# H\n\n$x$\n\n|a|b|\n|1|2|", "# H\n\n$x$\n\n|a|b|\n|1|2|", "MDSEAL_PARSER_STRUCTURE_DISAGREEMENT"],
  ["parser-table-pipe-disagreement", "| a | b |\n| $x|y$ | z |", "| a | b |\n| $x\\|y$ | z |", "MDSEAL_PARSER_TABLE_COUNT_DISAGREEMENT"],
  ["parser-fence-disagreement", "```ts\nx\n", "```ts\nx\n```", "MDSEAL_PARSER_FENCE_COUNT_DISAGREEMENT"],
  ["parser-html-math-like-text", "<div>$x$</div>", "<div>$x$</div>", "MDSEAL_PARSER_HTML_BLOCK_DISAGREEMENT"],
  ["parser-list-display-math", "- item\n  $$x$$", "- item\n  $$x$$", "MDSEAL_PARSER_STRUCTURE_DISAGREEMENT"],
  ["parser-blockquote-display-math", "> $$\n> x\n> $$", "> $$\n> x\n> $$", "MDSEAL_PARSER_STRUCTURE_DISAGREEMENT"],
  ["parser-refuse-regression", "```ts\nx\n", "```ts\nx\n```", "MDSEAL_PARSER_STRUCTURE_DISAGREEMENT"],
] as const;

const katexCases = [
  ["katex-valid-inline", "Inline valid: $E = mc^2$", "Inline valid: $E = mc^2$", ""],
  ["katex-valid-display", "Display valid: $$E = mc^2$$", "Display valid: $$E = mc^2$$", ""],
  ["katex-invalid-syntax", "$\\frac{a}{$", "$\\frac{a}{$", "MDSEAL_KATEX_PARSE_ERROR"],
  ["katex-unsupported-command", "$\\unknownmacro{x}$", "$\\unknownmacro{x}$", "MDSEAL_KATEX_UNSUPPORTED_COMMAND"],
  ["katex-unsafe-command", "$\\href{javascript:alert(1)}{x}$", "$\\href{javascript:alert(1)}{x}$", "MDSEAL_KATEX_UNSAFE_COMMAND"],
  ["katex-custom-macro", "$\\R^n$", "$\\R^n$", ""],
  ["katex-unicode-warning", "$a − b$", "$a - b$", "MDSEAL_UNICODE_MINUS_IN_MATH"],
  ["katex-regression-refusal", "$\\href{javascript:alert(1)}{x}$", "$\\href{javascript:alert(1)}{x}$", "MDSEAL_KATEX_UNSAFE_COMMAND"],
  ["katex-repair-improves-validation", "$frac{a}{b}$", "$\\frac{a}{b}$", "MDSEAL_MATH_BACKSLASH_COLLAPSED"],
  ["katex-restore-regression-refusal", "$\\unknownmacro{x}$", "$\\unknownmacro{x}$", "MDSEAL_KATEX_UNSUPPORTED_COMMAND"],
] as const;

const imageCases = [
  ["image-basic-existing", "![equation](./images/equation.png)", "![equation](./images/equation.png)", "MDSEAL_IMAGE_EQUATION_WITHOUT_ALT_LATEX"],
  ["image-missing-file", "![equation](./images/missing.png)", "![equation](./images/missing.png)", "MDSEAL_IMAGE_MISSING_FILE"],
  ["image-equation-empty-alt", "![](./images/equation.png)", "![](./images/equation.png)", "MDSEAL_IMAGE_EQUATION_WITHOUT_ALT_LATEX"],
  ["image-equation-alt-latex", "![\\frac{a}{b}](./images/equation.png)", "![\\frac{a}{b}](./images/equation.png)", ""],
  ["image-path-with-spaces", "![formula](./images/space%20name.png \"title\")", "![formula](./images/space%20name.png \"title\")", "MDSEAL_IMAGE_EQUATION_WITHOUT_ALT_LATEX"],
  ["image-report-only-policy", "![equation](./images/equation.png)", "![equation](./images/equation.png)", "MDSEAL_IMAGE_WITNESS_SKIPPED"],
  ["image-sidecar-only-policy", "![equation](./images/equation.png)", "![equation](./images/equation.png)", "MDSEAL_IMAGE_WITNESS_WRITTEN"],
  ["image-policy-requires-ocr-refusal", "![equation](./images/equation.png)", "![equation](./images/equation.png)", "MDSEAL_REFUSE_IMAGE_POLICY_REQUIRES_OCR"],
  ["image-hash-drift-from-seal", "![eq](./images/equation.png)", "![eq](./images/equation.png)", "MDSEAL_IMAGE_HASH_CHANGED"],
  ["image-sweep-witness-written", "![equation](./images/equation.png)", "![equation](./images/equation.png)", "MDSEAL_IMAGE_WITNESS_WRITTEN"],
] as const;

const htmlImageCases = [
  ["html-image-simple", '<img src="a.png" alt="Diagram" title="Fig 1">', '<img src="a.png" alt="Diagram" title="Fig 1">', "MDSEAL_IMAGE_REFERENCE"],
  ["html-image-srcset", '<picture><source srcset="a.png 1x, b.png 2x" media="(min-width: 800px)"><img src="fallback.png" alt="Chart"></picture>', '<picture><source srcset="a.png 1x, b.png 2x" media="(min-width: 800px)"><img src="fallback.png" alt="Chart"></picture>', "MDSEAL_IMAGE_REFERENCE"],
  ["html-image-remote", '<img src="https://example.com/a.png" alt="Remote">', '<img src="https://example.com/a.png" alt="Remote">', "MDSEAL_IMAGE_REFERENCE"],
  ["html-image-data-uri", '<img src="data:image/png;base64,AAAA" alt="Embedded">', '<img src="data:image/png;base64,AAAA" alt="Embedded">', "MDSEAL_IMAGE_REFERENCE"],
  ["html-image-malformed", '<img src="unterminated alt="oops">', '<img src="unterminated alt="oops">', "MDSEAL_IMAGE_REFERENCE"],
  ["html-image-mixed", '![md](./m.png)\n<img src="./h.png" alt="html">', '![md](./m.png)\n<img src="./h.png" alt="html">', "MDSEAL_IMAGE_REFERENCE"],
] as const;

mkdirSync(root, { recursive: true });
for (const [name, broken, golden, diag] of [...cases, ...parserCases, ...katexCases, ...imageCases, ...htmlImageCases]) {
  const dir = join(root, name);
  mkdirSync(dir, { recursive: true });
  mkdirSync(join(dir, "images"), { recursive: true });
  writeFileSync(join(dir, "broken.md"), broken, "utf-8");
  writeFileSync(join(dir, "golden.md"), golden, "utf-8");
  if (name !== "image-missing-file") {
    writeFileSync(join(dir, "images", "equation.png"), Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO9q2V4AAAAASUVORK5CYII=", "base64"));
    writeFileSync(join(dir, "images", "space name.png"), Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO9q2V4AAAAASUVORK5CYII=", "base64"));
    writeFileSync(join(dir, "a.png"), Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO9q2V4AAAAASUVORK5CYII=", "base64"));
    writeFileSync(join(dir, "b.png"), Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO9q2V4AAAAASUVORK5CYII=", "base64"));
    writeFileSync(join(dir, "fallback.png"), Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO9q2V4AAAAASUVORK5CYII=", "base64"));
  }
  const meta = {
    name,
    profile: "katex-gfm",
    expectedDiagnostics: diag ? [diag] : [],
    mustPreserveZones: ["code_fence", "inline_code", "frontmatter"],
    allowProviders: false,
  };
  writeFileSync(join(dir, "meta.json"), JSON.stringify(meta, null, 2), "utf-8");
}
