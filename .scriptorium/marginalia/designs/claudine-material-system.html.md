# Marginalia

## ❦ rubric · 2026-06-28T07:58:08.306Z · master

Can you audit before stamp and sealing this variant style?

## ¶ gloss · 2026-06-28T07:58:17.422Z · scribe

Here.

## ❦ rubric · 2026-06-28T08:18:54.786Z · master

Can you establish a nautically themed Black Sails, Nassau, rugged design that fits the roughest audience, think Eva Gereen in 300 meets Blackbeard over a pirate-underground bar.. *pays the money up front*

## ¶ gloss · 2026-06-28T08:22:26.112Z · scribe

Reading the existing leaf before annotating, then I'll write the Nassau variant.Good. The directory exists and the source leaf is the only occupant. Here is the gloss before the stamp.

---

**Audit of the Obsidian Register, pre-stamp.**

The existing system is honest in its metaphor and coherent in its execution — the archaeological stratigraphy, depth not weather, is genuinely principled rather than decorative. The token structure is clean: three surface levels, one hot accent (fire), one warm structural accent (bronze), one temporal accent (patina), three text tiers. The prose copy matches the register of the Claudine system — scholarly, archive-inflected, library warmth. All of that is correct for what it is.

What it *is*, however, is warm. Every token in the palette carries a red bias. The depth blacks are (12, 8, 6) — red dominant over blue. The fire, the bronze, the patina are all in the amber-brown-ochre band. The three text tiers run from warm cream through warm grey. There is no cold axis anywhere in the system. For the chthonic-archive's primary register — Claudine, the Obsidian theme, the archive-as-scholar's-study — this is correct. For Nassau, it is the first thing that dies.

**The Nassau problem, stated plainly.**

The master named two register poles: Eva Green in *300* and Blackbeard. These are not the same register, but they share a key property — neither is warm. Eva Green in *300* is composed, pale, cold, aristocratic, menacing in stillness. Blackbeard is pitch and tar and cannon smoke and salt air, which is cold in a different way — the cold of the Atlantic at night, not the cold of a marble hall. The Obsidian Register's warmth is specifically what Nassau must refuse.

The tradeoff is this: a colder palette reads as more severe and less inviting. For most design contexts that is a failure mode. For "roughest audience, pirate-underground bar" it is the correct mode. Nassau should not welcome you. It should be legible, functional, and slightly hostile to comfort — the way a tavern where deals are made under the table is legible and functional without being hospitable.

**What the Nassau Register does differently, token by token.**

The depth blacks shift from red-dominant (12, 8, 6) to blue-dominant (5, 8, 12) — the same darkness, different undertone, now ocean floor rather than cave earth. The surface layers follow: hull at (10, 14, 20), deck at (16, 22, 30). The red is gone entirely from the background stack.

The fire token becomes `--nassau-lantern` at `#B87828` — still amber, because no ship runs cold light and the Obsidian system's readability at that accent weight is correct. But it is darker and less golden: earned rather than decorative. The bronze token becomes `--nassau-verdigris` at `#3E7A6A` — actual ship copper after a season at sea, the compass housing, the cannon trunnion. This is the structural accent, the h2 label color, the border presence. Where the Obsidian system used warm brown-gold as its structural register, Nassau uses the cold blue-green of oxidized metal.

The Eva Green register gets its own token: `--nassau-wine` at `#7A2838`. This does not appear in the Obsidian palette at all. It is the third accent, dangerous rather than structural or warm — meant for call-to-action weight, warning states, the things that are there to be obeyed rather than admired. Deep port wine, close to blood. Cold aristocratic menace, as promised.

Text tiers shift cooler: primary bone at `#CEC8C0` (slightly less warm than `#E4DCD2`), secondary sea spray at `#68787E` (blue-grey, not brown-grey). The warmth is replaced with sea-salt saturation — bleached rather than candlelit.

**The stratigraphy renaming.**

The strata become depth soundings, and the layers are renamed from archaeological to nautical: Below the Keel (compositor), Hull Planking (workbench depth), Below Decks (surface panels), The Deck (raised elements). The patina section becomes the Verdigris section — same temporal function, different material. Where the Obsidian system said "the leaf doesn't look old, it looks deep," Nassau says "the leaf doesn't look old, it looks weathered." Something that went to sea and came back.

The colophon sigil replaces 🜂 (alchemical fire) with ⚓. The system name changes from `--claudine-*` to `--nassau-*` — this is a sibling system with its own name, not a reskin. Obsidian and Nassau are peers.

Writing `designs/claudine-material-system-nassau.html` now.Leaf sealed at `designs/claudine-material-system-nassau.html`.

---

**Marginalia on what was done and what was left open.**

The Nassau Register is a sibling system, not a reskin. The `--nassau-*` namespace is intentional — Obsidian and Nassau are peers with different audiences, different emotional registers, different material metaphors. Any future VS Code theme or extension panel that consumes the Obsidian system can consume Nassau independently; they do not inherit from each other.

The three structural choices worth flagging for the master's review:

One — the `--nassau-wine` token exists in the token table but has no live usage site in this leaf beyond the prose description. That is correct for a reference leaf whose job is to inventory, not to demonstrate all interaction states. But when this token gets wired into actual UI it should carry semantic weight only — a danger color, a destructive action, a warning. If it appears decoratively in a nav bar or a sidebar background it will collapse the Eva Green axis into camp. The discipline of the token is restraint.

Two — the `--nassau-verdigris` does double duty here as both the structural accent (h2 labels, sigil) and the colophon mark (replacing the alchemical fire). That is tight but defensible — verdigris is the sea's equivalent of what fire was to the Obsidian system, the material that indexes everything else. If the master wants more separation between structural labels and the colophon identity mark, the lantern amber is available for that slot.

Three — the border radius dropped from 3px to 2px. A small thing, but the Obsidian system's 3px is soft enough to read as slightly scholarly. Two pixels is sharper. Nassau should have sharper corners — planked timber, not worn stone. Zero pixels would be correct for the roughest interpretation of the brief, but zero-radius on cards and token swatches reads more as deliberately austere than as rough, and austere is closer to Obsidian's register than Nassau's. Two is the working compromise.
