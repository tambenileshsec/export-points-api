from flask import Flask, request, Response, render_template_string
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pandas as pd
import io

app = Flask(__name__)

POLYGON_LAYER_URL = "https://services-eu1.arcgis.com/RD4JRHAllAtE3ymT/arcgis/rest/services/Secto_VM_Design_WFL1/FeatureServer/9"
POINT_LAYER_URL = "https://services-eu1.arcgis.com/RD4JRHAllAtE3ymT/arcgis/rest/services/Subunit_VM_Dataset/FeatureServer/0"

USERNAME = "Design_Test"
PASSWORD = "Secto@123"

gis = GIS("https://www.arcgis.com", USERNAME, PASSWORD)

@app.route("/export_points")
def export_points():
    polygon_id = request.args.get("polygon_id")
    if not polygon_id:
        return "Polygon ID is missing", 400

    # HTML page that triggers download
    download_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Exporting...</title>
        <script>
            setTimeout(function() {{
                window.location.href = "/download_excel?polygon_id={polygon_id}";
            }}, 1000);
            setTimeout(function() {{
                window.close();
            }}, 6000);
        </script>
    </head>
    <body>
        <h3>📥 Preparing your Excel export...</h3>
        <p>Your download will begin shortly.</p>
        <p>This window will close automatically.</p>
    </body>
    </html>
    """
    return render_template_string(download_page)

@app.route("/download_excel")
def download_excel():
    polygon_id = request.args.get("polygon_id")

    poly_layer = FeatureLayer(POLYGON_LAYER_URL, gis=gis)
    poly_result = poly_layer.query(where=f"OBJECTID = {polygon_id}", return_geometry=True)

    if not poly_result.features:
        return "Polygon not found", 404

    geom = poly_result.features[0].geometry

    point_layer = FeatureLayer(POINT_LAYER_URL, gis=gis)
    points_result = point_layer.query(geometry=geom, spatial_relationship="esriSpatialRelIntersects", return_all_records=True)

    records = [f.attributes for f in points_result.features]
    df = pd.DataFrame(records)

    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=exported_points.xlsx"}
    )

if __name__ == "__main__":
    app.run(debug=True)
