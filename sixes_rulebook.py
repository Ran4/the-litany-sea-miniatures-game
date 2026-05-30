# /// script
# requires-python = ">=3.11"
# dependencies = ["python-docx"]
# ///
"""
SIXES - A Fast Skirmish Wargame
Rulebook generator. Run with:  uv run sixes_rulebook.py
Produces sixes_rulebook.docx (then convert to PDF with soffice).
"""

from docx import Document
from docx.shared import Pt, Mm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ---- palette -----------------------------------------------------------------
INK     = RGBColor(0x20, 0x20, 0x20)
ACCENT  = RGBColor(0x8B, 0x1A, 0x1A)   # deep red
STEEL   = RGBColor(0x33, 0x4E, 0x5C)   # slate blue
GREY    = RGBColor(0x5A, 0x5A, 0x5A)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
HDR_FILL   = "334E5C"   # steel header fill
ZEBRA_FILL = "EDEFF1"   # light row stripe
BOX_FILL   = "F3EEE6"   # parchment callout

BODY_FONT = "Calibri"
HEAD_FONT = "Calibri"


# ---- low-level helpers -------------------------------------------------------
def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def cell_text(cell, text, bold=False, color=None, align=None, size=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    if align is not None:
        p.alignment = align
    run = p.add_run(text)
    run.font.name = BODY_FONT
    run.bold = bold
    if size:
        run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = color
    return run


def set_col_widths(table, widths):
    table.autofit = False
    for row in table.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = w


def add_table(doc, headers, rows, widths=None, font_size=10):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # header
    for i, h in enumerate(headers):
        c = table.rows[0].cells[i]
        shade(c, HDR_FILL)
        cell_text(c, h, bold=True, color=WHITE, size=font_size,
                  align=WD_ALIGN_PARAGRAPH.CENTER)
    # body
    for r_idx, row in enumerate(rows):
        cells = table.add_row().cells
        for i, val in enumerate(row):
            align = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
            cell_text(cells[i], str(val), size=font_size, align=align)
            if r_idx % 2 == 1:
                shade(cells[i], ZEBRA_FILL)
    if widths:
        set_col_widths(table, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return table


def heading(doc, text, level=1):
    if level == 1:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text.upper())
        run.font.name = HEAD_FONT
        run.font.size = Pt(17)
        run.font.bold = True
        run.font.color.rgb = ACCENT
        # bottom rule
        pPr = p._p.get_or_add_pPr()
        pbdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "12")
        bottom.set(qn("w:space"), "3")
        bottom.set(qn("w:color"), "8B1A1A")
        pbdr.append(bottom)
        pPr.append(pbdr)
        return p
    else:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(text)
        run.font.name = HEAD_FONT
        run.font.size = Pt(12.5)
        run.font.bold = True
        run.font.color.rgb = STEEL
        return p


def body(doc, text, size=10.5, space_after=6, italic=False, align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.08
    if align is not None:
        p.alignment = align
    # support **bold** inline markers
    parts = text.split("**")
    for i, seg in enumerate(parts):
        if seg == "":
            continue
        run = p.add_run(seg)
        run.font.name = BODY_FONT
        run.font.size = Pt(size)
        run.font.color.rgb = INK
        run.italic = italic
        if i % 2 == 1:
            run.bold = True
    return p


def bullet(doc, text, size=10.5):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    parts = text.split("**")
    for i, seg in enumerate(parts):
        if seg == "":
            continue
        run = p.add_run(seg)
        run.font.name = BODY_FONT
        run.font.size = Pt(size)
        run.font.color.rgb = INK
        if i % 2 == 1:
            run.bold = True
    return p


def numbered(doc, text, size=10.5):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.space_after = Pt(2)
    parts = text.split("**")
    for i, seg in enumerate(parts):
        if seg == "":
            continue
        run = p.add_run(seg)
        run.font.name = BODY_FONT
        run.font.size = Pt(size)
        run.font.color.rgb = INK
        if i % 2 == 1:
            run.bold = True
    return p


def callout(doc, title, text):
    """A shaded single-cell box for designer notes / examples."""
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.rows[0].cells[0]
    shade(cell, BOX_FILL)
    cell.width = Mm(170)
    # left accent border
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "24")
    left.set(qn("w:space"), "0")
    left.set(qn("w:color"), "8B1A1A")
    borders.append(left)
    tcPr.append(borders)

    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(title.upper())
    r.bold = True
    r.font.size = Pt(10)
    r.font.name = BODY_FONT
    r.font.color.rgb = ACCENT

    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(2)
    parts = text.split("**")
    for i, seg in enumerate(parts):
        if seg == "":
            continue
        run = p2.add_run(seg)
        run.font.name = BODY_FONT
        run.font.size = Pt(10)
        run.font.color.rgb = INK
        if i % 2 == 1:
            run.bold = True
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


