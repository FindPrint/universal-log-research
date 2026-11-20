#!/usr/bin/env python3
"""Extract and audit public supplementary tables/source data for Aronchik et al. (2026).

This is a descriptive reanalysis of selected published data, not a new treatment
discovery, an independent replication, or clinical advice.
"""
from __future__ import annotations
import csv, hashlib, io, json, re, zipfile
from datetime import datetime, timezone
from pathlib import Path
import platform
from xml.etree import ElementTree as ET
import numpy as np
import pandas as pd
import scipy
from scipy.stats import chi2, fisher_exact, mannwhitneyu
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "reanalyzed"
XLSX = ROOT / "41591_2026_4537_MOESM3_ESM.xlsx"
FIG4 = ROOT / "41591_2026_4537_MOESM7_ESM.zip"
FIG5 = ROOT / "41591_2026_4537_MOESM8_ESM.zip"
PAPER = "https://doi.org/10.1038/s41591-026-04537-w"
NS = {"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1 << 20), b""): h.update(block)
    return h.hexdigest()

def read_xlsx(path):
    """Read cached cell values with stdlib XML, without modifying the venv."""
    with zipfile.ZipFile(path) as z:
        ss=[]
        if "xl/sharedStrings.xml" in z.namelist():
            ssroot=ET.fromstring(z.read("xl/sharedStrings.xml"))
            ss=["".join(t.text or "" for t in si.findall(".//m:t",NS))
                for si in ssroot.findall("m:si",NS)]
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        rr=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rels={e.attrib["Id"]:e.attrib["Target"] for e in rr}
        result={}
        for sh in wb.findall("m:sheets/m:sheet",NS):
            target=rels[sh.attrib["{"+NS["r"]+"}id"]].lstrip("/")
            if not target.startswith("xl/"): target="xl/"+target
            root=ET.fromstring(z.read(target)); rows=[]
            for row in root.findall(".//m:sheetData/m:row",NS):
                vals={}
                for c in row.findall("m:c",NS):
                    letters=re.match(r"[A-Z]+",c.attrib.get("r","A"))[0]
                    col=0
                    for ch in letters: col=col*26+ord(ch)-64
                    col-=1
                    if c.attrib.get("t")=="inlineStr":
                        val="".join(t.text or "" for t in c.findall(".//m:t",NS))
                    else:
                        v=c.find("m:v",NS); val="" if v is None else v.text or ""
                        if c.attrib.get("t")=="s" and val: val=ss[int(val)]
                    vals[col]=val
                rows.append([vals.get(i,"") for i in range(max(vals)+1)] if vals else [])
            result[sh.attrib["name"]]=rows
        return result

def csv_rows(path, rows):
    width=max(map(len,rows),default=0)
    with path.open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f)
        for row in rows: w.writerow(row+[""]*(width-len(row)))

def value_text(x):
    return str(x.get("string","") if isinstance(x,dict) else (x or ""))

def bh(p):
    p=np.asarray(p,float); ix=np.argsort(p); z=p[ix]
    qsort=np.minimum.accumulate((z*len(z)/np.arange(1,len(z)+1))[::-1])[::-1]
    out=np.empty_like(qsort); out[ix]=qsort
    return np.minimum(out,1).tolist()

