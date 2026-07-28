import yaml
with open("app/country_packs/NL/sources.yaml") as f:
    data = yaml.safe_load(f)
for s in data["sources"]:
    dr = s.get("disabled_reason", "") or ""
    print(f"{s['id']:30s} enabled={s.get('enabled',True)} reason={'YES' if dr else 'NO'} {dr[:50] if dr else ''}")
