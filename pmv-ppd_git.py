from pythermalcomfort.models import pmv_ppd_iso
import pandas as pd
import numpy as np
import os

# --- PATH CONFIGURATION ---
# Get the absolute path of the directory where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define relative paths for data input and results output
# This ensures the code works on any computer without modification
data_folder = os.path.join(BASE_DIR, "data")
output_directory = os.path.join(BASE_DIR, "output")

# Create the output directory automatically if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# --- DATA LOADING: SURVEY RESPONSES ---
# Path to the thermal comfort survey CSV file
survey_file = os.path.join(data_folder, "survey_responses.csv")

# Read the CSV (comma separated, no header in the source file)
values = pd.read_csv(survey_file, sep=',', header=None)

# Rename columns for clarity
values.columns = ['time', 'sex', 'age', 'office', 'clothing', 'activity', 'TSV', 'change']

# Create a reduced DataFrame focusing on key variables for analysis
df_survey_reduced = values[['time', 'office', 'clothing', 'activity']].copy()

# --- DATA LOADING: PHYSICAL PARAMETERS ---
# Path to the environmental measurements CSV file (temperature, humidity, etc.)
physical_file = os.path.join(data_folder, "physical_parameters.csv")

# Read the physical data CSV
values2 = pd.read_csv(physical_file, sep=',', header=None)

# Define column names: dry bulb temp (tdb), radiant temp (tr), air velocity (vr), relative humidity (rh)
values2.columns = ['time', 'office', 'tdb', 'tr', 'vr', 'rh']

# Select relevant columns for the final merging process
df_physical_parameters = values2[['time', 'office', 'tdb', 'tr', 'vr', 'rh']].copy()