def extract_clinical():
    sheets=read_xlsx(XLSX)
    output_map={
        "Supplementary Table 1":"clinical_high_dose_44.csv",
        "Supplementary Table 2":"clinical_lower_dose_13.csv",
        "Supplementary Table 3":"clinical_KRAS_amplification_16.csv",
        "Supplementary Table 4":"clinical_baseline_genomics_57.csv",
        "Supplementary Table 5":"preclinical_model_inventory.csv"}
    for name,file in output_map.items(): csv_rows(OUT/file,sheets[name])
    def frame(name):
        rows=sheets[name]; header=[str(x).replace("\n"," ").strip() for x in rows[1]]
        body=[r[:len(header)] for r in rows[2:] if r and str(r[0]).strip().startswith("Patient ")]
        return pd.DataFrame(body,columns=header)
    hi=frame("Supplementary Table 1"); lo=frame("Supplementary Table 2")
    sv="Acquired short variants in RAS signaling pathway (not present at baseline)"
    cn="Acquired copy number alterations in RAS signaling pathway (not present at baseline)"
    def detected(v):
        x=str(v).strip().lower()
        return bool(x) and "not detected" not in x and "not tested" not in x
    for df in (hi,lo):
        df["pathway_alteration"]=df[sv].map(detected)|df[cn].map(detected)
        df["KRAS_amp"]=df[cn].str.contains(r"\bKRAS\s+AMP\b",case=False,regex=True)
    hi["TP53_mut"]=hi["Pretreatment TP53 Status"].str.strip().str.lower().eq("mut")
    hi["event_text_count"]=hi.apply(lambda r:sum(
        len([x for x in str(r[c]).split(";") if detected(x)]) for c in (sv,cn)),axis=1)
    tp=hi.groupby("TP53_mut")["KRAS_amp"].agg(["sum","count"])
    m,mn=int(tp.loc[True,"sum"]),int(tp.loc[True,"count"])
    w,wn=int(tp.loc[False,"sum"]),int(tp.loc[False,"count"])
    a=int(hi.pathway_alteration.sum()); b=len(hi)-a
    c=int(lo.pathway_alteration.sum()); d=len(lo)-c
    tests=[]
    for label,table in [
        ("TP53 status vs acquired KRAS amplification",[[m,mn-m],[w,wn-w]]),
        ("160-300 mg vs <=120 mg: pathway acquisition",[[a,b],[c,d]])]:
        odds,p=fisher_exact(table,alternative="two-sided")
        tests.append({"comparison":label,"2x2":json.dumps(table),"odds_ratio":odds,"fisher_two_sided_p":p})
    metrics=[
        ("higher_dose_cohort_n",len(hi)),("higher_dose_pathway_alteration_n",a),
        ("higher_dose_acquired_KRAS_amp_n",int(hi.KRAS_amp.sum())),
        ("higher_dose_multiple_events_text_n",int((hi.event_text_count>1).sum())),
        ("higher_dose_secondary_KRAS_variant_text_n",int(hi[sv].str.contains(r"KRAS\s+[A-Z]\d",case=False,regex=True).sum())),
        ("TP53_mut_KRAS_amp",f"{m}/{mn}"),("TP53_wt_KRAS_amp",f"{w}/{wn}"),
        ("lower_dose_cohort_n",len(lo)),("lower_dose_pathway_alteration_n",c),
        ("lower_dose_acquired_KRAS_amp_n",int(lo.KRAS_amp.sum()))]
    pd.DataFrame(metrics,columns=["metric","value"]).to_csv(OUT/"clinical_replication_metrics.csv",index=False)
    pd.DataFrame(tests).to_csv(OUT/"clinical_replication_tests.csv",index=False)
    return metrics,tests

def extract_waterfalls(zip_path,label):
    raw=[]; summaries=[]
    with zipfile.ZipFile(zip_path) as outer:
        for member in outer.namelist():
            if not member.lower().endswith(".prism"): continue
            try:
                inner=zipfile.ZipFile(io.BytesIO(outer.read(member)))
                doc=json.loads(inner.read("document.json"))
            except (zipfile.BadZipFile,KeyError,json.JSONDecodeError): continue
            plotted=set()
            for gid in doc.get("sheets",{}).get("graphs",[]):
                graph=json.loads(inner.read(f"graphs/{gid}/sheet.json"))
                plotted.update(graph.get("inputDataSets",[]))
            for sid in doc.get("sheets",{}).get("data",[]):
                sh=json.loads(inner.read(f"data/sheets/{sid}/sheet.json"))
                if "waterfall" not in sh.get("title","").lower(): continue
                table=sh["table"]; groups=[]
                for did in table["dataSets"]:
                    ds=json.loads(inner.read(f"data/sets/{did}.json"))
                    groups.append((did,ds,value_text(ds.get("title"))))
                text=inner.read(f"data/tables/{table['uid']}/data.csv").decode("utf-8-sig")
                data=list(csv.reader(io.StringIO(text)))
                fmt=table.get("format",""); dformat=table.get("dataFormat","")
                nrep=int(table.get("replicatesCount",1))
                for j,(did,ds,group) in enumerate(groups):
                    if plotted and did not in plotted: continue
                    observations=[]
                    if fmt=="grouped" and dformat=="y_single":
                        for row_i,row in enumerate(data):
                            if j<len(row) and row[j].strip():
                                try: observations.append((row_i,float(row[j]),True,""))
                                except ValueError: pass
                    elif dformat=="y_replicates" and fmt in ("nested","grouped"):
                        # A nested Prism dataset is a block of replicatesCount
                        # adjacent columns; metadata marks absent/excluded animals.
                        valid={}
                        for item in ds.get("replicate ranges",[]):
                            parts=item.get("range","").split("~")
                            try:
                                start,end=int(parts[0]),int(parts[-1])
                                meta=item.get("replicate",{})
                                first=int(meta.get("firstRow",0)); last=int(meta.get("lastRow",len(data)-1))
                            except (ValueError,TypeError): continue
                            excluded=set()
                            for attr in meta.get("cellAttributes",[]):
                                if "EXCLUDED" in attr.get("attributes",[]):
                                    excluded.update(int(x) for x in str(attr.get("rows","")).split(",") if x.strip().isdigit())
                            for subcol in range(start,end+1): valid[subcol]=(first,last,excluded)
                        for row_i,row in enumerate(data):
                            for subcol in range(nrep):
                                if subcol not in valid: continue
                                first,last,excluded=valid[subcol]
                                cell=1+j*nrep+subcol # first field is the row title
                                if row_i<first or row_i>last or cell>=len(row) or not row[cell].strip(): continue
                                try: val=float(row[cell])
                                except ValueError: continue
                                observations.append((subcol,val,row_i not in excluded,"excluded in GraphPad" if row_i in excluded else ""))
                    else:
                        continue
                    vals=[]
                    for i,(subcol,v,included,reason) in enumerate(observations,1):
                        raw.append({"source_archive":label,"source_member":member,
                                    "sheet":sh["title"],"treatment":group,"animal_index":i,
                                    "percent_change_volume":v,"included_in_summary":included,
                                    "exclusion_reason":reason})
                        if included: vals.append(v)
                    if vals:
                        z=np.asarray(vals,float)
                        summaries.append({"source_archive":label,"source_member":member,
                          "sheet":sh["title"],"treatment":group,"n":len(z),
                          "mean_pct":float(z.mean()),"median_pct":float(np.median(z)),
                          "q1_pct":float(np.quantile(z,.25)),"q3_pct":float(np.quantile(z,.75)),
                          "regression_fraction":float(np.mean(z<0)),
                          "at_least_30pct_regression_fraction":float(np.mean(z<=-30))})
    return pd.DataFrame(raw),pd.DataFrame(summaries)

