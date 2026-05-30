# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib"]
# ///
"""
Top-down deployment maps for The Litany Sea scenarios -> assets/map_<i>.png
Specs authored directly from each scenario's setup/deployment/objectives.
Board is square in inches, origin bottom-left.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, RegularPolygon, FancyBboxPatch
from matplotlib.lines import Line2D

os.makedirs("assets", exist_ok=True)

C = {
    "brine_f": "#BFE0E0", "brine": "#3E8E92", "brine_deep": "#A6D2D4",
    "dry": "#ECDFC4", "sand_bg": "#F5EEDD", "dry_edge": "#C9B589",
    "gold": "#C9A227", "litany": "#E8B923", "reliq": "#7FD0D6",
    "terr": "#9A9486", "ink": "#20323B", "arrow": "#7A1414",
}
DEP = {"A": "#7A1414", "B": "#2E4552", "C": "#8A6D1F", "D": "#1F6E54"}


def draw_crystal(ax, x, y, kind, label=None, scale=1.0):
    if kind == "litany":
        ax.add_patch(RegularPolygon((x, y), numVertices=4, radius=1.7 * scale, orientation=0.785,
                                    facecolor=C["litany"], edgecolor=C["arrow"], linewidth=2.0, zorder=6))
        ax.plot(x, y, marker="*", markersize=8 * scale, color="#FFF6D5", zorder=7)
    elif kind == "reliq":
        ax.add_patch(RegularPolygon((x, y), numVertices=6, radius=2.1 * scale, orientation=0,
                                    facecolor=C["reliq"], edgecolor=C["ink"], linewidth=2.2, zorder=6))
        ax.plot(x, y, marker="*", markersize=10 * scale, color="#FFFFFF", zorder=7)
    else:
        ax.add_patch(RegularPolygon((x, y), numVertices=4, radius=1.15 * scale, orientation=0.785,
                                    facecolor=C["gold"], edgecolor=C["ink"], linewidth=1.1, zorder=6))
    if label:
        ax.text(x, y - 2.5 * scale, label, ha="center", va="top", fontsize=7, color=C["ink"],
                fontweight="bold", zorder=8)


def render(spec, idx):
    B = spec["board"]
    fig, ax = plt.subplots(figsize=(6.7, 7.1))
    ax.set_xlim(-1.5, B + 1.5)
    ax.set_ylim(-2.5, B + 4.5)
    ax.set_aspect("equal")
    ax.axis("off")

    base = C["brine_f"] if spec.get("base") == "brine" else C["sand_bg"]
    ax.add_patch(Rectangle((0, 0), B, B, facecolor=base, edgecolor="none", zorder=0))

    # horizontal bands (full width)
    for bd in spec.get("bands", []):
        fill = C["brine_f"] if bd["fill"] == "brine" else C["dry"]
        edge = C["brine"] if bd["fill"] == "brine" else C["dry_edge"]
        ax.add_patch(Rectangle((0, bd["y"]), B, bd["h"], facecolor=fill, edgecolor=edge,
                               linewidth=1.0, alpha=0.85, zorder=1))
        if bd.get("label"):
            ax.text(0.6, bd["y"] + bd["h"] / 2, bd["label"], ha="left", va="center", fontsize=6.6,
                    color="#5B6B6B", style="italic", zorder=2)

    # arbitrary regions (nave, choir-pit, pools)
    for rg in spec.get("regions", []):
        fill = {"brine": C["brine_f"], "dry": C["dry"], "deep": C["brine_deep"]}.get(rg["fill"], C["dry"])
        edge = rg.get("edge", C["brine"] if rg["fill"] in ("brine", "deep") else C["dry_edge"])
        ax.add_patch(Rectangle((rg["x"], rg["y"]), rg["w"], rg["h"], facecolor=fill, edgecolor=edge,
                               linewidth=rg.get("lw", 1.4), alpha=0.9,
                               linestyle=rg.get("ls", "-"), zorder=1.5))
        if rg.get("label"):
            ax.text(rg["x"] + rg["w"] / 2, rg["y"] + rg["h"] - 1.2, rg["label"], ha="center", va="top",
                    fontsize=6.8, color="#3D6E70", style="italic", zorder=2)

    # zone grid
    g = spec.get("grid")
    if g:
        for i in range(1, g["nx"]):
            ax.plot([B * i / g["nx"]] * 2, [0, B], color="#000", alpha=0.10, lw=0.7, zorder=2)
        for j in range(1, g["ny"]):
            ax.plot([0, B], [B * j / g["ny"]] * 2, color="#000", alpha=0.10, lw=0.7, zorder=2)

    # deploy zones (explicit rects with faction labels)
    for d in spec.get("deploy", []):
        col = DEP.get(d.get("color", "A"), DEP["A"])
        hatch = {"A": "//", "B": "\\\\", "C": "xx", "D": "++"}.get(d.get("color", "A"), "//")
        ax.add_patch(Rectangle((d["x"], d["y"]), d["w"], d["h"], facecolor=col, alpha=0.15,
                               edgecolor=col, linewidth=1.6, hatch=hatch, zorder=3))
        ax.text(d["x"] + d["w"] / 2, d["y"] + d["h"] / 2, d.get("label", ""), ha="center", va="center",
                fontsize=7.6, color=col, fontweight="bold", zorder=4, rotation=d.get("rot", 0))

    # terrain
    for t in spec.get("terrain", []):
        ax.add_patch(FancyBboxPatch((t["x"], t["y"]), t["w"], t["h"],
                                    boxstyle="round,pad=0.1,rounding_size=0.7", facecolor=C["terr"],
                                    edgecolor="#6E695E", alpha=0.5, linewidth=1.0, zorder=4))
        ax.text(t["x"] + t["w"] / 2, t["y"] + t["h"] / 2, t.get("label", ""), ha="center", va="center",
                fontsize=5.6, color="#3A372F", style="italic", zorder=5)

    # arrows
    for a in spec.get("arrows", []):
        ax.annotate("", xy=(a["x2"], a["y2"]), xytext=(a["x1"], a["y1"]),
                    arrowprops=dict(arrowstyle="-|>", color=C["arrow"], lw=2.0, shrinkA=4, shrinkB=4), zorder=7)
        if a.get("label"):
            ax.text((a["x1"] + a["x2"]) / 2, (a["y1"] + a["y2"]) / 2 + 1.0, a["label"], ha="center",
                    fontsize=6.8, color=C["arrow"], fontweight="bold", zorder=8,
                    rotation=a.get("rot", 0))

    # crystals
    for cr in spec.get("crystals", []):
        draw_crystal(ax, cr["x"], cr["y"], cr["kind"], cr.get("label"), cr.get("scale", 1.0))

    # notes
    for n in spec.get("notes", []):
        ax.text(n["x"], n["y"], n["text"], ha="center", va="center", fontsize=6.8, color=C["ink"],
                style="italic", zorder=9,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#CFC7B4", alpha=0.9))

    ax.add_patch(Rectangle((0, 0), B, B, facecolor="none", edgecolor=C["ink"], linewidth=2.6, zorder=9))

    # scale bar 6"
    ax.plot([0, 6], [-1.4, -1.4], color=C["ink"], lw=2.2)
    ax.text(3, -2.4, '6"', ha="center", va="top", fontsize=7, color=C["ink"])
    ax.text(B, -2.4, '%d" board' % B, ha="right", va="top", fontsize=7, color="#888", style="italic")

    ax.text(B / 2, B + 3.4, spec["name"], ha="center", fontsize=13.5, fontweight="bold", color=C["arrow"])
    ax.text(B / 2, B + 1.4, spec["blurb"], ha="center", fontsize=7.4, color=C["ink"], style="italic")

    handles = [
        Line2D([0], [0], marker="*", color="w", markerfacecolor=C["litany"], markeredgecolor=C["arrow"], markersize=13, label="Litany (key crystal)"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor=C["gold"], markeredgecolor=C["ink"], markersize=9, label="Salt-glass crystal"),
        Line2D([0], [0], marker="h", color="w", markerfacecolor=C["reliq"], markeredgecolor=C["ink"], markersize=12, label="Reliquary (the Prize)"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=C["brine_f"], markeredgecolor=C["brine"], markersize=11, label="Brine-deep (wet)"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=C["dry"], markeredgecolor=C["dry_edge"], markersize=11, label="Dry (exposed)"),
    ]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.035), ncol=3, fontsize=7,
              frameon=False, handletextpad=0.4, columnspacing=1.1)
    fig.tight_layout()
    out = "assets/map_%d.png" % idx
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def bands6(y0, h, fills, labels):
    return [{"y": y0 + i * h, "h": h, "fill": fills[i], "label": labels[i]} for i in range(len(fills))]


MAPS = [
    {  # 0 — Reckoning of the Sixth Toll: 6 tidal bands, all wet; 3 factions on shore
        "board": 36, "base": "dry",
        "name": "The Reckoning of the Sixth Toll",
        "blurb": "Six tidal bands, all drowned. Three orders wade off the shore as the Sea recedes in a secret order.",
        "bands": bands6(6, 5,
                        ["brine"] * 6,
                        ["Band 1 (shore)", "Band 2", "Band 3", "Band 4", "Band 5", "Band 6 (deep)"]),
        "deploy": [{"x": 0, "y": 0, "w": 36, "h": 6, "color": "A",
                    "label": "SHORE DEPLOY — Mnemarchs · Iconoclasts · Brine-Factors  (≤6\")"}],
        "crystals": [
            {"x": 18, "y": 8.5, "kind": "salt", "label": "minor"},
            {"x": 18, "y": 13.5, "kind": "salt", "label": "minor"},
            {"x": 18, "y": 18.5, "kind": "litany", "label": "major"},
            {"x": 18, "y": 23.5, "kind": "litany", "label": "major"},
            {"x": 18, "y": 28.5, "kind": "litany", "label": "Choir-Cantor ×2", "scale": 1.15},
            {"x": 18, "y": 33.5, "kind": "litany", "label": "Choir-Cantor ×2", "scale": 1.15}],
        "terrain": [{"x": 7, "y": 16, "w": 4, "h": 4, "label": "ruin"}, {"x": 26, "y": 25, "w": 4, "h": 4, "label": "ruin"}],
        "arrows": [{"x1": 33, "y1": 8, "x2": 33, "y2": 34, "label": "tide recedes (secret order)", "rot": 90}],
        "notes": [{"x": 9, "y": 31, "text": "Sediment: no deploy —\nre-dreams from drying bands"}],
    },
    {  # 1 — Reliquary Run: 4x4 grid all wet, central Choir-Pit, Nine Mouths center, 4 edges
        "board": 36, "base": "brine",
        "name": "The Reliquary Run",
        "blurb": "Sixteen drowned zones. Nine Mouths waits in the Choir-Pit, which dries last of all.",
        "grid": {"nx": 4, "ny": 4},
        "regions": [{"x": 9, "y": 9, "w": 18, "h": 18, "fill": "deep", "label": "Choir-Pit (dries last)",
                     "edge": "#2E4552", "lw": 2.0, "ls": "--"}],
        "deploy": [
            {"x": 0, "y": 0, "w": 36, "h": 4.5, "color": "A", "label": "Mnemarchs"},
            {"x": 0, "y": 31.5, "w": 36, "h": 4.5, "color": "B", "label": "Ash Iconoclasts"},
            {"x": 0, "y": 4.5, "w": 4.5, "h": 27, "color": "C", "label": "Brine-Factors", "rot": 90},
            {"x": 31.5, "y": 4.5, "w": 4.5, "h": 27, "color": "D", "label": "Sediment", "rot": 90}],
        "crystals": [
            {"x": 18, "y": 18, "kind": "reliq", "label": "Nine Mouths ×3", "scale": 1.2},
            {"x": 4.5, "y": 13.5, "kind": "salt"}, {"x": 31.5, "y": 22.5, "kind": "salt"},
            {"x": 13.5, "y": 4.5, "kind": "salt"}, {"x": 22.5, "y": 31.5, "kind": "salt"},
            {"x": 31.5, "y": 4.5, "kind": "salt"}],
        "arrows": [{"x1": 3, "y1": 3, "x2": 8, "y2": 8, "label": "corners dry first"},
                   {"x1": 33, "y1": 33, "x2": 28, "y2": 28, "label": ""}],
    },
    {  # 2 — Sealing of the Last Shoal: asymmetric, band1 dry shore, rest wet
        "board": 36, "base": "dry",
        "name": "The Sealing of the Last Shoal",
        "blurb": "Attacker wades off the shore to Silence; defender seals the seaward heart of the reef.",
        "bands": bands6(0, 6,
                        ["dry", "brine", "brine", "brine", "brine", "brine"],
                        ["Band 1 (dry shore)", "Band 2", "Band 3", "Band 4", "Band 5", "Band 6 (deep)"]),
        "deploy": [
            {"x": 0, "y": 0, "w": 36, "h": 6, "color": "B", "label": "ATTACKER — Ash Iconoclasts (shore)"},
            {"x": 0, "y": 18, "w": 36, "h": 18, "color": "A", "label": "DEFENDER — Mnemarchs (bands 4–6)"}],
        "crystals": [
            {"x": 18, "y": 3, "kind": "salt"}, {"x": 11, "y": 9, "kind": "salt"}, {"x": 25, "y": 9, "kind": "salt"},
            {"x": 13, "y": 15, "kind": "litany"}, {"x": 23, "y": 16, "kind": "litany"}, {"x": 18, "y": 21, "kind": "litany"},
            {"x": 18, "y": 33, "kind": "salt"}],
        "terrain": [{"x": 5, "y": 25, "w": 4, "h": 3, "label": "outcrop"}, {"x": 28, "y": 27, "w": 4, "h": 3, "label": "outcrop"}],
        "arrows": [{"x1": 32.5, "y1": 7, "x2": 32.5, "y2": 31, "label": "shallows recede seaward", "rot": 90}],
    },
    {  # 3 — Last Liquidation: 6 bands, bands1-2 dry, Vault-Heart band4
        "board": 36, "base": "dry",
        "name": "The Last Liquidation",
        "blurb": "Grab the Vault-Heart from the deep, run it to your own edge, and sell before the brine quits.",
        "bands": bands6(0, 6,
                        ["dry", "dry", "brine", "brine", "brine", "brine"],
                        ["Band 1 (dry)", "Band 2 (dry)", "Band 3", "Band 4", "Band 5", "Band 6 (deep)"]),
        "deploy": [
            {"x": 0, "y": 0, "w": 36, "h": 6, "color": "A", "label": "EXTRACTION EDGE A  ≤6\""},
            {"x": 0, "y": 30, "w": 36, "h": 6, "color": "B", "label": "EXTRACTION EDGE B  ≤6\""}],
        "crystals": [
            {"x": 18, "y": 21, "kind": "reliq", "label": "Vault-Heart", "scale": 1.15},
            {"x": 11, "y": 15, "kind": "salt"}, {"x": 25, "y": 27, "kind": "salt"}],
        "terrain": [{"x": 7, "y": 24, "w": 4, "h": 3, "label": "ruin"}, {"x": 27, "y": 14, "w": 4, "h": 3, "label": "ruin"}],
        "arrows": [{"x1": 4, "y1": 9, "x2": 4, "y2": 33, "label": "tide recedes; Band 4 flips R3", "rot": 90}],
        "notes": [{"x": 26, "y": 21, "text": "Band 4 = the hinge"}],
    },
    {  # 4 — Undertow Verdict: 6x6 cathedral, nave wet, aisle dry, diagonal deploy
        "board": 36, "base": "dry",
        "name": "The Undertow Verdict",
        "blurb": "The drowned cathedral. The nave dries outside-in, then reverses — safe and risky holdings trade places.",
        "grid": {"nx": 6, "ny": 6},
        "regions": [{"x": 12, "y": 6, "w": 18, "h": 24, "fill": "brine", "label": "The Nave (recedes outside-in, then reverses)"}],
        "deploy": [
            {"x": 0, "y": 0, "w": 10, "h": 10, "color": "B", "label": "Ash\nIconoclasts"},
            {"x": 26, "y": 26, "w": 10, "h": 10, "color": "D", "label": "Sediment"},
            {"x": 0, "y": 12, "w": 6, "h": 18, "color": "A", "label": "Mnemarchs", "rot": 90},
            {"x": 30, "y": 6, "w": 6, "h": 18, "color": "C", "label": "Brine-Factors", "rot": 90}],
        "crystals": [
            {"x": 15, "y": 9, "kind": "litany"}, {"x": 21, "y": 15, "kind": "litany"},
            {"x": 15, "y": 21, "kind": "litany"}, {"x": 21, "y": 27, "kind": "litany"}, {"x": 18, "y": 18, "kind": "reliq", "label": "deep nave"},
            {"x": 3, "y": 21, "kind": "salt"}, {"x": 33, "y": 15, "kind": "salt"}, {"x": 9, "y": 33, "kind": "salt"}],
        "arrows": [{"x1": 18, "y1": 18, "x2": 18, "y2": 27, "label": "R5: dries centre-out"},
                   {"x1": 18, "y1": 18, "x2": 24, "y2": 18, "label": ""}],
    },
]

if __name__ == "__main__":
    for i, m in enumerate(MAPS):
        print("wrote", render(m, i))
