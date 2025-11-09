import requests
import pandas as pd

url = "http://localhost:5000/api/ingestion/template"
response = requests.get(url)

if response.status_code == 200:
    # The content is in CSV format, so we can read it with pandas
    df = pd.read_csv(pd.io.common.StringIO(response.text))
    
    # Save the DataFrame to an Excel file
    df.to_excel("patient_visit_template.xlsx", index=False)
    print("Successfully created patient_visit_template.xlsx")
else:
    print(f"Failed to download template. Status code: {response.status_code}")