def combo_endpoint_comparisons(raw):
    """Exploratory independent-animal endpoint contrasts for three published models."""
    targets=[("4f Waterfall","Fig4f KP-4, daraxonrasib + amivantamab"),
             ("5g Waterfall","Fig5g parental HPAF-II, RAS(ON) doublet"),
             ("5h Waterfall","Fig5h resistant HPAF-II, RAS(ON) doublet")]
    rows=[]
    for token,label in targets:
        x=raw[(raw.source_member.str.contains(token,case=False,regex=False)) & raw.included_in_summary]
        if x.empty:continue
        by={k:g.percent_change_volume.to_numpy() for k,g in x.groupby("treatment")}
        # Fig. 4f names its mixed arm "Combination"; Fig. 5g/h name agents with '+'.
        comb=next((k for k in by if "combination" in k.lower() or "+" in k),None)
        if not comb:continue
        model_rows=[]; pvals=[]
        for arm,z in by.items():
            if arm==comb or arm.lower()=="control":continue
            test=mannwhitneyu(by[comb],z,alternative="two-sided",method="exact")
            rng=np.random.default_rng(20261116+len(rows)+len(model_rows))
            bcombo=np.median(rng.choice(by[comb],(20000,len(by[comb])),replace=True),axis=1)
            barm=np.median(rng.choice(z,(20000,len(z)),replace=True),axis=1)
            ci=np.quantile(bcombo-barm,[.025,.975])
            model_rows.append({"model_and_figure":label,"comparison":f"{comb} vs {arm}",
              "n_combo":len(by[comb]),"n_single":len(z),
              "median_combo_pct":float(np.median(by[comb])),"median_single_pct":float(np.median(z)),
              "delta_median_combo_minus_single":float(np.median(by[comb])-np.median(z)),
              "bootstrap_ci95_low":float(ci[0]),"bootstrap_ci95_high":float(ci[1]),
              "mann_whitney_exact_p":float(test.pvalue),
              "interpretation":"lower percent change means greater regression; exploratory; same published animals"})
            pvals.append(float(test.pvalue))
        for row,q in zip(model_rows,bh(pvals)):row["BH_q_within_model_comparisons"]=q
        rows.extend(model_rows)
    return pd.DataFrame(rows)

def extract_fig5d_survival(zip_path):
    """Extract mouse-level time-to-tumor-doubling/censoring from GraphPad survival table."""
    records=[]
    with zipfile.ZipFile(zip_path) as outer:
        member=next(n for n in outer.namelist() if "Figure 5d.prism" in n and n.endswith(".prism"))
        inner=zipfile.ZipFile(io.BytesIO(outer.read(member)))
        doc=json.loads(inner.read("document.json"))
        graph_ids=set()
        for gid in doc.get("sheets",{}).get("graphs",[]):
            graph=json.loads(inner.read(f"graphs/{gid}/sheet.json"));graph_ids.update(graph.get("inputDataSets",[]))
        sid=doc["sheets"]["data"][0]
        sheet=json.loads(inner.read(f"data/sheets/{sid}/sheet.json"));table=sheet["table"]
        actual_ids=set(table["dataSets"])
        plotted_ids=graph_ids & actual_ids
        titles=[]
        for did in table["dataSets"]:
            ds=json.loads(inner.read(f"data/sets/{did}.json"))
            titles.append((did,value_text(ds.get("title"))))
        text=inner.read(f"data/tables/{table['uid']}/data.csv").decode("utf-8-sig")
        for row in csv.reader(io.StringIO(text)):
            if len(row)<2 or not row[0].strip() or not row[1].strip():continue
            try: time=float(row[1])
            except ValueError:continue
            events=[]
            for j,(did,name) in enumerate(titles):
                if plotted_ids and did not in plotted_ids:continue
                cell=2+j
                if cell<len(row) and row[cell].strip():
                    try: events.append((name,int(float(row[cell]))))
                    except ValueError:pass
            if len(events)!=1:continue
            treatment,event=events[0]
            records.append({"source_member":member,"model":row[0].strip(),"treatment":treatment,
                            "time_to_tumor_doubling_days":time,"event_progression":event})
    return pd.DataFrame(records)