# ---- document setup ----------------------------------------------------------
doc = Document()

normal = doc.styles["Normal"]
normal.font.name = BODY_FONT
normal.font.size = Pt(10.5)
normal.font.color.rgb = INK

sec = doc.sections[0]
sec.page_height = Mm(297)
sec.page_width = Mm(210)
sec.top_margin = Inches(0.75)
sec.bottom_margin = Inches(0.7)
sec.left_margin = Inches(0.85)
sec.right_margin = Inches(0.85)

# footer
footer_p = sec.footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
fr = footer_p.add_run("SIXES — A Fast Skirmish Wargame  ·  v1.0")
fr.font.size = Pt(8)
fr.font.color.rgb = GREY
fr.font.name = BODY_FONT


# ============================================================ TITLE PAGE
for _ in range(4):
    doc.add_paragraph()

t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
tr = t.add_run("SIXES")
tr.font.name = HEAD_FONT
tr.font.size = Pt(80)
tr.font.bold = True
tr.font.color.rgb = ACCENT

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sr = sub.add_run("A  F A S T   S K I R M I S H   W A R G A M E")
sr.font.name = HEAD_FONT
sr.font.size = Pt(16)
sr.font.bold = True
sr.font.color.rgb = STEEL

doc.add_paragraph()
tag = doc.add_paragraph()
tag.alignment = WD_ALIGN_PARAGRAPH.CENTER
tgr = tag.add_run("Roll dice. Move models. No spreadsheet required.")
tgr.italic = True
tgr.font.size = Pt(13)
tgr.font.color.rgb = GREY

for _ in range(6):
    doc.add_paragraph()

need = doc.add_paragraph()
need.alignment = WD_ALIGN_PARAGRAPH.CENTER
nr = need.add_run("ALL YOU NEED")
nr.bold = True
nr.font.size = Pt(11)
nr.font.color.rgb = ACCENT
for line in [
    "A handful of six-sided dice  ·  A tape measure",
    "Some terrain  ·  Two warbands of miniatures  ·  A friend",
]:
    pp = doc.add_paragraph()
    pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = pp.add_run(line)
    rr.font.size = Pt(11)
    rr.font.color.rgb = INK

for _ in range(5):
    doc.add_paragraph()
ver = doc.add_paragraph()
ver.alignment = WD_ALIGN_PARAGRAPH.CENTER
vr = ver.add_run("Complete Rules  ·  Version 1.0")
vr.font.size = Pt(10)
vr.font.color.rgb = GREY

doc.add_page_break()


# ============================================================ CONTENTS
heading(doc, "Contents", 1)
contents = [
    "1.  The Idea Behind SIXES",
    "2.  What You Need & Core Concepts",
    "3.  Reading a Model Profile",
    "4.  Building a Warband",
    "5.  Weapons",
    "6.  Setting Up the Battlefield",
    "7.  The Game Round",
    "8.  Activations & Actions",
    "9.  Movement",
    "10. Shooting",
    "11. Line of Sight & Cover",
    "12. Fighting (Melee)",
    "13. Damage & Wounds",
    "14. Nerve (Morale)",
    "15. Winning the Game",
    "16. Scenario: Hold the Line",
    "17. Designer's Notes — Why So Few Modifiers",
    "18. Quick Reference (print this page)",
]
for c in contents:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(c)
    r.font.size = Pt(11.5)
    r.font.color.rgb = INK

doc.add_page_break()


