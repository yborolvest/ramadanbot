#!/usr/bin/env python3
"""
Helper script to inspect KNMI NetCDF files and find station IDs/names.
This will help identify the correct station code for De Bilt.
"""

import os
import tempfile
import requests

try:
    import netCDF4
    import numpy as np
except ImportError:
    print("Error: netCDF4 and numpy are required. Install with: pip install netCDF4 numpy")
    exit(1)

# Use the same API key as the main script
KNMI_API_KEY = os.environ.get("KNMI_API_KEY") or "eyJvcmciOiI1ZTU1NGUxOTI3NGE5NjAwMDEyYTNlYjEiLCJpZCI6ImVlNDFjMWI0MjlkODQ2MThiNWI4ZDViZDAyMTM2YTM3IiwiaCI6Im11cm11cjEyOCJ9"

base_url = "https://api.dataplatform.knmi.nl/open-data/v1"
dataset_name = "10-minute-in-situ-meteorological-observations"
dataset_version = "1.0"

print("Fetching most recent observation file from KNMI...")
list_url = f"{base_url}/datasets/{dataset_name}/versions/{dataset_version}/files"
headers = {"Authorization": KNMI_API_KEY}

params = {
    "maxKeys": 1,
    "sorting": "desc",
    "orderBy": "lastModified"
}

list_resp = requests.get(list_url, headers=headers, params=params)
list_resp.raise_for_status()
list_data = list_resp.json()

if not list_data.get("files"):
    print("Error: No observation files found")
    exit(1)

filename = list_data["files"][0]["filename"]
print(f"Found file: {filename}")

# Get download URL
download_url_endpoint = f"{base_url}/datasets/{dataset_name}/versions/{dataset_version}/files/{filename}/url"
download_resp = requests.get(download_url_endpoint, headers=headers)
download_resp.raise_for_status()
download_data = download_resp.json()
temp_download_url = download_data["temporaryDownloadUrl"]

# Download and inspect
print("Downloading and inspecting file...")
with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp_file:
    tmp_path = tmp_file.name
    try:
        file_resp = requests.get(temp_download_url, stream=True)
        file_resp.raise_for_status()
        for chunk in file_resp.iter_content(chunk_size=8192):
            tmp_file.write(chunk)
        tmp_file.flush()
        
        with netCDF4.Dataset(tmp_path, 'r') as nc:
            print("\n=== Available Variables ===")
            print(", ".join(sorted(nc.variables.keys())))
            
            # Try to find station-related variables
            station_var = None
            station_name_var = None
            
            for var_name in ['wsi', 'WSI', 'station_id', 'STN', 'station', 'stations']:
                if var_name in nc.variables:
                    station_var = nc.variables[var_name]
                    print(f"\nFound station ID variable: {var_name}")
                    break
            
            if station_var is None:
                var_names_lower = {k.lower(): k for k in nc.variables.keys()}
                for check_name in ['wsi', 'station_id', 'stn', 'station', 'stations']:
                    if check_name in var_names_lower:
                        station_var = nc.variables[var_names_lower[check_name]]
                        print(f"\nFound station ID variable: {var_names_lower[check_name]}")
                        break
            
            # Try to find station name variable
            for var_name in ['stationname', 'station_name', 'name', 'NAME']:
                if var_name in nc.variables:
                    station_name_var = nc.variables[var_name]
                    print(f"Found station name variable: {var_name}")
                    break
            
            if station_var is not None:
                print("\n=== Station Information ===")
                station_data = np.array(station_var[:])
                station_list = station_data.flatten()
                
                # Get station names if available
                station_names = None
                if station_name_var is not None:
                    name_data = np.array(station_name_var[:])
                    # Handle string arrays
                    if name_data.dtype.kind == 'U' or name_data.dtype.kind == 'S':
                        station_names = name_data.flatten()
                    else:
                        station_names = None
                
                print(f"Total stations: {len(station_list)}")
                print("\nStation IDs and Names:")
                print("-" * 60)
                
                for i, station_id in enumerate(station_list):
                    station_id_str = str(station_id)
                    if station_names is not None and i < len(station_names):
                        name = station_names[i]
                        # Clean up name if it's bytes
                        if isinstance(name, bytes):
                            name = name.decode('utf-8', errors='ignore')
                        elif isinstance(name, np.ndarray):
                            name = str(name).strip()
                        print(f"  Station ID: {station_id_str:10s} | Name: {name}")
                        
                        # Highlight De Bilt
                        name_lower = str(name).lower()
                        if 'bilt' in name_lower or 'de bilt' in name_lower:
                            print(f"    *** THIS IS DE BILT! Use station_code = {station_id_str} ***")
                    else:
                        print(f"  Station ID: {station_id_str}")
                        # Check if it's 260 (known De Bilt code)
                        if str(station_id) == "260":
                            print(f"    *** This is likely De Bilt (WMO code 260) ***")
                
                # Also check coordinates if available
                if 'lat' in nc.variables and 'lon' in nc.variables:
                    print("\n=== Station Coordinates ===")
                    lat_data = np.array(nc.variables['lat'][:])
                    lon_data = np.array(nc.variables['lon'][:])
                    for i, station_id in enumerate(station_list):
                        if i < len(lat_data) and i < len(lon_data):
                            lat = float(lat_data[i]) if lat_data.ndim > 0 else float(lat_data)
                            lon = float(lon_data[i]) if lon_data.ndim > 0 else float(lon_data)
                            print(f"  Station {station_id}: Lat={lat:.4f}, Lon={lon:.4f}")
                            # De Bilt is approximately at 52.1000°N, 5.1800°E
                            if abs(lat - 52.1000) < 0.1 and abs(lon - 5.1800) < 0.1:
                                print(f"    *** This matches De Bilt coordinates! Use station_code = {station_id} ***")
            else:
                print("\nWarning: Could not find station variable")
                print("Available variables:", ", ".join(nc.variables.keys()))
        
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

print("\n=== Inspection Complete ===")