def logrank_two_group(data,group_col,time_col,event_col,a,b):
    x=data[data[group_col].isin([a,b])].copy()
    times=np.sort(x.loc[x[event_col].eq(1),time_col].unique())
    oe=0.0; var=0.0
    for t in times:
        at_risk=x[time_col].ge(t)
        n1=int((at_risk & x[group_col].eq(a)).sum()); n2=int((at_risk & x[group_col].eq(b)).sum())
        d1=int((x[group_col].eq(a) & x[time_col].eq(t) & x[event_col].eq(1)).sum())
        d2=int((x[group_col].eq(b) & x[time_col].eq(t) & x[event_col].eq(1)).sum())
        n=n1+n2; d=d1+d2
        if n<=1:continue
        oe += d1 - d*n1/n
        var += (n1*n2*d*(n-d))/(n*n*(n-1))
    stat=(oe*oe/var) if var>0 else 0.0
    return {"group_a":a,"group_b":b,"n_a":int((x[group_col]==a).sum()),"n_b":int((x[group_col]==b).sum()),
            "events_a":int(((x[group_col]==a)&(x[event_col]==1)).sum()),
            "events_b":int(((x[group_col]==b)&(x[event_col]==1)).sum()),
            "logrank_chi2_1df":stat,"p_two_sided":float(chi2.sf(stat,1))}

def logrank_omnibus(data,group_col,time_col,event_col):
    groups=list(data[group_col].dropna().unique());u=np.zeros(len(groups));cov=np.zeros((len(groups),len(groups)))
    for t in np.sort(data.loc[data[event_col].eq(1),time_col].unique()):
        risk=np.array([((data[group_col].eq(g)) & data[time_col].ge(t)).sum() for g in groups],dtype=float)
        events=np.array([((data[group_col].eq(g)) & data[time_col].eq(t) & data[event_col].eq(1)).sum() for g in groups],dtype=float)
        n=risk.sum();d=events.sum()
        if n<=1 or d<=0:continue
        prob=risk/n;u+=events-d*prob
        cov+=(d*(n-d)/(n-1))*(np.diag(prob)-np.outer(prob,prob))
    stat=float(u @ np.linalg.pinv(cov) @ u)
    return {"groups":json.dumps(groups,ensure_ascii=False),"n_total":len(data),"events_total":int(data[event_col].sum()),
            "logrank_chi2":stat,"df":len(groups)-1,"p_two_sided":float(chi2.sf(stat,len(groups)-1))}

def km_curve(data,time_col,event_col):
    times=np.sort(data[time_col].unique());surv=1.0;ts=[0.0];ss=[1.0]
    for t in times:
        n=int((data[time_col]>=t).sum());d=int(((data[time_col]==t)&(data[event_col]==1)).sum())
        if n>0 and d>0:
            surv*=1-d/n;ts.append(float(t));ss.append(surv)
    return np.asarray(ts),np.asarray(ss)

def summarize_fig5d_survival(data):
    rows=[]
    for treatment,g in data.groupby("treatment"):
        t,s=km_curve(g,"time_to_tumor_doubling_days","event_progression")
        med=next((float(ti) for ti,si in zip(t,s) if si<=.5),None)
        horizon=float(data.time_to_tumor_doubling_days.max());area=0.0;prev=0.0;sv=1.0
        # Integrate the right-continuous KM step function through the common horizon.
        for ti,si in zip(t[1:],s[1:]):
            area+=sv*(ti-prev);prev=ti;sv=si
        area+=sv*(horizon-prev)
        rows.append({"treatment":treatment,"n":len(g),"progression_events":int(g.event_progression.sum()),
                     "censored":int((1-g.event_progression).sum()),"KM_median_days":med,
                     "RMST_to_common_max_followup_days":area,"common_max_followup_days":horizon})
    return pd.DataFrame(rows)

