#This code uses the SMILES format of each molecule to put the molecule in a 3D space, optimizes geometry using the MMFF force field, then saves each molecule as a .pdb file in a specific directory.
import os
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

csv_file_path = r"C:\Users\samue\Downloads\QSARCommonlyExposedSMILESOutput.csv"
output_directory = r"C:\Users\samue\Downloads\QSAR_PDB_Files"

def convert_csv_to_pdb(csv_file, output_dir):
    df = pd.read_csv(csv_file)

    df = df.dropna(subset=['SMILES'])

    df['SMILES'] = df['SMILES'].str.replace('-', '') #Removes hyphens from SMILES for rdkit

    def is_valid_smiles(smiles):
        try:
            return Chem.MolFromSmiles(smiles) is not None
        except:
            return False

    df = df[df['SMILES'].apply(is_valid_smiles)]

    print("Columns in CSV:", df.columns.tolist()) #For debugging

    required_columns = ['Name', 'SMILES'] #This is a check that these columns exist and is required for the code to run
    for col in required_columns:
        if col not in df.columns:
            raise KeyError(f"The column '{col}' is missing from the CSV file. Available columns are: " + ", ".join(df.columns))

    os.makedirs(output_dir, exist_ok=True)

    for index, row in df.iterrows(): #Converts each chemical in spreadsheet
        name = row['Name']
        smiles = row['SMILES']
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                print(f"Failed to convert SMILES to molecule for {name} (SMILES: {smiles})")
                continue

            mol = Chem.AddHs(mol)

            try:
                AllChem.EmbedMolecule(mol, randomSeed=42)
                AllChem.MMFFOptimizeMolecule(mol) #MMFF force field
            except Exception as e:
                print(f"Optimization failed for {name}: {e}")
                continue

            output_file = os.path.join(output_dir, f"{name}.pdb")
            Chem.MolToPDBFile(mol, output_file)
        except Exception as e:
            print(f"An error occurred with {name} (SMILES: {smiles}): {e}")

convert_csv_to_pdb(csv_file_path, output_directory)