# ============================================================ 1. THE IDEA
heading(doc, "1.  The Idea Behind SIXES", 1)
body(doc, "SIXES is a skirmish wargame for two players, each commanding a small "
          "warband of 4–8 miniatures. A game takes 30–60 minutes and fits on a "
          "small table (about 90 × 90 cm / 3 × 3 feet).")
body(doc, "The whole game runs on ordinary six-sided dice. There is one number "
          "you ever try to roll: a model's **target number**. Roll that number or "
          "higher and you succeed. That's it.")
body(doc, "Most skirmish games drown you in arithmetic — base 4+, minus one for "
          "cover, plus one for aiming, minus one because the target moved, and so "
          "on until you've done five sums to throw one die. SIXES refuses to do "
          "that. The whole game has only a **handful of modifiers**, each tied to "
          "something you can see on the table, and they never stack into a maths "
          "problem. If you can count to six, you can play.")
callout(doc, "The one promise",
        "You will never add and subtract a chain of modifiers that cancel each "
        "other out. Every modifier in SIXES changes the game in a way you can "
        "feel — or it isn't in the game.")


# ============================================================ 2. CONCEPTS
heading(doc, "2.  What You Need & Core Concepts", 1)
heading(doc, "Dice", 2)
body(doc, "You only need six-sided dice (**D6**). Grab a fistful — a dozen is plenty.")
body(doc, "A few heavy weapons roll a **D3**. To roll a D3, roll a D6 and read it "
          "like this:")
add_table(doc,
          ["D6 result", "1 – 2", "3 – 4", "5 – 6"],
          [["D3 value", "1", "2", "3"]],
          widths=[Mm(40), Mm(35), Mm(35), Mm(35)])

heading(doc, "Rolling to succeed", 2)
body(doc, "Whenever you roll, you are trying to **meet or beat a target number**. "
          "A target of 4+ means any die showing 4, 5 or 6 succeeds. A natural **6 "
          "always succeeds** and a natural **1 always fails**, whatever the target.")

heading(doc, "Measuring", 2)
body(doc, "Distances are in **inches** (use cm at 1\" ≈ 2.5 cm if you prefer). "
          "Measure from the nearest edge of a model's base to the nearest edge of "
          "the other model's base. You may **measure anything at any time** — no "
          "guessing, no gotchas.")

heading(doc, "Models & bases", 2)
body(doc, "Each miniature is a single **model** on a base. A model is either "
          "standing (normal) or removed (dead). Two models are **in base contact** "
          "when their bases touch — that's how you fight in melee.")


# ============================================================ 3. PROFILE
heading(doc, "3.  Reading a Model Profile", 1)
body(doc, "Every model has five numbers. That is the entire profile.")
add_table(doc,
          ["Stat", "Name", "What it does"],
          [
            ["M",   "Move",    "Inches the model moves with one Move action."],
            ["SK",  "Skill",   "Target number to hit — used for shooting AND fighting."],
            ["DEF", "Defense", "Target number to save against a hit."],
            ["W",   "Wounds",  "Hits the model takes before it is removed (usually 1)."],
            ["A",   "Attacks", "Dice the model rolls when it Fights in melee."],
          ],
          widths=[Mm(18), Mm(30), Mm(122)])
body(doc, "Lower is better for **SK** and **DEF** (3+ is better than 5+). Example "
          "profile written in shorthand:")
callout(doc, "Example — Veteran",
        "**M 5\"  ·  SK 3+  ·  DEF 4+  ·  W 1  ·  A 2.**  Moves 5 inches, hits on "
        "3+, saves on 4+, dies to one wound, throws 2 dice in a fight.")


# ============================================================ 4. WARBAND
heading(doc, "4.  Building a Warband", 1)
body(doc, "Spend **100 points** on models. Your warband must include exactly **one "
          "Leader**. A typical warband is 5–8 models. To play a quick first game, "
          "just give each side the same models and skip the points.")
