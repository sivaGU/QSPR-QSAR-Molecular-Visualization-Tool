import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


def convert_pdb_to_fasta(pdb_file_path):
    url = "https://zhanggroup.org/pdb2fasta/"

    # This section sets up the Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run headless if you do not want a visible browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)

        # This section uploads the PDB file from user.
        upload_button = driver.find_element(By.XPATH, '/html/body/p[2]/table/tbody/tr/td/form/p[1]/input')
        upload_button.send_keys(pdb_file_path)

        # This section submits the user form to convert the file.
        convert_button = driver.find_element(By.XPATH, '/html/body/p[2]/table/tbody/tr/td/form/p[2]/input[1]')
        convert_button.click()

        try:
            # This section waits for the result page to load and obtains the FASTA sequence.
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '/html/body/pre')))
            fasta_sequence = driver.find_element(By.XPATH, '/html/body/pre').text

            # This section removes the '>pdb:A' prefix if present, which gets inputted from the website. This allows the user to get the raw amino acid sequence.
            if fasta_sequence.startswith('>pdb:A'):
                fasta_sequence = fasta_sequence[len('>pdb:A'):].strip()

        except TimeoutException:
            # This section uses JavaScript to extract the FASTA sequence if an element is not found within the wait time.
            fasta_sequence = driver.execute_script("return document.body.textContent;").strip()
            if fasta_sequence.startswith('>pdb:A'):
                fasta_sequence = fasta_sequence[len('>pdb:A'):].strip()

        if fasta_sequence:
            return fasta_sequence
        else:
            print(f"FASTA sequence not found for {pdb_file_path}")
            return None
    finally:
        driver.quit()


def save_to_excel(data, excel_file_path):
    # This section creates a data frame.
    df = pd.DataFrame(data, columns=['Ligand Name', 'FASTA Sequence'])
    # This section saves the data frame to an excel.
    df.to_excel(excel_file_path, index=False)


# This main section inputs the user's filepath to the interacting residues PDB file folder and iterates through each one through the webscraping server.
def main():
    folder_path = r'insert pathname here'
    data = []

    for filename in os.listdir(folder_path):
        if filename.endswith('_interacting_residues.pdb'):
            pdb_file_path = os.path.join(folder_path, filename)
            ligand_name = filename.split('_')[0]
            fasta_sequence = convert_pdb_to_fasta(pdb_file_path)
            if fasta_sequence:
                data.append((ligand_name, fasta_sequence))

    save_to_excel(data, 'AA_New_BPAs.xlsx')


if __name__ == "__main__":
    main()



