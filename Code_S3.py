#This code creates a directory of PDBQT files from a directory of PDB files, using OpenBabel for the conversion from .pdb to .pdbqt file format.
import os
import subprocess

obabel_path = r"C:\Program Files\OpenBabel-3.1.1\obabel.exe"

input_dir = r"C:\Users\samue\Downloads\QSAR_PDB_Files"
output_dir = r"C:\Users\samue\Downloads\QSAR_PDBQT_Files"

os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if filename.endswith(".pdb"):
        input_file = os.path.join(input_dir, filename)
        output_file = os.path.join(output_dir, filename.replace(".pdb", ".pdbqt"))
        print(f"Processing: {input_file} -> {output_file}")
        try:
            command = [obabel_path, input_file, "-O", output_file]
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"Converted {input_file} to {output_file}")
        except FileNotFoundError:
            print(f"Error: obabel executable not found. Check obabel_path.")
        except subprocess.CalledProcessError as e:
            print(f"Error converting {input_file}: {e.stderr.decode().strip()}")