# --- PREPARE SURVEY DATAFRAME ---
# Convert 'time' to datetime objects so pandas can calculate temporal "proximity"
df_survey_reduced['time'] = pd.to_datetime(df_survey_reduced['time'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
df_survey_reduced = df_survey_reduced.dropna(subset=['time'])

# Convert 'office' to string to avoid type conflicts during merging
df_survey_reduced['office'] = df_survey_reduced['office'].astype(str)

# MANDATORY SORTING (Required for merge_asof)
df_survey_reduced = df_survey_reduced.sort_values('time')


# --- PREPARE PHYSICAL PARAMETERS DATAFRAME ---
df_physical_parameters['time'] = pd.to_datetime(df_physical_parameters['time'], format='%m/%d/%Y %H:%M:%S', errors='coerce')
df_physical_parameters = df_physical_parameters.dropna(subset=['time'])

# Convert 'office' to string
df_physical_parameters['office'] = df_physical_parameters['office'].astype(str)

# MANDATORY SORTING (Required for merge_asof)
df_physical_parameters = df_physical_parameters.sort_values('time')

# --- DATA MERGING (Nearest Neighbor Join) ---
try:
    # merge_asof matches the survey time to the closest physical measurement time within the same office
    df_final = pd.merge_asof(
        df_survey_reduced,
        df_physical_parameters,
        on='time',
        by='office',
        direction='nearest'
    )

    # Final column selection
    df_final = df_final[['clothing', 'activity', 'tdb', 'tr', 'vr', 'rh']]
    print("Merging successful!")
    print(df_final.head())

except Exception as e:
    print(f"Error during merging: {e}")

# --- SAVE MERGED DATAFRAME ---
file_name = 'merged_data.csv'
full_path = os.path.join(output_directory, file_name)

# Ensure output directory exists
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Save as CSV (Semicolon separator for European Excel compatibility)
df_final.to_csv(full_path, index=False, sep=';', encoding='utf-8-sig')
print(f"Success! Merged file generated at: {full_path}")

# --- MAPPING CLO AND MET VALUES (ISO 7730) ---
# Mapping clothing descriptions to insulation values (clo)
clo_mapping = {
    "Caleçon, combinaison, chaussettes, chaussures": 0.70,
    "Caleçon, chemise, combinaison, chaussettes, chaussures": 0.80,
    "Caleçon, chemise, pantalon, blouse, chaussettes, chaussures": 0.90,
    "Sous-vêtements à manches et jambes courtes, chemise, pantalon, veste, chaussettes, chaussures": 1.00,
    "Sous-vêtements à manches et jambes longues, veste isolante, chaussettes, chaussures": 1.20,
    "Sous-vêtements à manches et jambes courtes, chemise, pantalon, veste, veste et pantalon isolants, chaussettes, chaussures, casquette, gants": 1.40,
    "Sous-vêtements à manches et jambes courtes, chemise, pantalon, veste, veste et pantalon isolants, chaussettes, chaussures": 2.00,
    "Sous-vêtements à manches et jambes longues, veste et pantalon isolant, parka isolante, combinaison ouatinée, chaussettes, chaussures, casquette, gants": 2.55
}

# Mapping activity descriptions to metabolic rates (met)
met_mapping = {
    "Repos, couché": 0.8,
    "Repos, assis": 1.0,
    "Activité sédentaire (bureau, domicile, école, laboratoire)": 1.2,
    "Activité légère, debout (achats, laboratoire, industrie légère)": 1.6,
    "Activité moyenne, debout (vente, travail ménager, travail sur machine)": 2.0,
    "Marche à plat: 2 km/h": 1.9,
    "Marche à plat: 3 km/h": 2.4,
    "Marche à plat: 4 km/h": 2.8,
    "Marche à plat: 5 km/h": 3.4
}

# Clean strings (remove leading/trailing spaces) to ensure matching
df_final['clothing'] = df_final['clothing'].str.strip()
df_final['activity'] = df_final['activity'].str.strip()

# Apply numerical values based on dictionaries
df_final['clo_value'] = df_final['clothing'].map(clo_mapping)
df_final['met_value'] = df_final['activity'].map(met_mapping)

# Reorganize columns for final layout
final_columns = ['clothing', 'clo_value', 'activity', 'met_value', 'tdb', 'tr', 'vr', 'rh']
df_final_clo_met = df_final[final_columns]

# Save the CLO/MET result
file_name_clo_met = 'merged_data_clo_met.csv'
full_path_clo_met = os.path.join(output_directory, file_name_clo_met)
df_final_clo_met.to_csv(full_path_clo_met, index=False, sep=';', encoding='utf-8-sig')
print(f"Success! CLO/MET file generated at: {full_path_clo_met}")

# --- PMV & PPD CALCULATIONS ---
# 1. Force conversion to numeric types and handle invalid values
calculation_cols = ['tdb', 'tr', 'vr', 'rh', 'met_value', 'clo_value']
for col in calculation_cols:
    df_final[col] = pd.to_numeric(df_final[col], errors='coerce')

# 2. Drop rows with missing values that would cause calculation errors
df_clean = df_final.dropna(subset=calculation_cols).copy()

# 3. Define calculation function with internal error handling
def compute_comfort(row):
    try:
        res = pmv_ppd_iso(
            tdb=float(row['tdb']),
            tr=float(row['tr']),
            vr=float(row['vr']),
            rh=float(row['rh']),
            met=float(row['met_value']),
            clo=float(row['clo_value']),
            model="7730-2005"
        )
        return pd.Series({'pmv': res['pmv'], 'ppd': res['ppd']})
    except Exception:
        # Return None if calculation fails for specific row data
        return pd.Series({'pmv': None, 'ppd': None})

# 4. Apply the PMV/PPD model
print("Calculating PMV/PPD indices...")
df_results_values = df_clean.apply(compute_comfort, axis=1)

# 5. Assemble final results dataframe
df_results = pd.concat([df_clean[calculation_cols], df_results_values], axis=1)

# --- SAVE FINAL COMFORT RESULTS ---
file_name_results = 'comfort_results.csv'
full_path_results = os.path.join(output_directory, file_name_results)

df_results.to_csv(full_path_results, index=False, sep=';', encoding='utf-8-sig')
print(f"Success! Final calculation file generated at: {full_path_results}")