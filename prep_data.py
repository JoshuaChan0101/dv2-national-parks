"""Builds data/park_species.csv and data/observations.csv from the ALA downloads.

Put this file in your project folder (next to data/ and ala_records/):
    parks_wildlife/
        prep_data.py
        ala_records/   <- one CSV per park, named exactly like the park in parks.csv
        data/          <- output goes here (parks.csv should already be in it)

Run:  python prep_data.py      (needs pandas: pip install pandas)

Only records identified to SPECIES level are kept. ALA also holds records identified
only to genus, family or order (e.g. "ACANTHIZIDAE"); counting those as species would
inflate "species recorded". Subspecies are merged into their species.
"""
import re
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
SRC = HERE / "ala_records"
OUT = HERE / "data"
OUT.mkdir(exist_ok=True)

WANT = {"scientificName", "vernacularName", "class", "year", "month", "countryConservation"}
CLASS = {"aves": "Birds", "mammalia": "Mammals", "reptilia": "Reptiles", "amphibia": "Frogs"}
SEVERITY = {"Not listed": 0, "Vulnerable": 1, "Endangered": 2, "Critically Endangered": 3}
BY_SEVERITY = {v: k for k, v in SEVERITY.items()}
BINOMIAL = re.compile(r"^[A-Z][a-z]+ [a-z][a-z-]+(\s|$)")
NOT_A_SPECIES = {"sp", "spp", "cf", "aff"}
# Animals offered in the chart 03 dropdown (edit to match specs/03_species_finder_map.json)
COMMON_OVERRIDE = {"Pseudomys fumeus": "Smoky Mouse", "Dasyurus hallucatus": "Northern Quoll"}
# ALA gives every Tiger Snake record "Vulnerable" because the listed Krefft's Tiger Snake (Flinders Ranges)
# is treated as a synonym. Checked on SPRAT: only that local form is listed, and none of the 12 parks
# has records of it, so the species is treated as not threatened here.
STATUS_OVERRIDE = {"Notechis scutatus": "Not listed"}
DROPDOWN = ["Koala", "Bare-nosed Wombat", "Tasmanian Devil", "Platypus", "Red Kangaroo",
            "Southern Cassowary", "Superb Lyrebird", "Short-beaked Echidna", "Dingo"]


def status(s):
    s = str(s).lower()
    if "critically" in s: return "Critically Endangered"
    if "endangered" in s: return "Endangered"
    if "vulnerable" in s: return "Vulnerable"
    return "Not listed"


# 1. Read every park file
frames = []
for f in sorted(SRC.glob("*.csv")):
    d = pd.read_csv(f, low_memory=False, usecols=lambda c: c in WANT)
    missing = WANT - set(d.columns)
    if missing:
        raise SystemExit(f"{f.name} is missing columns {missing}. Columns found: {list(d.columns)}")
    d["park"] = f.stem
    print(f"{f.name}: {len(d):,} rows")
    frames.append(d)
if not frames:
    raise SystemExit(f"No CSV files found in {SRC}")
df = pd.concat(frames, ignore_index=True)

# 2. Keep animals of the four groups, identified to species level
df["class"] = df["class"].astype(str).str.lower().map(CLASS)
df = df.dropna(subset=["class", "scientificName"])
name = df["scientificName"].astype(str).str.replace(r"\s*\([^)]*\)", "", regex=True).str.strip()  # drop "(Subgenus)"
is_species = name.str.match(BINOMIAL) & ~name.str.split().str[1].isin(NOT_A_SPECIES)
print(f"\nDropped {(~is_species).sum():,} of {len(df):,} records not identified to species level")
df = df[is_species].copy()
name = name[is_species]
df["species"] = name.str.split().str[:2].str.join(" ")      # merge subspecies into species
df["exact"] = name.str.split().str.len() == 2

# 3. Status, year, month
df["status"] = df["countryConservation"].map(status)
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["month"] = pd.to_numeric(df["month"], errors="coerce")

# 4. One common name per species (used in every park), and a status per species per park
v = df.dropna(subset=["vernacularName"])
mode = lambda s: s.mode().iat[0]
common = (v[v["exact"]].groupby("species")["vernacularName"].agg(mode)
          .combine_first(v.groupby("species")["vernacularName"].agg(mode)))
# A species counts as threatened only if the species itself is listed. If just one subspecies
# is listed (e.g. a rare island form of a common bird), the species is not marked threatened.
sev = df.assign(sev=df["status"].map(SEVERITY))
# Status is worked out park by park, so an animal is only marked threatened in the parks
# where its own records carry a listing (e.g. a listed local form of a widespread snake).
worst = (sev[sev["exact"]].groupby(["park", "species"])["sev"].max()
         .combine_first(sev.groupby(["park", "species"])["sev"].max()))

# 5. park_species.csv: one row per species per park
ps = df.groupby(["park", "species", "class"]).size().rename("records").reset_index()
ps["common"] = ps["species"].map(common).fillna(ps["species"])
ps["common"] = ps["species"].map(COMMON_OVERRIDE).fillna(ps["common"])   # plain-English names
ps["status"] = [BY_SEVERITY[int(worst[(p, sp)])] for p, sp in zip(ps["park"], ps["species"])]
ps["status"] = ps["species"].map(STATUS_OVERRIDE).fillna(ps["status"])
ps = ps[["park", "species", "common", "class", "status", "records"]]
ps.to_csv(OUT / "park_species.csv", index=False)

# 6. observations.csv: sightings per park, group, year and month
ob = (df.dropna(subset=["year", "month"]).astype({"year": int, "month": int})
        .groupby(["park", "class", "year", "month"]).size().rename("records").reset_index())
ob.to_csv(OUT / "observations.csv", index=False)

# 7. Checks
print("\nPer park (species recorded, threatened species, sightings):")
summary = ps.assign(thr=ps["status"].ne("Not listed")).groupby("park").agg(
    species=("species", "size"), threatened=("thr", "sum"), sightings=("records", "sum"))
print(summary.to_string())

parks_file = OUT / "parks.csv"
if parks_file.exists():
    names = set(pd.read_csv(parks_file)["park"])
    print("\nIn parks.csv but no records file:", sorted(names - set(ps["park"])) or "none")
    print("Records file but not in parks.csv:", sorted(set(ps["park"]) - names) or "none")
if (ps["status"] == "Not listed").all():
    print("\nWARNING: no threatened species found. Check the countryConservation values.")

print("\nDropdown animals (parks where each was recorded):")
for a in DROPDOWN:
    n = ps.loc[ps["common"] == a, "park"].nunique()
    print(f"  {a}: {n} parks" + ("   <-- NOT FOUND, change the name" if n == 0 else ""))

# Full list of threatened animals, to scan for doubtful ones against SPRAT (not part of the website)
check = (ps[ps["status"] != "Not listed"].groupby(["common", "species", "status"])
           .agg(parks=("park", "nunique"), records=("records", "sum")).reset_index()
           .sort_values("records", ascending=False))
check.to_csv(HERE / "threatened_check.csv", index=False)
print(f"\n{len(check)} threatened animals listed in threatened_check.csv (outside data/)")

print("\nCommon names that look unfamiliar (check these in the threatened chart):")
thr = ps[ps["status"] != "Not listed"].groupby(["common", "species"])["records"].sum()
print(thr.sort_values(ascending=False).head(12).to_string())