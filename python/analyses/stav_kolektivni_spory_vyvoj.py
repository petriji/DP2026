r"""
Casovy vyvoj poctu kolektivnich sporu v CR (2013--2025).

Data source
-----------
* CMKOS: Zprava o prubehu kolektivniho vyjednavani na vyssim stupni
  a na podnikove urovni v roce 2025 (sekce 7: kolektivni spory).

Output
------
  python/figures/stav_kolektivni_spory_vyvoj.pgf
  latex/texparts/python/stav_kolektivni_spory_vyvoj.tex

Run
---
    python analyses/stav_kolektivni_spory_vyvoj.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import COUNTRY_COLORS, FIGURE_COMPACT_LABEL_SIZE
from stattool.style import apply_style_pgf, cm2in, save_figure_tex_pgf, savefig_pgf

# ── Parameters ────────────────────────────────────────────────────────────────
YEARS = list(range(2013, 2026))

# Kolektivni spory resene zprostredkovatelem (KSVS + PKS)
KSVS_MEDIATION = [1, 0, 0, 4, 1, 3, 2, 1, 1, 0, 0, 0, 0]
PKS_MEDIATION = [8, 15, 6, 17, 13, 28, 17, 18, 19, 15, 9, 6, 10]

# Eskalacni ukazatele (stavkove pohotovosti, stavky)
KSVS_ALERTS = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
PKS_ALERTS = [2, 8, 4, 5, 10, 10, 8, 2, 5, 6, 4, 3, 3]
PKS_STRIKES = [0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0]

apply_style_pgf()

# ── 1. Build frame ───────────────────────────────────────────────────────────
df = pd.DataFrame(
    {
        "time": YEARS,
        "ksvs_mediation": KSVS_MEDIATION,
        "pks_mediation": PKS_MEDIATION,
        "ksvs_alerts": KSVS_ALERTS,
        "pks_alerts": PKS_ALERTS,
        "pks_strikes": PKS_STRIKES,
    }
)
df["collective_disputes_total"] = df["ksvs_mediation"] + df["pks_mediation"]
df["alerts_total"] = df["ksvs_alerts"] + df["pks_alerts"]

print(df[["time", "collective_disputes_total", "alerts_total", "pks_strikes"]].to_string(index=False))

# ── 2. Plot ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=cm2in(15, 9))

x = np.arange(len(df))
ax.bar(
    x,
    df["collective_disputes_total"],
    color=COUNTRY_COLORS.get("CZ", "#D62728"),
    alpha=0.35,
    label="kolektivní spory",
)

ax.plot(
    x,
    df["alerts_total"],
    color="#1f3b73",
    marker="o",
    linewidth=1.8,
    label="stávkové pohotovosti",
)
ax.plot(
    x,
    df["pks_strikes"],
    color="#2b8c2b",
    marker="s",
    linewidth=1.6,
    label="stávky",
)

ax.set_xticks(x)
ax.set_xticklabels(df["time"].astype(str), rotation=0)
ax.set_xlim(-0.6, len(df) - 0.4)
ax.set_ylim(0, max(df["collective_disputes_total"]) + 5)

STRINGS = {
    "title": r"Kolektivní spory, stávkové pohotovosti a stávky, \acs{geo-CZ}",
    "ylabel": "počet případů",
}
ax.set_title(STRINGS["title"])
ax.set_ylabel(STRINGS["ylabel"])
ax.set_xlabel("rok")
ax.legend(frameon=False, fontsize=FIGURE_COMPACT_LABEL_SIZE, loc="upper right")

savefig_pgf(fig, "stav_kolektivni_spory_vyvoj", strings=STRINGS)

save_figure_tex_pgf(
    "stav_kolektivni_spory_vyvoj",
    caption=(
        r"Casovy vyvoj poctu kolektivnich sporu resenych prostrednictvim "
        r"zprostredkovatele, stavkovych pohotovosti a stavek, \\acs{geo-CZ}, 2013--2025"
    ),
    label="fig:stav_kolektivni_spory_vyvoj",
    resizebox_width=r"\linewidth",
    cite_key="CMKOS_ZpravaKV2025",
    strings=STRINGS,
)

print("Done.")