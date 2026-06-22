"""Render a diverging bar chart of the week's largest OMB re-apportionments.

Pulls the FY2026 SF-132 apportionment index from BlazingStar's CC0 mirror,
finds accounts (TAFS) whose latest apportionment iteration changed in the 7 days
ending at the most recent approval in the file, and charts the biggest dollar
moves. Writes weekly_reapportionments.png.

Methodology matches demo.ipynb: data_json rows only (they carry the amount),
BUREAU-* rollups excluded, current vs. prior iteration per agency+TAFS.
"""
import re

import matplotlib.pyplot as plt
import pandas as pd
import requests

SF132_FY = 2026
TOP_N = 12
INCREASE = "#2A9D8F"   # teal
DECREASE = "#E76F51"   # muted orange-red
ACCENT = "#69539E"     # BlazingStar purple

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "blazingstar-data-demo (https://github.com/abigailhaddad/blazingstar-data)"})

# Loan/credit financing accounts swing on credit-program mechanics, not outlays;
# flag them so the chart doesn't read those moves as ordinary spending changes.
FINANCING = re.compile(r"financing|guaranteed|direct loan|credit", re.I)


def load_changes():
    idx = SESSION.get(f"https://cdn.bzstr.co/sf132/fy{SF132_FY}/index.json", timeout=90).json()
    df = pd.DataFrame(idx["files"])
    df = df[(df["file_type"] == "data_json")
            & (~df["tafs"].str.startswith("BUREAU", na=False))].copy()
    df["amount"] = pd.to_numeric(df["total_approved_amount"], errors="coerce")
    df["iteration"] = pd.to_numeric(df["iteration"], errors="coerce")
    df["approved"] = pd.to_datetime(df["approval_timestamp"], utc=True, errors="coerce")
    df = df.sort_values(["agency", "tafs", "iteration"])
    df["prev"] = df.groupby(["agency", "tafs"])["amount"].shift(1)
    cur = df.groupby(["agency", "tafs"]).tail(1).copy()
    cur["delta"] = cur["amount"] - cur["prev"]

    anchor = df["approved"].max()
    start = anchor - pd.Timedelta(days=7)
    changed = cur[(cur["approved"] >= start) & cur["delta"].notna() & (cur["delta"] != 0)].copy()
    return changed, start, anchor, idx["generated_at"]


def short(name):
    name = str(name).split(",")[0]              # drop trailing ", Energy" etc.
    name = re.sub(r"\s+(Financing )?Account$", "", name)
    return name if len(name) <= 32 else name[:31] + "…"


def main():
    changed, start, anchor, generated = load_changes()
    top = changed.reindex(changed["delta"].abs().sort_values().index).tail(TOP_N)

    labels = [f"{r.agency}  {short(r.account_name)}" + ("  ★" if FINANCING.search(str(r.account_name)) else "")
              for r in top.itertuples()]
    deltas = (top["delta"] / 1e9).tolist()
    colors = [INCREASE if d >= 0 else DECREASE for d in deltas]

    n = len(changed)
    net = changed["delta"].sum() / 1e9
    gross = changed["delta"].abs().sum() / 1e9

    fig, ax = plt.subplots(figsize=(11, 7.4))
    fig.subplots_adjust(top=0.76, bottom=0.11, left=0.34, right=0.96)

    bars = ax.barh(range(len(top)), deltas, color=colors, height=0.72)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(labels, fontsize=10)

    for bar, d in zip(bars, deltas):
        ax.text(d + (0.35 if d >= 0 else -0.35), bar.get_y() + bar.get_height() / 2,
                f"{'+' if d >= 0 else '−'}${abs(d):.1f}B", va="center",
                ha="left" if d >= 0 else "right", fontsize=10, fontweight="bold",
                color="#222")

    # Title, subtitle, and footer placed in figure coordinates to avoid overlap.
    fig.text(0.015, 0.955, f"OMB re-apportioned ${gross:.0f}B across {n} accounts in one week",
             fontsize=18, fontweight="bold", color=ACCENT, ha="left", va="top")
    fig.text(0.015, 0.885,
             f"Largest week-over-week changes to apportioned budget authority, week ending "
             f"{anchor.date()} (net +${net:.0f}B).\nA re-apportionment updates the legal spending limit "
             f"on an account — not necessarily new money.\n★ = loan/credit financing account (swings on "
             f"credit-program mechanics, not outlays).",
             fontsize=9.5, color="#555", ha="left", va="top", linespacing=1.5)

    ax.axvline(0, color="#333", lw=1)
    ax.set_xlabel("change in apportioned amount, $ billions", fontsize=10, color="#555")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(left=False)
    ax.grid(axis="x", color="#e7e7e7", lw=0.8)
    ax.set_axisbelow(True)
    pad = max(abs(min(deltas)), abs(max(deltas))) * 0.18
    ax.set_xlim(min(deltas) - pad - 1.5, max(deltas) + pad + 1.5)

    fig.text(0.015, 0.02,
             "Source: OMB SF-132 apportionments, mirrored CC0 at data.blazingstaranalytics.com  ·  "
             "reproducible: github.com/abigailhaddad/blazingstar-data",
             fontsize=8, color="#888")
    fig.savefig("weekly_reapportionments.png", dpi=200, facecolor="white")
    print(f"wrote weekly_reapportionments.png  (data generated_at {generated}, "
          f"window {start.date()}→{anchor.date()}, {n} accounts, net +${net:.1f}B)")


if __name__ == "__main__":
    main()