def plot_fig5d_survival(data,path):
    palette=["#888888","#2878B5","#E08E2F","#25855A"]
    fig,ax=plt.subplots(figsize=(9,6))
    for color,(name,g) in zip(palette,data.groupby("treatment",sort=False)):
        t,s=km_curve(g,"time_to_tumor_doubling_days","event_progression")
        ax.step(t,s,where="post",linewidth=2,label=f"{name} (n={len(g)})",color=color)
        cens=g[g.event_progression.eq(0)]
        if not cens.empty:
            # Place censor marks at the corresponding KM estimate just before/at censor time.
            cx=[];cy=[]
            for ct in cens.time_to_tumor_doubling_days:
                ix=np.searchsorted(t,ct,side="right")-1;cx.append(ct);cy.append(s[max(ix,0)])
            ax.scatter(cx,cy,marker="+",s=32,color=color,zorder=4)
    ax.set(xlabel="Jours jusqu’au doublement tumoral (PFS préclinique)",ylabel="Probabilité sans progression estimée",
           title="KPC/Y : survie Kaplan–Meier — données source Figure 5d")
    ax.set_ylim(0,1.03);ax.set_xlim(left=0);ax.grid(alpha=.23);ax.legend(fontsize=8,loc="best")
    fig.tight_layout();fig.savefig(path,dpi=180);plt.close(fig)