add_table(doc,
          ["Archetype", "M", "SK", "DEF", "W", "A", "Weapons", "Pts"],
          [
            ["Leader",  '5"', "3+", "4+", "2", "2", "Rifle + Blade", "30"],
            ["Veteran", '5"', "3+", "4+", "1", "2", "Rifle + Blade", "18"],
            ["Grunt",   '5"', "4+", "5+", "1", "1", "Rifle + Blade", "10"],
            ["Scout",   '7"', "4+", "5+", "1", "1", "SMG",           "12"],
            ["Brute",   '6"', "4+", "4+", "2", "3", "Heavy Melee",   "20"],
            ["Heavy",   '4"', "4+", "3+", "2", "1", "Heavy Weapon",  "25"],
          ],
          widths=[Mm(28), Mm(14), Mm(14), Mm(16), Mm(12), Mm(12), Mm(50), Mm(14)],
          font_size=10)

heading(doc, "Special abilities", 2)
bullet(doc, "**Leader — Command:** Once per round, after any friendly model within "
            "6\" rolls to hit, that model may re-roll all of its missed hits from "
            "that one Shoot or Fight.")
bullet(doc, "**Scout — Infiltrate:** During deployment, place this model anywhere "
            "on the table more than 9\" from any enemy model.")
bullet(doc, "**Brute — Wrecker:** A Brute may re-roll the Damage die of its Heavy "
            "Melee weapon.")
body(doc, "That is the complete list of abilities. Each one does a single, obvious "
          "thing.", italic=True, size=9.5, space_after=4)


# ============================================================ 5. WEAPONS
heading(doc, "5.  Weapons", 1)
body(doc, "A weapon tells you its **Range**, how many **Shots** (dice) it fires, "
          "and its **Damage**. Melee weapons use the model's **A** stat instead of "
          "Shots.")
add_table(doc,
          ["Weapon", "Range", "Shots", "Damage", "Special"],
          [
            ["Pistol",       '12"', "1", "1",  "May fire while in base contact"],
            ["Rifle",        '24"', "1", "1",  "—"],
            ["SMG",          '18"', "3", "1",  "—"],
            ["Shotgun",      '12"', "2", "1",  "—"],
            ["Heavy Weapon", '30"', "1", "D3", "Heavy"],
            ["Sniper Rifle", '36"', "1", "D3", "Sniper"],
            ["Blade",        "Melee", "A", "1",  "—"],
            ["Heavy Melee",  "Melee", "A", "D3", "—"],
            ["Power Weapon", "Melee", "A", "1",  "Piercing"],
          ],
          widths=[Mm(30), Mm(22), Mm(20), Mm(22), Mm(76)],
          font_size=10)

heading(doc, "Weapon special rules — the complete list", 2)
bullet(doc, "**Heavy:** The model must spend the **Aim** action before firing this "
            "weapon (so it cannot move and shoot in the same activation).")
bullet(doc, "**Sniper:** Ignores the Cover bonus.")
bullet(doc, "**Piercing:** The target gets **no Defense save** against this hit.")
body(doc, "Three special rules. That's all of them.", italic=True, size=9.5,
     space_after=4)


# ============================================================ 6. BATTLEFIELD
heading(doc, "6.  Setting Up the Battlefield", 1)
numbered(doc, "Play on roughly a 3 × 3 ft area. Scatter **6–10 pieces of terrain** "
              "— walls, crates, ruins, woods. A table with plenty of cover plays "
              "far better than an empty one.")
numbered(doc, "Each player's **deployment zone** is the 6\" strip along their own "
              "table edge.")
numbered(doc, "Roll off (each rolls a D6, re-roll ties). The winner picks a table "
              "edge; the loser takes the opposite edge.")
numbered(doc, "Starting with the roll-off winner, players take turns placing **one "
              "model at a time** in their own deployment zone, until all models are "
              "down. (Scouts with Infiltrate are placed last.)")
numbered(doc, "Place objectives if the scenario uses them, then begin Round 1.")


# ============================================================ 7. ROUND
heading(doc, "7.  The Game Round", 1)
body(doc, "A game lasts **4 rounds** (play 5 for a bigger battle). Each round:")
numbered(doc, "**Initiative.** Both players roll a D6; highest chooses who "
              "activates first this round (re-roll ties).")
numbered(doc, "**Alternate activations.** Starting with that player, the two "
              "players take turns activating **one model each**. Keep alternating "
              "until every model has activated once.")
numbered(doc, "**End of round.** Resolve any end-of-round scenario scoring, then "
              "start the next round with a fresh Initiative roll.")
