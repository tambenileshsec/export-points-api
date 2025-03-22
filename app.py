from flask import Flask, request, send_file
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pandas as pd
import tempfile
import os

app = Flask(__name__)

# Use built-in login for AGOL (replace with credentials if needed)

# Securely access credentials
AGOL_USERNAME = os.environ.get("AGOL_USERNAME")
AGOL_PASSWORD = os.environ.get("AGOL_PASSWORD")

gis = GIS("https://www.arcgis.com", AGOL_USERNAME, AGOL_PASSWORD)


# Your AGOL Feature Layer URLs
POLYGON_LAYER_URL = "https://services-eu1.arcgis.com/RD4JRHAllAtE3ymT/arcgis/rest/services/Secto_VM_Design_WFL1/FeatureServer/9"
POINT_LAYER_URL = "https://services-eu1.arcgis.com/RD4JRHAllAtE3ymT/arcgis/rest/services/Subunit_VM_Dataset/FeatureServer/0"

polygon_layer = FeatureLayer(POLYGON_LAYER_URL)
point_layer = FeatureLayer(POINT_LAYER_URL)

@app.route('/export_points')
def export_points():
    polygon_id = request.args.get("polygon_id")

    if not polygon_id:
        return "Error: 'polygon_id' parameter is required", 400

    # Query the selected polygon
    polygon_result = polygon_layer.query(where=f"OBJECTID = {polygon_id}", return_geometry=True)
    if not polygon_result.features:
        return "Polygon not found", 404

    polygon_geom = polygon_result.features[0].geometry

    # Query points that intersect with the selected polygon
    points_result = point_layer.query(
        geometry=polygon_geom,
        spatial_rel='esriSpatialRelIntersects',
        out_fields='*',
        return_geometry=False
    )

    if not points_result.features:
        return "No points found inside the selected polygon.", 200

    # Convert to DataFrame and export to Excel
    df = pd.DataFrame([f.attributes for f in points_result.features])
    temp_dir = tempfile.gettempdir()
    output_file = os.path.join(temp_dir, f"points_export_{polygon_id}.xlsx")
    df.to_excel(output_file, index=False, engine='openpyxl')

    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
