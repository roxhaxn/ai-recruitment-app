import os
import json
import pandas as pd

def combine_json_to_csv(json_folder="parsed_resumes", output_csv="parsed_resumes/parsed_output.csv"):
    records = []

    for file in os.listdir(json_folder):
        if file.endswith(".json"):
            with open(os.path.join(json_folder, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                records.append(data)

    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False)
    print(f"✅ Combined {len(df)} JSON files into {output_csv}")
    return df

if __name__ == "__main__":
    combine_json_to_csv()

