from pathlib import Path

# Download the IDF files
import urllib.request

urllib.request.urlretrieve('https://www.energycodes.gov/sites/default/files/documents/ASHRAE901_OfficeSmall_STD2016.zip', 'IDFs.zip')

#Create directories if not already created
Path("IDF_directory").mkdir(parents=True, exist_ok=True)
Path("output").mkdir(parents=True, exist_ok=True)
Path("ep").mkdir(parents=True, exist_ok=True)

#Unzip IDFs
import zipfile
with zipfile.ZipFile('IDFs.zip', 'r') as zip_ref:
    zip_ref.extractall('IDF_directory')

import os

# Remove everything that is not an IDF
for item in os.listdir('IDF_directory'):
    if item.endswith(".idf") is not True:
        os.remove(os.path.join('IDF_directory', item))