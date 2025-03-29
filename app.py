from flask import Flask, request, send_file
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pandas as pd
import tempfile
import os

app = Flask(__name__)

USERNAME = "Design_Test"
PASSWORD = "Secto@123"
gis = GIS("https://www.arcgis.com", USERNAME, PASSWORD)

POLYGON_LAYER_URL = "https://services-eu1.arcgis.com/RD4JRHAllAtE3ymT/arcgis/rest/services/MDU_Masterplan_VM/FeatureServer/0"
POINT_LAYER_URL = "https://services-eu1.arcgis.com/RD4JRHAllAtE3ymT/arcgis/rest/services/Subunit_VM_Dataset/FeatureServer/0"

polygon_layer = FeatureLayer(POLYGON_LAYER_URL)
point_layer = FeatureLayer(POINT_LAYER_URL)

@app.route('/export_points')
def export_points():
    polygon_id = request.args.get("polygon_id")
    if not polygon_id:
        return "Error: polygon_id is required", 400

    try:
        # Get the selected polygon's geometry
        poly_result = polygon_layer.query(where=f"FID = {polygon_id}", return_geometry=True)
        if not poly_result.features:
            return f"No polygon found with FID={polygon_id}", 404

        polygon_geom = poly_result.features[0].geometry

        # Calculate bounding box (envelope)
        x_coords = [pt[0] for ring in polygon_geom['rings'] for pt in ring]
        y_coords = [pt[1] for ring in polygon_geom['rings'] for pt in ring]

        envelope = {
            "xmin": min(x_coords),
            "ymin": min(y_coords),
            "xmax": max(x_coords),
            "ymax": max(y_coords),
            "spatialReference": polygon_geom["spatialReference"]
        }

        print("Using envelope:", envelope)

        # Query points within bounding box
        points_result = point_layer.query(
            geometry=envelope,
            geometry_type="esriGeometryEnvelope",
            spatial_rel="esriSpatialRelIntersects",
            return_geometry=False,
            out_fields="*"
        )

        features = points_result.features
        if not features:
            return "No points found within the polygon extent."

        df = pd.DataFrame([f.attributes for f in features])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            df.to_excel(tmp.name, index=False)
            return send_file(tmp.name, as_attachment=True, download_name="points_export.xlsx")

    except Exception as e:
        return f"An error occurred: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
