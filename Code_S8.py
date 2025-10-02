import os
import time
import glob
import pyautogui

# Path to the Avogadro shortcut
avogadro_path = r"Path_To_Avogadro" # Actual path not disclosed for privacy reasons

# Folder containing the SDF files (ligands)
sdf_folder = r"SDF_Path" # Actual path not disclosed for privacy reasons

# Output Folder
output_folder = r"OutputFolder" # Actual path not disclosed for privacy reasons
os.makedirs(output_folder, exist_ok=True)

# Coordinates for the Exit button
exit_button_x, exit_button_y = 600, 450 

os.startfile(avogadro_path)
print("Launching Avogadro...")
time.sleep(10)

sdf_files = glob.glob(os.path.join(sdf_folder, "*.sdf"))
if not sdf_files:
    print("No SDF files found in the folder.")
    exit()

for sdf_file in sdf_files:
    casrn = os.path.splitext(os.path.basename(sdf_file))[0]
    print(f"Processing {casrn}...")

    # Open the SDF file in Avogadro
    pyautogui.hotkey('ctrl', 'o')
    time.sleep(1)
    pyautogui.write(sdf_file, interval=0.02)
    pyautogui.press('enter')
    time.sleep(3)

    # Open the Extensions menu and go to the desired option
    pyautogui.hotkey('alt', 'x')
    time.sleep(0.5)
    pyautogui.press('down', presses=9, interval=0.2)
    pyautogui.press('enter')
    pyautogui.press('enter')
    time.sleep(3)

    # In the Generate dialog, type the CASRN and hit Enter
    pyautogui.write(casrn, interval=0.02)
    pyautogui.press('enter')
    time.sleep(2)

    # Click the Exit button
    pyautogui.press('esc')
    time.sleep(1)
    # Close the current molecule and go to next file
    pyautogui.hotkey('ctrl', 'w')
    time.sleep(1)

print("Processing complete! All molecules have been processed.")