callout(doc, "Why alternating?",
        "You are never sitting and watching your opponent move their whole army. "
        "Something is always happening on your side of the table within seconds.")


# ============================================================ 8. ACTIONS
heading(doc, "8.  Activations & Actions", 1)
body(doc, "When you activate a model, it performs **two actions**. You may take the "
          "same action twice **only for Move**. So a model can Move twice (run), or "
          "Move then Shoot, or Aim then Shoot, or Move then Fight (a charge), and "
          "so on.")
add_table(doc,
          ["Action", "Effect"],
          [
            ["Move",  "Move up to M inches (see Movement)."],
            ["Shoot", "Fire one weapon at a target in range and line of sight. Once per activation."],
            ["Fight", "Attack an enemy in base contact. Once per activation."],
            ["Aim",   "Your next Shoot this activation ignores Cover and re-rolls one missed hit."],
            ["Rally", "Remove the Shaken condition from this model."],
          ],
          widths=[Mm(24), Mm(146)])
body(doc, "A model may **Shoot at most once** and **Fight at most once** per "
          "activation — there is no double-shooting. Beyond that, mix and match the "
          "two actions however you like.")


# ============================================================ 9. MOVEMENT
heading(doc, "9.  Movement", 1)
bullet(doc, "A **Move** action lets the model move up to **M inches** in any "
            "direction. Two Move actions (a run) cover up to 2 × M.")
bullet(doc, "Models may move over **low terrain** (walls, crates up to about 1\" "
            "tall) freely, and move **through** difficult terrain such as woods at "
            "half speed (count each inch as two).")
bullet(doc, "Models may **not** move through other models or off the table.")
bullet(doc, "To enter melee, simply Move into base contact with an enemy. Doing so "
            "this activation makes your following Fight a **Charge** (see Fighting).")


# ============================================================ 10. SHOOTING
heading(doc, "10.  Shooting", 1)
body(doc, "The **Shoot** action resolves in three quick steps.")
numbered(doc, "**Pick a target** in range and line of sight (see next section). "
              "You may target any visible enemy.")
numbered(doc, "**Roll to hit.** Roll a number of dice equal to the weapon's "
              "**Shots**. Each die that meets the shooter's **SK** is a hit.")
numbered(doc, "**Roll to save.** For each hit, the target rolls its **DEF**. Each "
              "save that succeeds cancels a hit. Every hit that is **not** saved "
              "deals the weapon's **Damage** to the target.")
callout(doc, "Shooting example",
        "A Grunt (SK 4+) fires an SMG (3 shots) at a Scout (DEF 5+) in the open. "
        "Grunt rolls 3 dice: 2, 4, 6 → two hits. Scout rolls 2 saves: 5, 3 → one "
        "saved, one fails. The Scout takes 1 Damage and, with W 1, is removed. "
        "**No modifiers, no sums — just two handfuls of dice.**")


# ============================================================ 11. LOS & COVER
heading(doc, "11.  Line of Sight & Cover", 1)
heading(doc, "Line of sight", 2)
body(doc, "If you can draw a straight line from your model to **any part** of the "
          "target without it being completely blocked by terrain or another model, "
          "you can see it and may shoot it. When in doubt, crouch down and look "
          "from behind the firing model.")
heading(doc, "Cover — the only shooting modifier", 2)
body(doc, "A target is **in cover** if it is inside terrain (woods, ruins) or if "
          "the shot crosses a piece of terrain within 1\" of the target (a wall it "
          "is hiding behind). A model in cover **adds +1 to each of its Defense "
          "saves** against shooting.")
bullet(doc, "Cover either applies or it doesn't — it never stacks. Two walls give "
            "the same +1 as one.")
bullet(doc, "Cover helps only against **shooting**, never in melee.")
bullet(doc, "The **Aim** action and **Sniper** weapons ignore cover entirely.")
callout(doc, "Cover example",
        "That same Scout (DEF 5+) is now behind a wall: it saves on **4+** instead "
        "of 5+. One visible cause, one clear effect, decided in a glance.")


