from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
source = ROOT / "supplemental_table_1_krasi_g12c_pdac_gi.xlsx"
df = pd.read_excel(source, header=2, dtype=str).fillna("")
df.columns = [str(c).strip().replace("\xa0", " ") for c in df.columns]
pdac = df[df["Tumor type"].str.strip().str.upper().eq("PDAC")]
print("columns:", list(df.columns))
print("source rows:", len(df), "PDAC rows:", len(pdac), "PDAC patients:", pdac["Patient ID"].nunique())
print("PDAC patients:", sorted(pdac["Patient ID"].unique(), key=lambda x: int(x.rsplit(" ", 1)[-1])))
print("Treatments / responses:\n", pdac.groupby(["Treatment", "Best response"]).size().to_string())
print("Gene / alteration combinations:\n", pdac.groupby(["Gene/variant", "Alteration type"]).size().to_string())
print("\nPATIENT DETAIL")
for (patient, treatment, response), group in pdac.groupby(["Patient ID", "Treatment", "Best response"], sort=False):
    details = " | ".join(
        f"{row['Gene/variant']} [{row['Alteration type']}] {row['Pre-treatment VAF (%)']} -> {row['End of Therapy VAF (%)']}"
        for _, row in group.iterrows()
    )
    print(patient, treatment, response, "\n ", details)
