import json
o = json.load(open("sixes_content.json", encoding="utf-8"))
def t(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"
dist = {d.get("faction",""): d for d in o.get("council",{}).get("distinctiveness",[])}
brief = {"world": {
    "name": o["setting"]["worldName"],
    "tagline": o["setting"].get("tagline",""),
    "premise": t(o["setting"].get("premise",""), 700),
    "twist": t(o["setting"].get("theTwist",""), 500),
    "mechanics": [{"name": m.get("name"), "concept": t(m.get("concept",""),300)} for m in o["setting"].get("worldMechanics",[])],
    "terms": [{"term": x.get("term"), "meaning": t(x.get("meaning",""),160)} for x in o["setting"].get("terminology",[])],
}, "factions": [], "scenarios": []}
for i, f in enumerate(o["factions"]):
    d = dist.get(f["name"], {})
    lore = f.get("lore", {})
    brief["factions"].append({
        "index": i, "name": f["name"], "identity": d.get("playstyle") or "",
        "playstyle": t(d.get("signatureMechanic",""), 280),
        "colorMotif": next((x.get("colorMotif","") for x in o["setting"].get("factions",[]) if x.get("name")==f["name"]), ""),
        "signatureRule": {"name": f.get("signatureRule",{}).get("name",""), "text": t(f.get("signatureRule",{}).get("text",""), 280)},
        "lore": {k: t(lore.get(k,""), 480) for k in ("origin","culture","whyTheyFight","leadership","homeland")},
        "units": [{"name": u.get("name"), "role": u.get("role"), "flavor": t(u.get("flavor",""),220),
                   "stat": "M%s SK%s DEF%s W%s A%s" % (u.get("M"),u.get("SK"),u.get("DEF"),u.get("W"),u.get("A"))}
                  for u in f.get("units",[])],
        "characters": [{"name": c.get("name"), "title": c.get("title"), "flavor": t(c.get("flavor",""),260),
                        "rule": c.get("uniqueRule",{}).get("name","")} for c in f.get("characters",[])],
    })
for i, s in enumerate(o.get("scenarios",[])):
    brief["scenarios"].append({"index": i, "name": s.get("name"), "hook": t(s.get("hook",""),260),
        "setup": t(s.get("setup",""),700), "deployment": t(s.get("deployment",""),700),
        "objectives": t(s.get("objectives",""),700), "twist": t(s.get("twist",""),300)})
json.dump(brief, open("art_brief.json","w",encoding="utf-8"), ensure_ascii=False)
print("brief bytes:", len(open("art_brief.json","rb").read()))
print("factions:", len(brief["factions"]), "scenarios:", len(brief["scenarios"]))

# split into small per-agent files
import os
os.makedirs("brief", exist_ok=True)
json.dump(brief["world"], open("brief/world.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
for fobj in brief["factions"]:
    json.dump(fobj, open("brief/faction_%d.json" % fobj["index"],"w",encoding="utf-8"), ensure_ascii=False, indent=1)
for sobj in brief["scenarios"]:
    json.dump(sobj, open("brief/scenario_%d.json" % sobj["index"],"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("split files written:", len(os.listdir("brief")))