# ============================================================ 12. FIGHTING
heading(doc, "12.  Fighting (Melee)", 1)
body(doc, "Use the **Fight** action when in base contact with an enemy. Fighting "
          "uses the same hit-and-save sequence as shooting.")
numbered(doc, "**Count attack dice.** Roll dice equal to your model's **A**. If you "
              "moved into base contact this activation, this is a **Charge**: add "
              "**+1 attack die**.")
numbered(doc, "**Roll to hit** against your **SK**, exactly as for shooting.")
numbered(doc, "**Target saves** on its **DEF**. Cover does not apply in melee. "
              "Unsaved hits deal the melee weapon's Damage.")
body(doc, "Only the **activating** model deals damage with its Fight action. If the "
          "defender survives, it can strike back when it is activated later. This is "
          "why charging first — and bringing tough models — matters.")
callout(doc, "Fighting example",
        "A Brute (A 3, SK 4+, Heavy Melee, Damage D3) charges a Veteran (DEF 4+, "
        "W 1). Charge gives 3 + 1 = 4 dice. Brute rolls 4, 4, 2, 5 → three hits. "
        "Veteran saves 4, 1, 3 → one save. Two hits get through; the first D3 of "
        "Damage already removes the W 1 Veteran.")


# ============================================================ 13. DAMAGE
heading(doc, "13.  Damage & Wounds", 1)
bullet(doc, "Each unsaved hit removes a number of **Wounds** equal to the weapon's "
            "**Damage** (1, or D3 for heavy weapons).")
bullet(doc, "When a model's Wounds reach **0 or less**, it is **removed** from play.")
bullet(doc, "Most models have **W 1** — for them, one unsaved hit is the end, and "
            "Damage values above 1 are simply overkill. Damage matters against "
            "**W 2+** models such as Leaders, Brutes and Heavies.")
bullet(doc, "Track wounds on multi-wound models with a die or a token beside them.")


# ============================================================ 14. NERVE
heading(doc, "14.  Nerve (Morale)", 1)
body(doc, "A warband holds steady until it starts taking real losses.")
bullet(doc, "A warband becomes **Broken** the moment it has lost **half or more** "
            "of the models it started with.")
bullet(doc, "While Broken, at the **start of each of your models' activations**, "
            "roll a D6. On a **1–2** that model is **Shaken** for this activation "
            "and may take only **Move** actions (retreat, hide — no shooting or "
            "fighting). On 3+ it acts normally.")
bullet(doc, "A model may instead spend an action to **Rally**, but since Shaken "
            "lasts only the one activation, most players simply ride it out or fall "
            "back to cover.")
body(doc, "That is the entire morale system: one die, only when you are losing, "
          "with one clear effect.", italic=True, size=9.5, space_after=4)


# ============================================================ 15. WINNING
heading(doc, "15.  Winning the Game", 1)
body(doc, "Pick a victory condition before you start:")
bullet(doc, "**Objectives (recommended):** Place **3 objective markers** — one at "
            "the centre and one near each side, all at least 9\" apart. You "
            "**control** an objective if you have more models within **3\"** of it "
            "than your opponent does. At the end of Round 4, score **1 point per "
            "objective controlled**. Most points wins.")
bullet(doc, "**Elimination:** If a warband is completely wiped out, the other side "
            "wins immediately.")
body(doc, "If objective points are tied at the end, the player who has lost fewer "
          "models wins. Still tied? Call it an honourable draw.")


# ============================================================ 16. SCENARIO
heading(doc, "16.  Scenario: Hold the Line", 1)
body(doc, "A complete starter game.")
bullet(doc, "**Warbands:** 100 points each.")
bullet(doc, "**Battlefield:** 3 × 3 ft, 6–10 terrain pieces, standard 6\" "
            "deployment zones.")
bullet(doc, "**Objectives:** Three markers in a line across the table centre, 9\" "
            "apart.")
bullet(doc, "**Length:** 4 rounds.")
bullet(doc, "**Scoring:** At the end of **Rounds 2, 3 and 4**, score 1 point per "
            "objective you control. Highest total after Round 4 wins.")
bullet(doc, "**Twist — Push On:** A model within 3\" of an objective it controls may "
            "treat its **Nerve** rolls as automatically passed.")


