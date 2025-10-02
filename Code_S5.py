#This code takes an spreadsheet input file with ChemSpider links for each chemical, and  webscrapes each chemical's page to generate an output file with chemical descriptors for each chemical.
#This code was specifically used to generate the spreadsheet for the Top 50 PFAS Binders for Estrogen Receptor Alpha and Beta
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

def load_input(file_path):
    return pd.read_csv(file_path)

def extract_numeric_value(property_text): #Returns the first number from a string
    match = re.search(r"[-+]?[0-9]*\.?[0-9]+", property_text)
    return float(match.group(0)) if match else None

def scrape_chemspider(url):
    headers = { #For the HTTP request header
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            properties = {}
            rows = soup.find_all('tr')
            for row in rows: #Finds number after specific HTML code for each chemical property
                title_tag = row.find('td', class_='prop_title')
                value_tag = row.find('td', class_='prop_value_nowrap') or row.find('td', class_='prop_value')
                if title_tag and value_tag:
                    title = title_tag.get_text(strip=True)
                    value = value_tag.get_text(strip=True)
                    numeric_value = extract_numeric_value(value)
                    properties[title] = numeric_value
            return properties
        else:
            print(f"Failed to fetch URL: {url} (Status Code: {response.status_code})")
            return {}
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return {}

def main():
    input_file = r"C:\Users\samue\Downloads\ERBetaInput.csv" #Also used for ERAlpha input and output
    output_file = r"C:\Users\samue\Downloads\ERBetaOutput.csv"

    data = load_input(input_file)
    required_properties = [ #Specifies list of chemical properties to scrape for each chemical in the spreadsheet
        '#Freely Rotating Bonds',
        '#H bond acceptors',
        '#H bond donors',
        'ACD/LogD (pH 7.4)',
        'ACD/LogP',
        'Boiling Point',
        'Density',
        'Enthalpy of Vaporization',
        'Polar Surface Area',
        'Polarizability',
        'Surface Tension'
    ]

    scraped_data = {col: [] for col in required_properties}

    for idx, row in data.iterrows(): #Adds each property to the spreadsheet
        url = row.get('ChemSpyder')
        if pd.notna(url) and url.startswith("http"):
            scraped_properties = scrape_chemspider(url)
            for prop in required_properties:
                scraped_data[prop].append(scraped_properties.get(prop, None))
        else:
            for prop in required_properties:
                scraped_data[prop].append(None)

    for prop in required_properties:
        data[prop] = scraped_data[prop]

    data.to_csv(output_file, index=False)
    print(f"Scraped data saved to {output_file}")

if __name__ == "__main__":
    main()

