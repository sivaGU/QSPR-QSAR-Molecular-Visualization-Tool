import os
import glob
import csv
import re
import sys

# Folder containing the .out files
folder_path = r"Path_To_out_Files" # Actual path not disclosed for privacy reasons

# Output CSV file name
output_csv = "MOPAC results.csv"

# Get a list of all .out files in the folder
out_files = glob.glob(os.path.join(folder_path, "*.out"))
if not out_files:
    print("No OUT files found in the folder.")
    sys.exit()

results = [] # Store results in list

for file_path in out_files:
    # Extract CASRN from the filename
    casrn = os.path.splitext(os.path.basename(file_path))[0]
    
    molecular_weight = None
    homo = None
    lumo = None
    
    with open(file_path, "r") as f:
        for line in f:
            # Extract Molecular Weight
            if "MOLECULAR WEIGHT" in line:
                mw_match = re.search(r"MOLECULAR WEIGHT\s*=\s*([\d\.]+)", line)
                if mw_match:
                    molecular_weight = mw_match.group(1)
            
            # Extract HOMO and LUMO energies
            if "HOMO LUMO ENERGIES" in line:
                hl_match = re.search(r"HOMO LUMO ENERGIES.*=\s*([-.\d]+)\s+([-.\d]+)", line)
                if hl_match:
                    homo = hl_match.group(1)
                    lumo = hl_match.group(2)
    
    # Only add the file's data if all values were successfully extracted
    if molecular_weight is not None and homo is not None and lumo is not None:
        results.append((casrn, molecular_weight, homo, lumo))
    else:
        print(f"Warning: Unable to extract all values from file {file_path}")

# Put results in csv file
with open(output_csv, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["CASRN", "Molecular Weight", "HOMO", "LUMO"])
    for row in results:
        writer.writerow(row)

print(f"Results successfully written to '{output_csv}'")
