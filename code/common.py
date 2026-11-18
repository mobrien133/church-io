"""Loaders shared across scripts: Scorecard programs merged with FSA financing, thresholds, in-state shares and polity."""
import numpy as np
import pandas as pd
import config as C

POLITY_LABELS = {"E": "Episcopal/hierarchical", "C": "Connectional/synodical", "G": "Congregational",
                 "M": "Assemblies-of-God type", "I": "Independent/interdenominational"}
YESHIVA = "Yeshiva|Talmud|Rabbinical|Mesivta|Medrash"
FIPS = {'AL': 1, 'AK': 2, 'AZ': 4, 'AR': 5, 'CA': 6, 'CO': 8, 'CT': 9, 'DE': 10, 'DC': 11, 'FL': 12, 'GA': 13, 'HI': 15, 'ID': 16,
        'IL': 17, 'IN': 18, 'IA': 19, 'KS': 20, 'KY': 21, 'LA': 22, 'ME': 23, 'MD': 24, 'MA': 25, 'MI': 26, 'MN': 27, 'MS': 28,
        'MO': 29, 'MT': 30, 'NE': 31, 'NV': 32, 'NH': 33, 'NJ': 34, 'NM': 35, 'NY': 36, 'NC': 37, 'ND': 38, 'OH': 39, 'OK': 40,
        'OR': 41, 'PA': 42, 'RI': 44, 'SC': 45, 'SD': 46, 'TN': 47, 'TX': 48, 'UT': 49, 'VT': 50, 'VA': 51, 'WA': 53, 'WV': 54,
        'WI': 55, 'WY': 56}


def thresholds():
    t = pd.read_csv(C.THRESHOLDS).set_index("state").threshold_2024
    return t.drop("US").to_dict()


def polity_map():
    """Author's coding of sponsoring bodies, with the corrections recorded in the README."""
    pol = pd.read_csv(C.POLITY_SHEET, dtype={"opeid6": str})
    pol["opeid6"] = pol.opeid6.str.zfill(6)
    pol.loc[pol.INSTNM == "SUM Bible College and Theological Seminary", ["sponsoring_body", "polity"]] = ["Independent Pentecostal", "G"]
    pol.loc[pol.INSTNM == "Ohio Christian University", "sponsoring_body"] = \
        "Churches of Christ in Christian Union (holiness; Salvation Army ties)"
    pol = pd.concat([pol, pd.DataFrame([dict(INSTNM="Bethel University (MN)", opeid6="009058", polity="G",
                                             sponsoring_body="Converge (formerly Baptist General Conference)")])], ignore_index=True)
    return pol, pol.drop_duplicates("opeid6").set_index("opeid6")[["polity", "sponsoring_body"]]


def fsa_institutions():
    f = C.DER / "fsa_institutions.csv"
    if not f.exists():
        raise SystemExit("Run 01_fsa_panel.py first.")
    return pd.read_csv(f, dtype={"opeid6": str})


def raw_scorecard():
    sc = pd.read_csv(C.SCORECARD, dtype=str, low_memory=False)
    num = lambda s: pd.to_numeric(s, errors="coerce")
    sc["earn4"] = num(sc.EARN_MDN_4YR); sc["earners4"] = num(sc.EARN_COUNT_WNE_4YR); sc["earn1"] = num(sc.EARN_MDN_1YR)
    sc["opeid6"] = sc.OPEID6.str.zfill(6)
    return sc


def instate_shares():
    """Share of first-time degree-seeking students from the institution's own state, IPEDS EF2022C (revised)."""
    ef = pd.read_csv(C.IPEDS_DIR / "ef2022c_rv.csv")
    tot = ef[ef.EFCSTATE == 99].set_index("UNITID").EFRES01
    own = ef[ef.EFCSTATE <= 56][["UNITID", "EFCSTATE", "EFRES01"]]
    return tot, own


def programs():
    """Every Scorecard program in the extract, at the rule's unit, with state, financing, thresholds and polity.
    Puerto Rico excluded; multi-campus records repeating a program's earnings dropped."""
    sc = raw_scorecard()
    inst = fsa_institutions()[["opeid6", "state", "type", "no_dl_5y", "dl_usd_2526", "pell_usd_2526", "years_with_dl", "dl_ug_recip_2526"]]
    _, polmap = polity_map()
    sc = sc.merge(inst, on="opeid6", how="left").merge(polmap, left_on="opeid6", right_index=True, how="left")
    sc = sc[sc.state != "PR"].drop_duplicates(subset=["opeid6", "CIPCODE", "CREDLEV", "earn4"]).copy()
    sc["no_dl_5y"] = sc.no_dl_5y.astype(str).eq("True")
    sc["th"] = sc.state.map(thresholds())
    sc["yeshiva"] = sc.INSTNM.str.contains(YESHIVA, case=False, regex=True)
    tot, own = instate_shares()
    sc["UNITIDn"] = pd.to_numeric(sc.UNITID, errors="coerce")
    ownmap = own.groupby(["UNITID", "EFCSTATE"]).EFRES01.sum()

    def share(u, st):
        if pd.isna(u) or int(u) not in tot.index or st not in FIPS or tot[int(u)] == 0:
            return np.nan
        return ownmap.get((int(u), FIPS[st]), 0) / tot[int(u)]
    sc["instate"] = [share(u, s) for u, s in zip(sc.UNITIDn, sc.state)]
    sc["th_rule"] = np.where(sc.instate < 0.5, C.NATIONAL_HS, sc.th)
    sc["th_rule"] = np.where(sc.th.isna(), np.nan, sc.th_rule)
    return sc


def religion_ba(sc=None):
    """The 237 scored religion bachelor's programs (CIP 38-39, reported four-year earnings, a U.S. state threshold)."""
    sc = programs() if sc is None else sc
    ba = sc[sc.CIPCODE.str[:2].isin(["38", "39"]) & (sc.CREDLEV == "3") & sc.earn4.notna() & sc.th.notna()].copy()
    ba["margin_rule"] = ba.earn4 - ba.th_rule
    ba["fail_rule"] = ba.earn4 < ba.th_rule
    ba["fail_state"] = ba.earn4 < ba.th
    ba["fail10_rule"] = ba.earn4 < ba.th_rule * 1.1
    ba["fail10_state"] = ba.earn4 < ba.th * 1.1
    return ba


def wmedian(v, w):
    v = np.asarray(v, float); w = np.asarray(w, float); o = np.argsort(v); v, w = v[o], w[o]
    c = np.cumsum(w)
    return float(v[np.searchsorted(c, c[-1] / 2)])


def save(df, name, index=False):
    p = C.TAB / name
    df.to_csv(p, index=index)
    print(f"  -> {p.relative_to(C.ROOT)}")
