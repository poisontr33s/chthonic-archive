#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: theme_token_coverage.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
theme_token_coverage.py — SFS Token Scope Coverage Audit (Stage 4.0).

@SID:           TOOL_THEME_TOKEN_COVERAGE_V1
@Shabti:        CLI Script
@Purpose:       Parses chthonic-geology-color-theme.json and compares defined
                tokenColors + semanticTokenColors against the VS Code TextMate
                grammar universe. Reports covered categories, uncovered gaps,
                and per-language specializations.
"""

import json
import sys
from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────
# VS Code TextMate Grammar Universe — Canonical Scope Categories
# ────────────────────────────────────────────────────────────────────────────
# Source: https://macromates.com/manual/en/language_grammars#naming_conventions
# Extended with VS Code-specific and language-specific additions.

TEXTMATE_UNIVERSE: dict[str, list[str]] = {
    # ── Core Categories ────────────────────────────────────────────────────
    "comment": [
        "comment",
        "comment.line",
        "comment.line.double-slash",
        "comment.line.double-dash",
        "comment.line.number-sign",
        "comment.line.percentage",
        "comment.line.character",
        "comment.block",
        "comment.block.documentation",
        "comment.block.javadoc",
        "punctuation.definition.comment",
    ],
    "constant": [
        "constant",
        "constant.numeric",
        "constant.numeric.integer",
        "constant.numeric.float",
        "constant.numeric.hex",
        "constant.numeric.octal",
        "constant.numeric.binary",
        "constant.character",
        "constant.character.escape",
        "constant.character.unicode",
        "constant.language",
        "constant.language.boolean",
        "constant.language.null",
        "constant.language.undefined",
        "constant.other",
        "constant.other.placeholder",
        "constant.other.color",
        "constant.other.symbol",
        "constant.other.caps",
        "constant.other.enum",
        "constant.regexp",
    ],
    "entity": [
        "entity.name",
        "entity.name.function",
        "entity.name.function.definition",
        "entity.name.function.decorator",
        "entity.name.function.macro",
        "entity.name.type",
        "entity.name.type.class",
        "entity.name.type.interface",
        "entity.name.type.enum",
        "entity.name.type.parameter",
        "entity.name.type.module",
        "entity.name.type.lifetime",
        "entity.name.type.anchor",
        "entity.name.tag",
        "entity.name.section",
        "entity.name.namespace",
        "entity.name.module",
        "entity.name.package",
        "entity.name.import",
        "entity.name.label",
        "entity.other.attribute-name",
        "entity.other.attribute-name.class",
        "entity.other.attribute-name.id",
        "entity.other.attribute-name.pseudo-class",
        "entity.other.attribute-name.pseudo-element",
        "entity.other.inherited-class",
    ],
    "invalid": [
        "invalid",
        "invalid.illegal",
        "invalid.deprecated",
    ],
    "keyword": [
        "keyword",
        "keyword.control",
        "keyword.control.conditional",
        "keyword.control.loop",
        "keyword.control.flow",
        "keyword.control.return",
        "keyword.control.yield",
        "keyword.control.break",
        "keyword.control.continue",
        "keyword.control.import",
        "keyword.control.export",
        "keyword.control.from",
        "keyword.control.as",
        "keyword.control.default",
        "keyword.control.new",
        "keyword.control.exception",
        "keyword.control.trycatch",
        "keyword.operator",
        "keyword.operator.assignment",
        "keyword.operator.comparison",
        "keyword.operator.logical",
        "keyword.operator.relational",
        "keyword.operator.arithmetic",
        "keyword.operator.spread",
        "keyword.operator.rest",
        "keyword.operator.type",
        "keyword.operator.expression.typeof",
        "keyword.operator.expression.instanceof",
        "keyword.operator.expression.keyof",
        "keyword.operator.expression.in",
        "keyword.operator.expression.delete",
        "keyword.operator.expression.void",
        "keyword.operator.ternary",
        "keyword.operator.quantifier.regexp",
        "keyword.other",
        "keyword.other.unit",
        "keyword.other.unsafe",
    ],
    "markup": [
        "markup.heading",
        "markup.heading.setext",
        "markup.bold",
        "markup.italic",
        "markup.strikethrough",
        "markup.underline",
        "markup.underline.link",
        "markup.quote",
        "markup.inline.raw",
        "markup.fenced_code",
        "markup.fenced_code.block",
        "markup.raw.block",
        "markup.list",
        "markup.list.numbered",
        "markup.list.unnumbered",
        "markup.inserted",
        "markup.deleted",
        "markup.changed",
        "markup.separator",
    ],
    "meta": [
        "meta.function-call",
        "meta.function",
        "meta.class",
        "meta.block",
        "meta.return.type",
        "meta.object-literal.key",
        "meta.template.expression",
        "meta.embedded",
        "meta.embedded.line",
        "meta.parameter",
        "meta.type.parameters",
        "meta.brace",
        "meta.brace.round",
        "meta.brace.square",
        "meta.brace.curly",
        "meta.decorator",
        "meta.annotation",
        "meta.link.inline",
        "meta.link.inline.uri",
        "meta.diff.header",
        "meta.diff.range",
        "meta.diff.index",
        "meta.structure.dictionary.key",
        "meta.macro.rules",
        "meta.attribute",
        "meta.fstring",
        "meta.property-value",
    ],
    "punctuation": [
        "punctuation",
        "punctuation.separator",
        "punctuation.terminator",
        "punctuation.accessor",
        "punctuation.definition.parameters",
        "punctuation.definition.block",
        "punctuation.definition.comment",
        "punctuation.definition.tag",
        "punctuation.definition.tag.begin",
        "punctuation.definition.tag.end",
        "punctuation.definition.template-expression",
        "punctuation.definition.template-expression.begin",
        "punctuation.definition.template-expression.end",
        "punctuation.definition.variable",
        "punctuation.definition.decorator",
        "punctuation.definition.annotation",
        "punctuation.definition.anchor",
        "punctuation.definition.attribute",
        "punctuation.definition.lifetime",
        "punctuation.definition.list.begin",
        "punctuation.definition.expression",
        "punctuation.definition.to-file.diff",
        "punctuation.definition.from-file.diff",
        "punctuation.section",
    ],
    "storage": [
        "storage.type",
        "storage.type.class",
        "storage.type.function",
        "storage.type.interface",
        "storage.type.enum",
        "storage.type.struct",
        "storage.type.annotation",
        "storage.modifier",
        "storage.modifier.async",
        "storage.modifier.static",
        "storage.modifier.readonly",
        "storage.modifier.lifetime",
        "storage.modifier.unsafe",
    ],
    "string": [
        "string",
        "string.quoted",
        "string.quoted.single",
        "string.quoted.double",
        "string.quoted.triple",
        "string.quoted.docstring",
        "string.quoted.double.html",
        "string.template",
        "string.regexp",
        "string.interpolated",
        "string.other.link",
        "string.value.json",
        "string.quoted.double.json",
    ],
    "support": [
        "support.function",
        "support.function.magic",
        "support.function.builtin",
        "support.function.macro",
        "support.function.css",
        "support.function.transform",
        "support.type",
        "support.type.builtin",
        "support.type.property-name",
        "support.type.property-name.json",
        "support.type.property-name.toml",
        "support.type.property-name.css",
        "support.type.property-name.table.toml",
        "support.type.vendored.property-name",
        "support.class",
        "support.class.component",
        "support.constant",
        "support.constant.property-value",
        "support.constant.font-name",
        "support.variable",
        "support.other",
    ],
    "variable": [
        "variable",
        "variable.other",
        "variable.other.readwrite",
        "variable.other.object",
        "variable.other.constant",
        "variable.other.property",
        "variable.other.enummember",
        "variable.other.normal",
        "variable.other.alias",
        "variable.other.receiver",
        "variable.parameter",
        "variable.parameter.function",
        "variable.language",
        "variable.language.this",
        "variable.language.self",
        "variable.language.super",
    ],
    # ── Language-Specific Categories ────────────────────────────────────────
    "source-specific": [
        # SQL
        "keyword.other.DML.sql",
        "keyword.other.DDL.sql",
        "keyword.other.data-integrity.sql",
        "keyword.other.sql",
        "constant.other.database-name.sql",
        "constant.other.table-name.sql",
        "support.function.aggregate.sql",
        "support.function.scalar.sql",
        "support.function.string.sql",
        # Docker
        "keyword.other.special-method.dockerfile",
        # Shell
        "variable.other.normal.shell",
        "punctuation.definition.variable.shell",
        # C/C++
        "keyword.control.directive.include",
        "keyword.control.directive.define",
        "keyword.control.directive.conditional",
        "entity.name.function.preprocessor",
        "meta.preprocessor",
        # PHP
        "variable.other.php",
        "punctuation.definition.variable.php",
        "storage.type.class.php",
        # Ruby
        "variable.other.readwrite.instance.ruby",
        "variable.other.readwrite.class.ruby",
        "punctuation.definition.variable.ruby",
        "keyword.control.class.ruby",
    ],
}

# ── VS Code Semantic Token Types (full set from LSP spec) ──────────────────
SEMANTIC_TOKEN_TYPES: list[str] = [
    "namespace",
    "type",
    "class",
    "enum",
    "interface",
    "struct",
    "typeParameter",
    "parameter",
    "variable",
    "property",
    "enumMember",
    "event",
    "function",
    "method",
    "macro",
    "keyword",
    "modifier",
    "comment",
    "string",
    "number",
    "regexp",
    "operator",
    "decorator",
    "label",
    "selfKeyword",
    "builtinType",
    "formatSpecifier",
    "lifetime",
    "generic",
    "angle",
    "boolean",
    "escapeSequence",
    "intrinsic",
    "constParameter",
    "unresolvedReference",
    "magicFunction",
    "parenthesis",
    "punctuation",
    "bitwise",
    "logical",
    "comparison",
    "colon",
    "semicolon",
    "comma",
    "dot",
    "arithmetic",
    "attributeBracket",
    "builtinAttribute",
    "toolModule",
    "derive",
    "deriveHelper",
    "procMacro",
]

# ── Semantic Token Modifiers ───────────────────────────────────────────────
SEMANTIC_TOKEN_MODIFIERS: list[str] = [
    "declaration",
    "definition",
    "readonly",
    "static",
    "deprecated",
    "abstract",
    "async",
    "modification",
    "documentation",
    "defaultLibrary",
    "mutable",
    "consuming",
    "callable",
    "controlFlow",
    "injected",
    "unsafe",
    "attribute",
    "trait",
    "library",
    "public",
    "reference",
    "crateRoot",
]


def load_theme(theme_path: Path) -> dict:
    """Load and parse theme JSON."""
    with open(theme_path, encoding="utf-8") as f:
        return json.load(f)


def extract_token_scopes(theme: dict) -> set[str]:
    """Extract all TextMate scopes from tokenColors array."""
    scopes: set[str] = set()
    for rule in theme.get("tokenColors", []):
        scope = rule.get("scope", [])
        if isinstance(scope, str):
            scopes.add(scope)
        elif isinstance(scope, list):
            for s in scope:
                scopes.add(s)
    return scopes


def extract_semantic_tokens(
    theme: dict, lsp_modifiers: list[str]
) -> dict[str, set[str]]:
    """Extract semantic token types and their modifiers from semanticTokenColors."""
    base_types: set[str] = set()
    modifiers_seen: set[str] = set()
    custom_modifiers: set[str] = set()
    lsp_mod_set = set(lsp_modifiers)

    for key in theme.get("semanticTokenColors", {}):
        # Keys can be: "type", "type.modifier", "*.modifier"
        if key.startswith("*."):
            modifier = key[2:]
            # Wildcard modifiers that match LSP spec count as LSP coverage
            if modifier in lsp_mod_set:
                modifiers_seen.add(modifier)
            else:
                custom_modifiers.add(modifier)
        elif "." in key:
            base_type, modifier = key.split(".", 1)
            base_types.add(base_type)
            modifiers_seen.add(modifier)
        else:
            base_types.add(key)

    return {
        "base_types": base_types,
        "modifiers": modifiers_seen,
        "custom_modifiers": custom_modifiers,
    }


def match_scope_to_category(scope: str, universe: dict[str, list[str]]) -> str | None:
    """Find which universe category a scope belongs to."""
    for category, scopes_in_cat in universe.items():
        for ref_scope in scopes_in_cat:
            if scope == ref_scope or scope.startswith(ref_scope + "."):
                return category
    # Fallback: match by top-level prefix
    top = scope.split(".")[0]
    if top in universe:
        return top
    return None


def audit_textmate_coverage(
    defined_scopes: set[str], universe: dict[str, list[str]]
) -> dict:
    """Audit which universe categories are covered/uncovered."""
    covered_categories: dict[str, list[str]] = {}
    uncategorized: list[str] = []

    for scope in sorted(defined_scopes):
        cat = match_scope_to_category(scope, universe)
        if cat:
            covered_categories.setdefault(cat, []).append(scope)
        else:
            uncategorized.append(scope)

    uncovered: list[str] = []
    partially_covered: dict[str, dict] = {}

    for category, scopes_list in universe.items():
        matched = covered_categories.get(category, [])
        if not matched:
            uncovered.append(category)
        else:
            unmatched = [s for s in scopes_list if s not in defined_scopes]
            if unmatched:
                partially_covered[category] = {
                    "covered_count": len(matched),
                    "total_in_universe": len(scopes_list),
                    "missing_scopes": unmatched,
                }

    return {
        "covered_categories": covered_categories,
        "uncovered_categories": uncovered,
        "partially_covered": partially_covered,
        "uncategorized_scopes": uncategorized,
    }


def audit_semantic_coverage(
    defined: dict[str, set[str]],
    lsp_types: list[str],
    lsp_modifiers: list[str],
) -> dict:
    """Audit semantic token type and modifier coverage."""
    covered_types = defined["base_types"] & set(lsp_types)
    uncovered_types = set(lsp_types) - defined["base_types"]
    covered_mods = defined["modifiers"] & set(lsp_modifiers)
    uncovered_mods = set(lsp_modifiers) - defined["modifiers"]

    return {
        "covered_types": sorted(covered_types),
        "uncovered_types": sorted(uncovered_types),
        "coverage_pct": (
            len(covered_types) / len(lsp_types) * 100 if lsp_types else 0
        ),
        "covered_modifiers": sorted(covered_mods),
        "uncovered_modifiers": sorted(uncovered_mods),
        "modifier_coverage_pct": (
            len(covered_mods) / len(lsp_modifiers) * 100 if lsp_modifiers else 0
        ),
        "custom_modifiers": sorted(defined["custom_modifiers"]),
    }


def format_report(
    textmate_audit: dict,
    semantic_audit: dict,
    scope_count: int,
    semantic_count: int,
) -> str:
    """Format the coverage audit report."""
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("  SFS TOKEN SCOPE COVERAGE AUDIT — Stage 4.0")
    lines.append("=" * 72)
    lines.append("")

    # ── Summary ────────────────────────────────────────────────────────
    lines.append("## Summary")
    lines.append(f"  TextMate tokenColor rules:     {scope_count}")
    lines.append(f"  Semantic token definitions:     {semantic_count}")
    lines.append("")

    # ── TextMate Coverage ──────────────────────────────────────────────
    total_cats = len(TEXTMATE_UNIVERSE)
    covered_cats = len(textmate_audit["covered_categories"])
    uncovered_cats = len(textmate_audit["uncovered_categories"])
    partial_cats = len(textmate_audit["partially_covered"])

    lines.append("## TextMate Scope Coverage")
    lines.append(f"  Categories in universe:        {total_cats}")
    textmate_pct = covered_cats / total_cats * 100 if total_cats else 0
    lines.append(f"  Fully/partially covered:       {covered_cats}/{total_cats} ({textmate_pct:.1f}%)")
    lines.append(f"  Completely uncovered:           {uncovered_cats}")
    lines.append("")

    if textmate_audit["uncovered_categories"]:
        lines.append("  ### UNCOVERED CATEGORIES (no rules at all)")
        for cat in sorted(textmate_audit["uncovered_categories"]):
            lines.append(f"    ✗ {cat}")
        lines.append("")

    if textmate_audit["partially_covered"]:
        lines.append("  ### PARTIALLY COVERED (some scopes missing)")
        for cat, info in sorted(textmate_audit["partially_covered"].items()):
            pct = info["covered_count"] / info["total_in_universe"] * 100
            lines.append(
                f"    ◐ {cat}: {info['covered_count']}/{info['total_in_universe']} ({pct:.0f}%)"
            )
            for s in info["missing_scopes"][:8]:
                lines.append(f"      - {s}")
            if len(info["missing_scopes"]) > 8:
                lines.append(
                    f"      ... and {len(info['missing_scopes']) - 8} more"
                )
        lines.append("")

    lines.append("  ### COVERED CATEGORIES")
    for cat, scopes in sorted(textmate_audit["covered_categories"].items()):
        lines.append(f"    ✓ {cat} ({len(scopes)} scopes)")
    lines.append("")

    if textmate_audit["uncategorized_scopes"]:
        lines.append("  ### UNCATEGORIZED (defined but not in universe reference)")
        for s in sorted(textmate_audit["uncategorized_scopes"]):
            lines.append(f"    ? {s}")
        lines.append("")

    # ── Semantic Token Coverage ────────────────────────────────────────
    lines.append("## Semantic Token Coverage")
    lines.append(
        f"  LSP types covered:             {len(semantic_audit['covered_types'])}/{len(SEMANTIC_TOKEN_TYPES)} "
        f"({semantic_audit['coverage_pct']:.1f}%)"
    )
    lines.append(
        f"  LSP modifiers covered:         {len(semantic_audit['covered_modifiers'])}/{len(SEMANTIC_TOKEN_MODIFIERS)} "
        f"({semantic_audit['modifier_coverage_pct']:.1f}%)"
    )
    lines.append(
        f"  Custom modifiers (SFS):        {len(semantic_audit['custom_modifiers'])}"
    )
    lines.append("")

    if semantic_audit["uncovered_types"]:
        lines.append("  ### UNCOVERED SEMANTIC TYPES")
        for t in semantic_audit["uncovered_types"]:
            lines.append(f"    ✗ {t}")
        lines.append("")

    if semantic_audit["uncovered_modifiers"]:
        lines.append("  ### UNCOVERED SEMANTIC MODIFIERS")
        for m in semantic_audit["uncovered_modifiers"]:
            lines.append(f"    ✗ {m}")
        lines.append("")

    if semantic_audit["custom_modifiers"]:
        lines.append("  ### CUSTOM SFS MODIFIERS (not in LSP spec)")
        for m in semantic_audit["custom_modifiers"]:
            lines.append(f"    ☥ {m}")
        lines.append("")

    lines.append("=" * 72)
    lines.append("  END OF AUDIT")
    lines.append("=" * 72)

    return "\n".join(lines)


def main() -> int:
    import argparse
    import urllib.request

    repo_root = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description="SFS Token Scope Coverage Audit")
    parser.add_argument("--theme", metavar="PATH",
                        help="Path to a theme JSON file to audit (default: geology theme)")
    parser.add_argument("--update-universe", action="store_true",
                        help="Fetch updated TextMate scope universe from vscode-textmate GitHub and write to data/indices/textmate_universe.json")
    args = parser.parse_args()

    if args.update_universe:
        _URL = (
            "https://raw.githubusercontent.com/microsoft/vscode-textmate/main/src/grammar.ts"
        )
        out_dir = repo_root / "data" / "indices"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "textmate_universe_raw.ts"
        print(f"Fetching TextMate grammar source: {_URL} ...")
        try:
            with urllib.request.urlopen(_URL, timeout=15) as resp:  # noqa: S310
                content = resp.read().decode("utf-8")
            out_path.write_text(content, encoding="utf-8")
            print(f"Written: {out_path}")
            print("NOTE: Universe raw source fetched — parse manually or run scope extractor.")
        except Exception as e:
            print(f"ERROR fetching universe: {e}", file=sys.stderr)
            return 1
        return 0

    if args.theme:
        theme_path = Path(args.theme)
    else:
        theme_path = (
            repo_root
            / "extensions"
            / "chthonic-archive"
            / "themes"
            / "chthonic-geology-color-theme.json"
        )

    if not theme_path.exists():
        print(f"ERROR: Theme file not found: {theme_path}", file=sys.stderr)
        return 1

    theme = load_theme(theme_path)

    # Extract
    defined_scopes = extract_token_scopes(theme)
    semantic_defs = extract_semantic_tokens(theme, SEMANTIC_TOKEN_MODIFIERS)

    scope_count = len(theme.get("tokenColors", []))
    semantic_count = len(theme.get("semanticTokenColors", {}))

    # Audit
    textmate_audit = audit_textmate_coverage(defined_scopes, TEXTMATE_UNIVERSE)
    semantic_audit = audit_semantic_coverage(
        semantic_defs, SEMANTIC_TOKEN_TYPES, SEMANTIC_TOKEN_MODIFIERS
    )

    # Report
    report = format_report(textmate_audit, semantic_audit, scope_count, semantic_count)
    print(report)

    # Also dump JSON for machine consumption
    json_out = theme_path.parent.parent / "audit-reports" / "token_coverage_audit.json"
    audit_data = {
        "textmate": {
            "rule_count": scope_count,
            "unique_scopes": len(defined_scopes),
            "covered_categories": list(textmate_audit["covered_categories"].keys()),
            "uncovered_categories": textmate_audit["uncovered_categories"],
            "partially_covered": {
                k: {
                    "covered": v["covered_count"],
                    "total": v["total_in_universe"],
                    "missing": v["missing_scopes"],
                }
                for k, v in textmate_audit["partially_covered"].items()
            },
        },
        "semantic": {
            "definition_count": semantic_count,
            "covered_types": semantic_audit["covered_types"],
            "uncovered_types": semantic_audit["uncovered_types"],
            "type_coverage_pct": round(semantic_audit["coverage_pct"], 1),
            "covered_modifiers": semantic_audit["covered_modifiers"],
            "uncovered_modifiers": semantic_audit["uncovered_modifiers"],
            "modifier_coverage_pct": round(
                semantic_audit["modifier_coverage_pct"], 1
            ),
            "custom_modifiers": semantic_audit["custom_modifiers"],
        },
    }
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"\nJSON audit data written to: {json_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
