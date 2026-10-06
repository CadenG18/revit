# -*- coding: utf-8 -*-
__title__ = "Place Squares at Intersections (Pinned, Styled)"
__author__ = "Caden Gabel"
__doc__ = "Places pinned squares at intersection points of selected detail lines, with user-defined width and line style."

from pyrevit import revit, forms
from Autodesk.Revit.DB import Transaction, BuiltInCategory, XYZ, Line, FilteredElementCollector, GraphicsStyle

doc = revit.doc
uidoc = revit.uidoc

TOLERANCE = 0.001  # ft
ENDPOINT_TOL = 1e-6
INCH_TO_FEET = 1.0 / 12.0

SQUARE_OPTIONS = {
    '1/8"': 1/8.0 * INCH_TO_FEET,
    '1/4"': 1/4.0 * INCH_TO_FEET,
    '3/8"': 3/8.0 * INCH_TO_FEET,
    '1/2"': 1/2.0 * INCH_TO_FEET
}


def is_detail_line(elem):
    return (
        elem.Category
        and elem.Category.Id.IntegerValue == int(BuiltInCategory.OST_Lines)
        and hasattr(elem, "GeometryCurve")
    )


def get_line_endpoints(line):
    curve = line.GeometryCurve
    p0 = curve.GetEndPoint(0)
    p1 = curve.GetEndPoint(1)
    z = p0.Z
    return XYZ(p0.X, p0.Y, z), XYZ(p1.X, p1.Y, z)


def segments_intersect(p1, p2, q1, q2, tol=TOLERANCE, endpoint_tol=ENDPOINT_TOL):
    """Return intersection point of two segments (ignores endpoints)."""
    def det(a, b, c, d):
        return a*d - b*c

    x1, y1 = p1.X, p1.Y
    x2, y2 = p2.X, p2.Y
    x3, y3 = q1.X, q1.Y
    x4, y4 = q2.X, q2.Y

    denominator = det(x1 - x2, y1 - y2, x3 - x4, y3 - y4)
    if abs(denominator) < 1e-12:
        return None

    px = det(det(x1, y1, x2, y2), x1 - x2, det(x3, y3, x4, y4), x3 - x4) / denominator
    py = det(det(x1, y1, x2, y2), y1 - y2, det(x3, y3, x4, y4), y3 - y4) / denominator

    if (
        min(x1, x2) - tol <= px <= max(x1, x2) + tol
        and min(y1, y2) - tol <= py <= max(y1, y2) + tol
        and min(x3, x4) - tol <= px <= max(x3, x4) + tol
        and min(y3, y4) - tol <= py <= max(y3, y4) + tol
    ):
        intersection = XYZ(px, py, p1.Z)
        for endpoint in [p1, p2, q1, q2]:
            if intersection.DistanceTo(endpoint) < endpoint_tol:
                return None
        return intersection
    return None


# -------------------- MAIN --------------------

elements = revit.get_selection()
if not elements:
    forms.alert("Please select detail lines before running the script.", exitscript=True)

detail_lines = [e for e in elements if is_detail_line(e)]
if not detail_lines:
    forms.alert("No detail lines found.", exitscript=True)

# User selects square width
square_label = forms.SelectFromList.show(sorted(SQUARE_OPTIONS.keys()), title="Select square width", multiselect=False)
if not square_label:
    forms.alert("No square width selected.", exitscript=True)
square_width = SQUARE_OPTIONS[square_label]

# Get all line styles (GraphicsStyle) that belong to the Lines category
line_styles = [gs for gs in FilteredElementCollector(doc)
               .OfClass(GraphicsStyle)
               if gs.GraphicsStyleCategory.Id.IntegerValue == int(BuiltInCategory.OST_Lines)]

if not line_styles:
    forms.alert("No line styles found in project.", exitscript=True)

# User selects line style
line_style_name = forms.SelectFromList.show(
    [ls.Name for ls in line_styles],
    title="Select line style for squares",
    multiselect=False
)
if not line_style_name:
    forms.alert("No line style selected.", exitscript=True)

# Get the GraphicsStyle object
gs_obj = [ls for ls in line_styles if ls.Name == line_style_name][0]

active_view = doc.ActiveView

t = Transaction(doc, "Place Pinned Styled Squares at Intersections")
t.Start()

intersection_points = []

# Find intersections
for i, line1 in enumerate(detail_lines):
    start1, end1 = get_line_endpoints(line1)
    for j, line2 in enumerate(detail_lines):
        if j <= i:
            continue
        start2, end2 = get_line_endpoints(line2)
        intersect = segments_intersect(start1, end1, start2, end2)
        if intersect:
            intersection_points.append(intersect)

# Place pinned, styled square at each intersection
for pt in intersection_points:
    half = square_width / 2
    p0 = XYZ(pt.X - half, pt.Y - half, pt.Z)
    p1 = XYZ(pt.X + half, pt.Y - half, pt.Z)
    p2 = XYZ(pt.X + half, pt.Y + half, pt.Z)
    p3 = XYZ(pt.X - half, pt.Y + half, pt.Z)

    lines = [
        Line.CreateBound(p0, p1),
        Line.CreateBound(p1, p2),
        Line.CreateBound(p2, p3),
        Line.CreateBound(p3, p0)
    ]
    for l in lines:
        detail_line = doc.Create.NewDetailCurve(active_view, l)
        detail_line.LineStyle = gs_obj
        detail_line.Pinned = True

t.Commit()

forms.alert("Placed {} pinned squares at intersections.".format(len(intersection_points)), title="Complete")
