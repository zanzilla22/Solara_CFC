from flask import Flask, jsonify, render_template
import requests, csv
from bs4 import BeautifulSoup
from io import StringIO

app = Flask(__name__)

# ignore selective detectors; nh; sh; global
#N+ S-; E+ W-
CFC_areaCoords = {
    "alt": (82.5, -62.3),
    "sum": (72.6, -38.4),
    "brw": (71.3, -156.6),
    "mhd": (53, -10),
    "thd": (41, -124),
    "nwr": (40.052, -105.585),
    "kum": (19.5, -154.8),
    "mlo": (19.5, -155.6),
    "smo": (-14.3, -170.6),
    "cgo": (-40.7, 144.8),
    "psa": (-64.6, -64.0),
    "spo": (-90, 0),  # South Pole (90S) can be represented as (90, 0)
}
pix_size =  256
tiles = 3
scale_factor = pix_size * tiles / 90 #90 is the max for long/lat magnitude
CFC_areaCoords = {key: (lat * scale_factor, lon * scale_factor) for key, (lat, lon) in CFC_areaCoords.items()}

@app.route('/get_flux_data', methods=['GET'])
def get_flux_data():
    print("trying to get flux data")
    url = 'https://spaceweather.gc.ca/forecast-prevision/solar-solaire/solarflux/sx-5-flux-en.php'
    response = requests.get(url)

    if response.status_code == 200:
        print("accessed")
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'table table-bordered'})
        # print(soup)
        if table:
            # Find the last row in the table
            last_row = table.find_all('tr')[-1]

            # Extract the last row's data as a list
            last_row_data = [cell.text.strip() for cell in last_row.find_all('td')]

            print(last_row_data)
            return jsonify(last_row_data)

    else:
        print("site reference was goodnt")

    return jsonify({'error': 'Table not found'}), 404

def cfcRasterImage(no):
    CFC_link_index = {
        11: "https://gml.noaa.gov/aftp/data/hats/cfcs/cfc11/combined/HATS_global_F11.txt",
        12: "https://gml.noaa.gov/aftp/data/hats/cfcs/cfc12/combined/HATS_global_F12.txt",
        13: "https://gml.noaa.gov/aftp/data/hats/cfcs/cfc113/combined/HATS_global_F113.txt",
    }

    response = requests.get(CFC_link_index[no])

    # Check if the request was successful
    if response.status_code == 200:
        # Convert the response content (CSV data) into a string
        csv_data = response.text

        # Use StringIO to treat the string as a file-like object
        csv_file = StringIO(csv_data)

        # Create a CSV reader object
        csv_reader = csv.reader(csv_file)

        rows = list(csv_reader)

        # header row is index 67
        print("Header row i think idk")
        # both length 33
        header = rows[67][0].split()
        latestFilledData = 0
        for i in range(len(rows) - 1, -1, -1):
            if 'nan' not in rows[i][0].split():
                latestFilledData = (rows[i][0].split())
                break  # Stop looking further

        print(header[8].split('_')[1])
        # data = {(CFC_areaCoords[header[i].split('_')[1]] if header[i].split('_')[1] in [key for key in CFC_areaCoords] and len(header[i].split('_')) == 3 else header[i]): latestFilledData[i] for i in range(len(header))}
        data = {(CFC_areaCoords[header[i].split('_')[1]] if header[i].split('_')[1] in [key for key in CFC_areaCoords] and len(header[i].split('_')) == 3 else ""): float(latestFilledData[i]) for i in range(len(header))}
        del data[""]

        print(data)
    else:
        print(f"Failed to fetch CSV data. Status code: {response.status_code}")


@app.route('/', methods=['GET'])
def index():
    # print(get_flux_data())
    cfcRasterImage(11)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