def main():
    OUT.mkdir(exist_ok=True)
    metrics,ctests=extract_clinical()
    raws=[]; sums=[]
    for p,label in ((FIG4,"source_data_Fig4"),(FIG5,"source_data_Fig5")):
        if p.exists():
            r,s=extract_waterfalls(p,label);raws.append(r);sums.append(s)
    raw=pd.concat(raws,ignore_index=True) if raws else pd.DataFrame()
    summ=pd.concat(sums,ignore_index=True) if sums else pd.DataFrame()
    raw.to_csv(OUT/"prism_waterfall_animals.csv",index=False)
    summ.to_csv(OUT/"prism_waterfall_summary.csv",index=False)
    ftests=combo_endpoint_comparisons(raw)
    ftests.to_csv(OUT/"preclinical_combo_endpoint_comparisons.csv",index=False)
    surv=extract_fig5d_survival(FIG5)
    surv.to_csv(OUT/"fig5d_mouse_time_to_doubling.csv",index=False)
    surv_summary=summarize_fig5d_survival(surv)
    surv_summary.to_csv(OUT/"fig5d_KM_summary.csv",index=False)
    combo=next((x for x in surv.treatment.unique() if "+" in x),None)
    mono=[x for x in surv.treatment.unique() if x!=combo and x!="Vehicle"]
    logtests=[logrank_two_group(surv,"treatment","time_to_tumor_doubling_days","event_progression",mono[0],mono[1]),
              *[logrank_two_group(surv,"treatment","time_to_tumor_doubling_days","event_progression",combo,x) for x in mono]]
    for row,q in zip(logtests,bh([x["p_two_sided"] for x in logtests])):row["BH_q_three_pairwise"]=q
    pd.DataFrame(logtests).to_csv(OUT/"fig5d_logrank_combo_vs_monos.csv",index=False)
    pd.DataFrame([logrank_omnibus(surv,"treatment","time_to_tumor_doubling_days","event_progression")]).to_csv(OUT/"fig5d_logrank_omnibus.csv",index=False)
    plot_fig5d_survival(surv,OUT/"figure5d_pfs_km.png")
    mm=dict(metrics)
    f4=summ[(summ.source_archive=="source_data_Fig4") & summ.source_member.str.contains("4f Waterfall",case=False,regex=False)]
    tlines="\n".join(f"- {t['comparison']}: OR={t['odds_ratio']:.4g}; Fisher p={t['fisher_two_sided_p']:.5g}; table={t['2x2']}" for t in ctests)
    flines="\n".join(f"- Fig. {figure}: {r.treatment} (n={int(r.n)}): médiane {r.median_pct:.1f}%, moyenne {r.mean_pct:.1f}%, régression <0: {r.regression_fraction:.0%}, régression ≥30%: {r.at_least_30pct_regression_fraction:.0%}." for figure,token in (("4f KP-4","4f Waterfall"),("5g parental HPAF-II","5g Waterfall"),("5h résistant HPAF-II","5h Waterfall")) for r in summ[(summ.source_archive.str.startswith("source_data_Fig")) & summ.source_member.str.contains(token,case=False,regex=False)].itertuples())
    ftestlines="\n".join(f"- {r.model_and_figure}: {r.comparison}: Δ médian {r.delta_median_combo_minus_single:.1f} points (IC bootstrap 95% {r.bootstrap_ci95_low:.1f} à {r.bootstrap_ci95_high:.1f}); p exact Mann–Whitney {r.mann_whitney_exact_p:.4g}; q BH dans le modèle {r.BH_q_within_model_comparisons:.4g}." for r in ftests.itertuples())
    survlines="\n".join(f"- {r.treatment}: n={r.n}, événements={r.progression_events}, censures={r.censored}, médiane KM={r.KM_median_days if pd.notna(r.KM_median_days) else 'non atteinte'} jours, RMST jusqu’à {r.common_max_followup_days:g} j={r.RMST_to_common_max_followup_days:.2f} jours." for r in surv_summary.itertuples())
    loglines="\n".join(f"- {r['group_a']} vs {r['group_b']}: n={r['n_a']}/{r['n_b']}, événements={r['events_a']}/{r['events_b']}, log-rank chi2(1)={r['logrank_chi2_1df']:.3f}, p={r['p_two_sided']:.5g}, q BH sur les trois comparaisons={r['BH_q_three_pairwise']:.5g}." for r in logtests)
    omnibus=logrank_omnibus(surv,"treatment","time_to_tumor_doubling_days","event_progression")
    report=f"""# Réanalyse traçable: résistance au daraxonrasib dans le PDAC

Généré (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}  
Article primaire: Aronchik et al., Nature Medicine (2026), {PAPER}.  
Nature de ce travail: réplication arithmétique/descriptive de données publiées. Ce n'est ni une découverte thérapeutique indépendante, ni une preuve de guérison, ni un avis médical.

## Résumé scientifique

L'article décrit des altérations acquises de signalisation RAS dans un groupe sélectionné de patients ayant bénéficié initialement du daraxonrasib puis progressé. Les données publiées et les expériences précliniques pointent vers une réactivation du flux RAS/MAPK et évaluent des associations avec ciblage RTK, double inhibition RAS(ON), ou réponse aux dommages de l'ADN (DDR). Ces pistes sont déjà rapportées par les auteurs; notre apport ici est de préserver et recalculer une partie des tables/données source, avec des limites explicites.

## Contexte clinique actuel

Au 16 novembre 2026, la FDA a approuvé le daraxonrasib (RASONQUE) le 26 août 2026 pour certains adultes atteints d'un adénocarcinome pancréatique métastatique après au moins une ligne systémique ou non candidats à une thérapie multi-agents. Dans l'essai randomisé de 500 personnes, la médiane de survie globale rapportée était 13,2 contre 6,7 mois (HR 0,40), et la médiane de survie sans progression 7,2 contre 3,6 mois. Ce bénéfice important ne signifie pas guérison: l'étude de résistance que nous réanalysons porte précisément sur la progression après un bénéfice initial. Ces résultats cliniques ne valident pas les doubles combinaisons testées chez la souris; l'intérêt de ce projet est de prioriser les questions de résistance et de biomarqueurs, pas de conseiller un traitement à une personne. Source FDA: https://www.fda.gov/drugs/cancer-approvals/fda-approves-daraxonrasib-metastatic-pancreatic-adenocarcinoma.

Mise à jour clinique vérifiée le 16 novembre 2026: un essai randomisé de phase III actif (RASolute 309; NCT07805954) évalue daraxonrasib + zoldonrasib contre gemcitabine + nab-paclitaxel en première ligne chez des patients avec PDAC métastatique KRAS G12D. L'essai est une question clinique déjà en cours, pas un résultat d'efficacité ni une preuve de guérison. Source NCI: https://www.cancer.gov/research/participate/clinical-trials-search/v?id=NCI-2026-06840.

## Réplication des comptes cliniques du supplément

- Cohorte à 160–300 mg/j: n={mm['higher_dose_cohort_n']}; altération acquise signalée dans les colonnes « RAS signaling pathway »: {mm['higher_dose_pathway_alteration_n']}; KRAS amplification acquise: {mm['higher_dose_acquired_KRAS_amp_n']}.
- Cohorte distincte à ≤120 mg/j: n={mm['lower_dose_cohort_n']}; événements dans ces colonnes: {mm['lower_dose_pathway_alteration_n']}; KRAS amplification: {mm['lower_dose_acquired_KRAS_amp_n']}. Ce n'est pas un bras témoin randomisé.
- KRAS amplification par statut TP53 prétraitement dans la cohorte haute dose: TP53-mut {mm['TP53_mut_KRAS_amp']}; TP53-wt {mm['TP53_wt_KRAS_amp']}.
- Plus d'un événement textuel trouvé par séparation des points-virgules dans les deux colonnes d'altérations: {mm['higher_dose_multiple_events_text_n']}. Ce compte mécanique n'est pas une nouvelle classification de voies.
- Variants KRAS secondaires repérés par motif textuel simple: {mm['higher_dose_secondary_KRAS_variant_text_n']}; ce contrôle ne remplace pas l'annotation experte.

Tests de Fisher recalculés:
{tlines}

Ces proportions concordent avec les chiffres de l'article (26/44 pour les altérations de voie et 16/44 pour KRAS amplification). La cohorte est sélectionnée sur une réponse/stabilisation initiale, puis une progression. Sans patients comparateurs qui ne progressent pas, cette table ne permet pas d'estimer un prédicteur général de résistance.

## Réanalyse exploratoire de points finaux précliniques Figures 4f, 5g et 5h

Les valeurs extraites des fichiers source Prism sont des pourcentages individuels de changement de volume tumoral: KP-4 avec amivantamab, HPAF-II parental et HPAF-II résistant avec double inhibition RAS(ON). Une valeur plus négative signifie une régression plus grande:

{flines}

Comparaisons exploratoires de médianes à ce point final:
{ftestlines}

Ces tests sur les points finaux ne reproduisent pas l'ANOVA à mesures répétées des auteurs. Il s'agit des mêmes animaux et expériences que la publication; ce n'est pas une validation indépendante. Le fichier Fig. 5h contient 8 valeurs non manquantes pour le bras combiné malgré n=9 dans la légende. Ce manque est conservé comme limite de complétude de la source. Les petits effectifs, le modèle choisi et le biais de publication limitent toute extrapolation à des personnes.

## Durée avant progression dans le modèle KPC/Y (Figure 5d)

Le fichier source Prism contient les temps individuels jusqu'au doublement tumoral et les indicateurs de progression/censure des trois modèles. J'ai recalculé les courbes Kaplan–Meier, les médianes si atteintes, la moyenne de survie restreinte (RMST) jusqu'au dernier suivi commun et un test log-rank bilatéral contre chaque monothérapie. Le statut 1 est interprété comme progression et 0 comme censure, conformément au format de la table de survie GraphPad et à la définition PFS de l'article.

{survlines}

Test log-rank omnibus recalculé sur les quatre bras: chi2({omnibus['df']})={omnibus['logrank_chi2']:.3f}, p={omnibus['p_two_sided']:.5g}. Comparaisons à deux groupes:
{loglines}

Le recalcul retrouve p≈0,046684 pour les deux monothérapies et p<0,0001 pour chacune des comparaisons doublet/monothérapie, cohérent avec les analyses Prism embarquées et la légende de la figure. Ce contrôle de cohérence vérifie l'extraction/calcul, pas une réplication indépendante. Le test groupé n'inclut pas de stratification par modèle.

## Usage honnête du pipeline universel ici

1. Des colonnes pertinentes comme TP53 prétraitement, variant KRAS, dose, altérations acquises, VAF pré/on/fin, modèle préclinique, traitement et volume tumoral peuvent être traitées comme flux liés et documentés; chaque flux doit garder son unité d'observation et son rôle causal supposé.
2. Le contrôle de sélection important est le patient ou l'animal. Les trois prélèvements d'une personne ne peuvent pas être concaténés et considérés comme trois personnes indépendantes. Les données ctDNA disponibles sont 44 personnes sélectionnées, pas un axe libre de 132 observations.
3. Pas de T0/TLog calculé sur cette table: le protocole courant exige n≥50; en outre, l'axe par personne est longitudinal/irrégulier, et l'inclusion est conditionnée à la progression. Le bon travail sur le pipeline est un mode longitudinal avec permutations par blocs (au niveau patient/animal), critères d'abstention et correction multiple définie avant de lire les résultats.
4. Le criblage PRISM de l'audit précédent a comparé 6 790 flux médicamenteux à 13 contrôles de dépendance sur au plus 38 modèles PDAC. Aucun résultat ne franchissait la correction globale des comparaisons. Le signal KRAS–AS-77 avait q=0,0413 dans la famille KRAS mais q=0,246 après correction sur les 13 contrôles; AS-77 n'est donc pas une piste validée. Le daraxonrasib n'était pas dans PRISM 24Q2: ce criblage ne valide aucune des combinaisons de l'étude récente.
5. « Tous les contrôles » ne signifie pas traiter chaque champ numérique comme un axe scientifique équivalent. L'identifiant patient/animal est une unité de regroupement, le bras de traitement est catégoriel, le temps est longitudinal, et les mesures biologiques ont des unités et des limites de détection. Le futur mode multi-contrôles doit conserver ces types, le lien entre flux et contrôle, ainsi que les blocs patient/animal, sans ordonner artificiellement des cellules ou des lignées.

## Décisions de recherche recommandées

1. Valider une cohorte externe avec prélèvements prétraitement, tôt sous traitement, progression et groupe sans progression, en corrigeant les limites de détection/shedding et en préenregistrant les définitions d'événements.
2. Prioriser des combinaisons par biomarqueur, pas de façon universelle: HER2 élevé/induit pour T-DXd; activité EGFR/MET pour amivantamab; amplification KRAS/flux RAS élevé pour intensifier blocage RAS; TP53 altéré et stress réplicatif pour DDR. Les associations sont déjà des hypothèses publiées à vérifier, et les profils bénéfice/risque diffèrent.
3. Refaire les essais de combinaison en matrices de dose dans des organoïdes humains indépendants, avec bras véhicule/mono/combo, réplicats biologiques, critères Bliss/Loewe/HSA prédéfinis, mesures de viabilité/apoptose et toxicité sur cellules non tumorales.
4. Actualiser le criblage cellulaire et génétique avec des données DepMap/PRISM versionnées et annotées. Le précédent écran PRISM était 24Q2; il ne comprend pas daraxonrasib.
5. Suivre les résultats de RASolute 309 et préparer une validation externe par biomarqueur. Le projet ne doit pas présenter la double inhibition comme traitement établi avant que l'essai rapporte ses résultats.

## Fichiers générés

- reanalyze_daraxonrasib_source_data.py: extraction/calculs reproductibles; aucune dépendance installée.
- clinical_replication_metrics.csv, clinical_replication_tests.csv: comptes et Fisher.
- clinical_high_dose_44.csv, clinical_lower_dose_13.csv et autres CSV: suppléments extraits.
- prism_waterfall_animals.csv, prism_waterfall_summary.csv: mesures individuelles/descriptives extraites des feuilles source « Waterfall » Figures 4 et 5; cellules exclues par GraphPad conservées mais non utilisées pour les résumés.
- preclinical_combo_endpoint_comparisons.csv: comparaisons exploratoires pour Fig. 4f et Fig. 5g/h.
- fig5d_mouse_time_to_doubling.csv, fig5d_KM_summary.csv, fig5d_logrank_combo_vs_monos.csv, fig5d_logrank_omnibus.csv, figure5d_pfs_km.png: réanalyse de temps-événement et graphiques.
- manifest.json: empreintes SHA-256 et sources.

## Reproduction

Depuis PowerShell, lancer le script avec l'interpréteur de l'environnement .venv du projet. Le code n'installe pas de paquet et conserve les suppléments téléchargés à côté de lui.

## Limites

- Phase 1/2 simple bras; échantillonnage ctDNA conditionné par shedding et progression; aucune combinaison testée chez l'humain par cet article.
- Environ 40% des personnes de l'analyse n'ont pas de mécanisme génomique de résistance identifié.
- Les données précliniques proviennent d'expériences publiées, pas d'un laboratoire indépendant.
- Une réponse animale ou une association statistique n'est pas un remède ni une preuve d'efficacité clinique.

## Journal de correction

La première extraction locale (v1, générée le 2026-11-17 à 00:23 UTC) a interprété incorrectement le format GraphPad imbriqué des fichiers Fig. 5 comme une matrice plate: elle produisait n=1 par bras. Après inspection du format interne, la version actuelle suit les blocs de 7 sous-colonnes, les groupes réellement tracés et les cellules exclues par GraphPad. Les résumés Fig. 5 de v1 sont supersédés et ne doivent pas être cités. La Fig. 4f était au format de table plate; son extraction n'a pas changé.

Le manifeste exclut le PDF généré et son fichier .sha256 afin d'éviter un hachage circulaire (le PDF contient le manifeste et le .sha256 contient le hachage du PDF). Le PDF est vérifié indépendamment par son fichier .sha256.
"""
    (OUT/"RAPPORT_REANALYSE_DARAXONRASIB.md").write_text(report,encoding="utf-8")
    manifest={"created_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
      "paper":PAPER,
      "source_urls":{
        "supplementary_tables":"https://static-content.springer.com/esm/art%3A10.1038%2Fs41591-026-04537-w/MediaObjects/41591_2026_4537_MOESM3_ESM.xlsx",
        "source_data_figures_4":"https://static-content.springer.com/esm/art%3A10.1038%2Fs41591-026-04537-w/MediaObjects/41591_2026_4537_MOESM7_ESM.zip",
        "source_data_figures_5":"https://static-content.springer.com/esm/art%3A10.1038%2Fs41591-026-04537-w/MediaObjects/41591_2026_4537_MOESM8_ESM.zip",
        "clinical_context_fda":"https://www.fda.gov/drugs/cancer-approvals/fda-approves-daraxonrasib-metastatic-pancreatic-adenocarcinoma",
        "clinical_context_phase3":"https://www.cancer.gov/research/participate/clinical-trials-search/v?id=NCI-2026-06840"},
      "runtime":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,"scipy":scipy.__version__},
      "parser_revision":"2; GraphPad nested replicates mapped by block and excluded cells honored; v1 Fig. 5 extraction superseded",
      "inputs":{p.name:{"sha256":sha256(p),"bytes":p.stat().st_size} for p in (XLSX,FIG4,FIG5) if p.exists()},
      "script":{"name":Path(__file__).name,"sha256":sha256(Path(__file__))},
      "outputs":{p.name:{"sha256":sha256(p),"bytes":p.stat().st_size}
                 for p in sorted(OUT.iterdir()) if p.is_file() and p.name!="manifest.json"
                 and p.suffix.lower()!=".pdf" and not p.name.lower().endswith(".pdf.sha256")},
      "interpretation":"Published selected cohort and animal experiments; reanalysis is not independent replication or evidence of cure."}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print(report[:report.index("## Réanalyse exploratoire")])
    print("\nFIGURE 4f summaries:\n"+flines+"\n"+ftestlines)
    print("\nOutput folder:",OUT)

if __name__=="__main__":main()
