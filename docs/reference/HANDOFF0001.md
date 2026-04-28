
---

# Implementing Structural Intervention (Option A)

To execute Option A, we will augment the master instructions file (`.github/copilotinstructions.md`) with hidden HTML anchors and update each branch file to link to those anchors. Specifically, we will:

* Insert HTML comment anchors at each major section of the SSOT file.
* Transform branch instructions (e.g., `20_rust.instructions.md`) into a referential view that points to the SSOT.
* Document the linking system so maintainers understand the convention.

This approach centralizes content in one “single source of truth” (SSOT) and avoids duplication. The strategy of using HTML anchors is supported by documentation tools (e.g., the “Documentation Anchor Suggester” recommends inserting comments like `` to create stable, hidden anchors in Markdown) which can then be pointed to. [mcpmarket.com](https://mcpmarket.com)

## 1. Insert HTML comment anchors in the SSOT file

We will edit `copilot-instructions.md` and add a unique HTML comment before each section heading. For example:

```markdown
# Section 0: Foundational Architecture
... content of Section 0 ...

## Section 1: K-Cup Hierarchy
... content of Section 1 ...

```

Each comment (`e.g.,`) serves as a hidden anchor. This does not appear in rendered output, but tools and Markdown parsers will recognize the anchor label. This technique is analogous to using named HTML anchor tags in Markdown. For instance, one StackOverflow answer shows that you can insert an anchor point by adding an HTML tag like `<a name="tith"></a>` before a header [stackoverflow.com](https://stackoverflow.com).

By contrast, our approach uses the HTML comment format shown above. The Anchor Suggester documentation even enforces a standard uppercase-hyphen naming convention for such anchors.

By anchoring each section, we ensure that we have stable reference points. (Optionally, we can also include a one-line description or unique ID in each comment for clarity.) After this step, the SSOT will still contain all original content, just with added `` markers before headings.

## 2. Transform branch instructions into referential links

Each branch-specific instructions file (like `20_rust.instructions.md`) will be rewritten to link back to the SSOT rather than duplicate content. In practice, we replace the detailed prose with brief references. For example, instead of repeating the “Prime Factions” details, the branch file might say:

```markdown
For details on Prime Factions (see Section 2 of the SSOT), refer to [Section 2](#Section-2-PR-FNS)

```

Here `#Section-2-PR-FNS` matches the HTML comment anchor `` we placed in `copilot-instructions.md`. When rendered, this becomes a link to the SSOT’s Section 2 heading.

Alternatively, if we split content into separate instruction files, the branch file can link to that file. For instance, the GitHub community solution for Copilot instructions shows using a markdown link like `[Xyz instruction file](instructions/xyz.instructions.md)` to refer to another instructions document [github.com](https://github.com).

In our case, we can either keep everything in one file (using fragment links `#Section-X`) or mirror that approach by moving some sections into `instructions/kcup.instructions.md` and linking to it. The key is: all substantive content stays in one place, and branch files simply point to it.

**In practice we will:**

* Remove or comment out the original table/section content in each branch file.
* Add bullet lists or statements that say “See Section N – Title in the SSOT.”
* If a branch had its own `.instructions.md`, we can either delete it (letting Copilot fallback to SSOT) or keep a stub that just links out.

This ensures consistency. As one expert advises, “Split the main `copilot-instructions.md` into multiple files and place those in an instructions folder. Now I add a reference to particular file this way: For Xyz details, refer [Xyz instruction file](https://www.google.com/search?q=instructions/xyz.instructions.md)” [github.com](https://github.com). We adapt this by pointing to our anchors.

## 3. Document the new structure and responsibilities

Finally, we’ll add a brief note at the top of the SSOT to explain this system. For example, an HTML comment or prose box like:

> **Note:** This instructions file is the single source of truth for Copilot. Section anchors (see `` comments) allow branch files to link here. Branch-specific instructions should reference sections above rather than duplicating content.

We should also indicate who is responsible for maintaining each section. Best practices for a Single Source of Truth (SSoT) suggest adding metadata or an “info panel” at the top of each document to show update responsibility [atlassian.com](https://www.atlassian.com).

```markdown

```

Or a Markdown info box. This makes clear how to handle future edits.

In summary, executing Option A means that `copilot-instructions.md` becomes the authoritative document (with HTML comment anchors marking each section), and each branch file is reduced to cross-references (e.g. via markdown links) to those anchors. This preserves a single source of truth while still allowing modular access. The use of HTML comment anchors for cross-referencing is a known technique in documentation tooling, and linking instruction files by path is supported in GitHub Copilot’s custom instructions model.

## Next Steps

1. **Apply these changes to the files.**
2. After inserting anchors and updating the branch `.instructions.md` files with links, verify by loading Copilot (or the relevant tool) and ensuring it sees the updated content via the links.
3. All references should now resolve to the anchored sections in the SSOT.

## References

The anchor-insertion method is described in documentation tooling guides. The linking strategy for Copilot instruction files is illustrated in GitHub community discussions. Our approach follows these practices.

### Citations

* [Anchor Suggester - Documentation Aid | Claude Code Skill](https://mcpmarket.com/tools/skills/documentation-anchor-suggester)
* [html - Cross-reference (named anchor) in markdown - Stack Overflow](https://stackoverflow.com/questions/5319754/cross-reference-named-anchor-in-markdown)
* [Referencing multiple Instruction MDs conditionally. · community · Discussion #1…](https://github.com/orgs/community/discussions/162201)
* [Single Source of Truth [+ How to Build One] | The Workstream](https://www.atlassian.com/work-management/knowledge-sharing/documentation/building-a-single-source-of-truth-ssot-for-your-team)

### All Sources

* mcpmarket
* stackoverflow
* github
* atlassian

---