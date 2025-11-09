import pandas as pd

df = pd.read_csv("patient_visit_template.csv")
df.to_excel("patient_visit_template.xlsx", index=False)

print("Successfully converted patient_visit_template.csv to patient_visit_template.xlsx")