# ============================================================ 17. DESIGNER
heading(doc, "17.  Designer's Notes — Why So Few Modifiers", 1)
body(doc, "Most rule bloat comes from modifiers that look meaningful but cancel "
          "out. \"Hit on 4+, minus one for cover, plus one for aiming, minus one "
          "because they moved...\" — you do four sums and land back on 4+. You did "
          "arithmetic to change nothing. That is pure friction: it slows the game, "
          "invites mistakes, and adds zero decisions.")
body(doc, "SIXES keeps **only modifiers that change a decision you make**:")
bullet(doc, "**Cover (+1 save)** rewards you for moving behind terrain. It changes "
            "where you stand — so it stays.")
bullet(doc, "**Charge (+1 attack die)** rewards reaching the enemy first. It "
            "changes when and how you commit to melee — so it stays.")
bullet(doc, "**Aim (ignore cover, re-roll a miss)** is a choice between moving and "
            "shooting well. It changes how you spend your two actions — so it stays.")
body(doc, "Notice the pattern: bonuses are mostly **extra dice or re-rolls**, not "
          "tweaks to the target number. Counting an extra die is instant; "
          "re-rolling is intuitive; recalculating a target number mid-throw is "
          "where tables grind to a halt. And crucially, **none of these stack into "
          "a sum** — cover is +1 or nothing, a charge is one extra die or none.")
callout(doc, "The test every rule had to pass",
        "Does this modifier change a decision the player makes? If yes, it earns "
        "its place. If it only changes a number on the way to the same result, it "
        "was cut. That single test is why SIXES plays at the speed of "
        "conversation.")

doc.add_page_break()


# ============================================================ 18. QUICK REF
heading(doc, "18.  Quick Reference", 1)
body(doc, "Print this page and keep it between the players.", italic=True,
     size=9.5, space_after=6)

heading(doc, "The Round", 2)
body(doc, "**1.** Roll Initiative (D6, high picks who goes first).  "
          "**2.** Alternate activating one model each.  "
          "**3.** End of round: score, then repeat. Game = 4 rounds.", space_after=4)

heading(doc, "Activation = 2 actions", 2)
body(doc, "Move (up to M) · Shoot (once) · Fight (once) · Aim · Rally. "
          "Only Move may be taken twice.", space_after=4)

heading(doc, "Attack sequence (shoot & fight)", 2)
add_table(doc,
          ["Step", "Do this"],
          [
            ["1. Dice", "Shoot: roll Shots.  Fight: roll A (+1 die if you Charged)."],
            ["2. Hit",  "Each die ≥ SK = a hit. Natural 6 always hits, 1 always misses."],
            ["3. Save", "Target rolls DEF per hit; +1 to saves if in Cover (shooting only)."],
            ["4. Damage","Each unsaved hit removes Damage Wounds. 0 Wounds = removed."],
          ],
          widths=[Mm(26), Mm(144)], font_size=9.5)

heading(doc, "The complete modifier list", 2)
add_table(doc,
          ["Modifier", "Effect", "When"],
          [
            ["Cover",     "+1 to Defense saves", "Target in/behind terrain (shooting only)"],
            ["Charge",    "+1 attack die",       "Moved into base contact this activation"],
            ["Aim",       "Ignore cover, re-roll 1 miss", "Spent the Aim action"],
            ["Sniper",    "Ignores cover",       "Weapon special rule"],
            ["Piercing",  "No Defense save",     "Weapon special rule"],
            ["Heavy",     "Must Aim to fire",    "Weapon special rule"],
          ],
          widths=[Mm(26), Mm(56), Mm(88)], font_size=9.5)

heading(doc, "D3 from a D6", 2)
add_table(doc,
          ["D6", "1–2", "3–4", "5–6"],
          [["D3", "1", "2", "3"]],
          widths=[Mm(34), Mm(30), Mm(30), Mm(30)], font_size=9.5)

heading(doc, "Nerve", 2)
body(doc, "Broken at half losses. While Broken, each model rolls D6 at the start of "
          "its activation: **1–2 = Shaken** (Move only this activation), 3+ normal.",
     space_after=4)

doc.save("sixes_rulebook.docx")
print("Wrote sixes_rulebook.docx")
