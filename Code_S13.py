import os
from chimerax.core.commands import run

# This section has the user input the location of their original receptor protein, the location of their top output
# file of ligands, and the output folder to where the interacting residues in pdb format will be stored.
protein_path = r'insert pathname here'
ligands_folder = r'insert pathname here'
output_folder = r'insert pathname here'

# This section ensures that the output folder exists before proceeding
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# This section implements the iteration within ChimeraX that will export the interacting residues with the receptor
# protein, given the output files of the ligand.
for filename in os.listdir(ligands_folder):
    if filename.endswith('.pdbqt'):
        ligand_path = os.path.join(ligands_folder, filename)
        print(f"Processing {ligand_path}")
        # This section implements the ChimeraX commands needed to determine the interacting residues.
        run(session, f'open {protein_path}')
        run(session, f'open {ligand_path}')

        print("Executing viewdockx command")
        run(session, 'viewdockx #2.1-15')

        print("Hiding models")
        run(session, 'hide #2.1-15 models')

        print("Showing ligand model")
        run(session, 'show #2.1 models')

        print("Selecting ligand model atoms")
        run(session, 'select add #2.1')

        print("Selecting residues within 5 angstroms of the ligand")
        run(session, 'select sel :< 5')

        print("Showing interacting side chains")
        run(session, 'show (#2.1#!1 & sel-residues & sidechain) target ab')

        print("Labeling selected residues")
        run(session, 'label (#!1#!2.1 & sel) text "{0.name} {0.number}{0.insertion_code}"')

        # This section saves the selected residues to a pdb format.
        ligand_name = os.path.basename(ligand_path).replace('.pdbqt', '')
        output_file = os.path.join(output_folder, f'{ligand_name}_interacting_residues.pdb')
        run(session, f'save {output_file} selectedOnly true')
        print(f"Selected residues saved to {output_file}")

        run(session, 'close all')
