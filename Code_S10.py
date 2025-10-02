import time
import pandas as pd
import sys
import rowan 

# Rowan API Key: Actual key not disclosed for privacy reasons
rowan.api_key = "rowan_key_here"

def dummy_compute_workflow(name, molecule, workflow):
    import random
    fukui_positive = [random.random() for _ in range(3)]
    return {"object_status": 1, "object_data": {"fukui_positive": fukui_positive}}

def run_fukui_calculations(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    # Create F+ column if it doesn't exist
    if "F+" not in df.columns:
        df["F+"] = ""
    
    for idx, row_data in df.iterrows():
        smiles = str(row_data["SMILES"]).strip()
        print(f"Processing row {idx}, SMILES: {smiles}")
       
        try:
            res = dummy_compute_workflow(
                name=f"Fukui_{idx}",
                molecule=smiles,
                workflow="fukui"
            )
           
            # Check the object status (0 means failure)
            status = res.get("object_status", None)
            if status == 0:
                print(f"Row {idx}: Returned status 0; marking F+ as NA.")
                df.at[idx, "F+"] = "NA"
            else:
                object_data = res.get("object_data", {})
                if "fukui_positive" not in object_data:
                    print(f"Row {idx}: No 'fukui_positive' data found; marking F+ as NA.")
                    df.at[idx, "F+"] = "NA"
                else:
                    fukui_pos = object_data["fukui_positive"]
                    # Find the highest F(+) value and its atom index.
                    highest_value = max(fukui_pos)
                    highest_index = max(range(len(fukui_pos)), key=lambda i: fukui_pos[i])
                    df.at[idx, "F+"] = highest_value
                    print(f"Row {idx}: Highest F(+) = {highest_value} (Atom index: {highest_index})")
        except Exception as e:
            print(f"Row {idx}: Exception encountered: {e}; marking F+ as NA.")
            df.at[idx, "F+"] = "NA"

        # Every 5 chemicals, save the incomplete results.
        if (idx + 1) % 5 == 0:
            desired_order = ["CASRN", "IONIZATION POTENTIAL", "HOMO", "LUMO", "MOLECULAR WEIGHT", "SMILES", "F+"]
            df = df.reindex(columns=desired_order)
            df.to_csv(output_csv, index=False)
            print(f"Intermediate save after processing {idx + 1} chemicals.")
            time.sleep(1)

    # Re-order the columns and save output
    desired_order = ["CASRN", "IONIZATION POTENTIAL", "HOMO", "LUMO", "MOLECULAR WEIGHT", "SMILES", "F+"]
    df = df.reindex(columns=desired_order)
    df.to_csv(output_csv, index=False)
    print(f"Results saved to {output_csv}")

if __name__ == "__main__":
    # Actual file paths not disclosed for privacy reasons
    input_file = r"Input_File_Path"
    output_file = r"Output_File_Path"
    run_fukui_calculations(input_file, output_file)
