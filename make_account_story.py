"""Tell the story of one Treasury account over time, from SF-132 apportionments.

For the White House Repair and Restoration no-year account (EOP 011-X-0109),
chart apportioned budget authority FY2022-2026, split by funding source:
direct appropriation vs. reimbursable/collected funds vs. balance brought
forward. The point the chart makes: the appropriation is flat; the growth is
entirely reimbursable/collected. Writes white_house_account.png.

Data: BlazingStar's CC0 mirror of OMB SF-132. Every figure traces to a
mirror_url with a published SHA-256.
"""
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import requests

TAFS = "011-X-0109"
FYS = range(2022, 2027)
APPROP = "#69539E"      # BlazingStar purple
REIMB = "#2A9D8F"       # teal
CARRY = "#C9C9C9"       # gray

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "blazingstar-data-demo (https://github.com/abigailhaddad/blazingstar-data)"})


def latest_schedule(fy, tafs):
    idx = SESSION.get(f"https://cdn.bzstr.co/sf132/fy{fy}/index.json", timeout=90).json()
    rows = [f for f in idx["files"] if f.get("file_type") == "data_json" and f["tafs"] == tafs]
    if not rows:
        return None
    f = max(rows, key=lambda r: int(r["iteration"]))
    return SESSION.get(f["mirror_url"], timeout=60).json()


def buckets(js):
    """Bucket schedule lines into appropriation / reimbursable / brought-forward (millions)."""
    approp = reimb = carry = 0
    for s in js["ScheduleData"]:
        ln = str(s["LineNumber"])
        amt = s["ApprovedAmount"] or 0
        if ln.startswith("6") or ln in ("1910", "1920", "1930"):
            continue                     # apportionment / total side — skip to avoid double count
        if ln.startswith("11"):
            approp += amt                # direct appropriation
        elif ln.startswith(("17", "18")):
            reimb += amt                 # spending authority from collections / reimbursements
        elif ln.startswith("10"):
            carry += amt                 # unobligated balance brought forward / recoveries
    return approp / 1e6, reimb / 1e6, carry / 1e6


def main():
    fys, approp, reimb, carry = [], [], [], []
    for fy in FYS:
        js = latest_schedule(fy, TAFS)
        if not js:
            continue
        a, r, c = buckets(js)
        fys.append(fy); approp.append(a); reimb.append(r); carry.append(c)
    totals = [a + r + c for a, r, c in zip(approp, reimb, carry)]

    fig, ax = plt.subplots(figsize=(10.5, 7.2))
    fig.subplots_adjust(top=0.74, bottom=0.10, left=0.10, right=0.97)
    x = range(len(fys))

    ax.bar(x, carry, color=CARRY, label="Balance brought forward")
    ax.bar(x, reimb, bottom=carry, color=REIMB, label="Reimbursable / collected funds")
    ax.bar(x, approp, bottom=[c + r for c, r in zip(carry, reimb)], color=APPROP,
           label="Direct appropriation")

    for xi, total in zip(x, totals):
        ax.text(xi, total + max(totals) * 0.015, f"${total:,.0f}M", ha="center",
                va="bottom", fontsize=11, fontweight="bold", color="#222")

    ax.set_xticks(list(x))
    ax.set_xticklabels([f"FY{fy}" for fy in fys], fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}M"))
    ax.set_ylim(0, max(totals) * 1.12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#ededed", lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", frameon=False, fontsize=10.5)

    # Annotate the punchline near the FY2026 bar.
    last = len(fys) - 1
    ax.annotate(f"Reimbursable / collected funds:\n${reimb[0]:,.1f}M (FY{fys[0]}) → ${reimb[-1]:,.0f}M (FY{fys[-1]})",
                xy=(last, carry[-1] + reimb[-1] * 0.5), xytext=(last - 1.9, max(totals) * 0.62),
                fontsize=10.5, color=REIMB, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=REIMB, lw=1.4))
    ax.annotate(f"Congress's appropriation never moved:\n~${approp[-1]:,.1f}M every year",
                xy=(last, totals[-1]), xytext=(last - 2.4, max(totals) * 0.86),
                fontsize=10.5, color=APPROP, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=APPROP, lw=1.4))

    fig.text(0.055, 0.945, "A tiny White House account grew to $323M — almost none of it appropriated",
             fontsize=15, fontweight="bold", color=APPROP, ha="left", va="top")
    fig.text(0.10, 0.885,
             "Apportioned budget authority for EOP account 011-X-0109, FY2022–FY2026. The direct appropriation stayed flat at\n"
             "~$2.5M; the growth is reimbursable / collected funds (Economy Act transfers and collections). Two sibling accounts\n"
             "push the full FY2026 family past $840M. Figures are budgetary resources, not cash spent.",
             fontsize=9.5, color="#555", ha="left", va="top", linespacing=1.5)
    fig.text(0.10, 0.02,
             "Source: OMB SF-132 apportionments, mirrored CC0 at data.blazingstaranalytics.com  ·  "
             "reproducible: github.com/abigailhaddad/blazingstar-data",
             fontsize=8, color="#888")

    fig.savefig("white_house_account.png", dpi=200, facecolor="white")
    print("wrote white_house_account.png")
    for fy, t, a, r in zip(fys, totals, approp, reimb):
        print(f"  FY{fy}: total ${t:,.1f}M  (approp ${a:,.1f}M, reimb ${r:,.1f}M)")


if __name__ == "__main__":
    main()
