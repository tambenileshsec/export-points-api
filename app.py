from flask import Flask, request, send_file, redirect, url_for
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

@app.route("/export_points")
def export_points():
    polygon_id = request.args.get("polygon_id")
    if not polygon_id:
        return "Error: polygon_id is required", 400

    try:
        # Get polygon geometry and attributes
        poly_result = polygon_layer.query(where=f"FID = {polygon_id}", return_geometry=True, out_fields='*')
        if not poly_result.features:
            return f"No polygon found with FID={polygon_id}", 404

        polygon_feature = poly_result.features[0]
        polygon_geom = polygon_feature.geometry
        polygon_attrs = polygon_feature.attributes

        # Get kmduid from polygon attributes
        kmduid = polygon_attrs.get("kmduid", "Unknown")

        # Create bounding box manually (for envelope geometry type)
        x_coords = [pt[0] for ring in polygon_geom['rings'] for pt in ring]
        y_coords = [pt[1] for ring in polygon_geom['rings'] for pt in ring]

        envelope = {
            "xmin": min(x_coords),
            "ymin": min(y_coords),
            "xmax": max(x_coords),
            "ymax": max(y_coords),
            "spatialReference": polygon_geom["spatialReference"]
        }

        # Query points within polygon envelope
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

        # Generate filename from polygon kmduid
        filename = f"{kmduid}_Address.xlsx"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            df.to_excel(tmp.name, index=False)

        # Store filename to use during download
        return redirect(url_for("download_file", filename=os.path.basename(tmp.name), download_name=filename))

    except Exception as e:
        return f"An error occurred: {e}", 500

@app.route("/download/<filename>")
def download_file(filename):
    filepath = os.path.join(tempfile.gettempdir(), filename)
    download_name = request.args.get("download_name", "Unknown_Address.xlsx")
    return send_file(filepath, as_attachment=True, download_name=download_name)

if __name__ == "__main__":
    app.run(debug=True)
