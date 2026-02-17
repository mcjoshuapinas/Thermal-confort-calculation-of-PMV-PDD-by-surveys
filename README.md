Thermal Comfort Study (CERTES)
This project provides a Python-based workflow to merge subjective thermal comfort survey data with synchronized physical environmental parameters.

Features
Temporal Data Merging: Uses merge_asof to synchronize survey responses with the nearest physical measurements based on timestamps and office locations.

ISO 7730 Mapping: Automatically maps descriptive clothing and activity levels to numerical Clo (insulation) and Met (metabolic rate) values.

Comfort Indices Calculation: Computes the PMV (Predicted Mean Vote) and PPD (Predicted Percentage of Dissatisfied) indices using the pythermalcomfort library.

Libraries Used
pandas - For data manipulation and time-series merging.

numpy - For numerical operations.

pythermalcomfort - To implement the ISO 7730:2005 thermal comfort model.

matplotlib - For data visualization and plotting results.

Project Structure
data/: Folder containing raw CSV files (Surveys and Physical Parameters).

output/: Folder where processed datasets and comfort results are saved.

main_script.py: The primary Python script for the analysis.
