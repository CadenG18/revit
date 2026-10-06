# -*- coding: utf-8 -*-
__title__  = "Toggle Grid Bubbles (Orientation Aware)"
__author__ = "Caden Gabel"
__doc__ = (
    "Turns grid bubbles on/off in selected Floor Plan views with orientation detection. "
    "Vertical grids use Top/Bottom logic; Horizontal grids use Left/Right logic."
)

from pyrevit import revit, forms
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Grid,
    View,
    ViewType,
    DatumEnds
)

doc = revit.doc

# ------------------------------------------------------------
# Helper: Determine grid orientation in view
# ------------------------------------------------------------
def get_grid_orientation(grid):
    curve = grid.Curve
    if not curve:
        return None

    direction = curve.Direction.Normalize()
    dx = abs(direction.X)
    dy = abs(direction.Y)

    if dx > dy:
        return "Horizontal"
    elif dy > dx:
        return "Vertical"
    return None

# ------------------------------------------------------------
# Step 1: Bubble behavior
# ------------------------------------------------------------
bubble_options = [
    "Bottom ON / Top OFF",
    "Left OFF / Right ON",
    "Both (Bottom+Right ON, Top+Left OFF)"
]

bubble_choice = forms.CommandSwitchWindow.show(
    bubble_options,
    message="Select grid bubble behavior:"
)

if not bubble_choice:
    forms.alert("No bubble option selected.", exitscript=True)

# ------------------------------------------------------------
# Step 2: View scope
# ------------------------------------------------------------
view_scope_options = [
    "Active View",
    "Select Multiple Floor Plans",
    "All Floor Plans"
]

view_scope = forms.CommandSwitchWindow.show(
    view_scope_options,
    message="Apply grid changes to which views?"
)

if not view_scope:
    forms.alert("No view scope selected.", exitscript=True)

# ------------------------------------------------------------
# Collect Floor Plan views only (exclude drafting)
# ------------------------------------------------------------
floor_plan_views = [
    v for v in FilteredElementCollector(doc)
    .OfClass(View)
    if (
        not v.IsTemplate
        and v.ViewType == ViewType.FloorPlan
    )
]

if not floor_plan_views:
    forms.alert("No Floor Plan views found in the model.", exitscript=True)

# ------------------------------------------------------------
# Determine views to process
# ------------------------------------------------------------
views = []

if view_scope == view_scope_options[0]:
    if doc.ActiveView.ViewType != ViewType.FloorPlan:
        forms.alert("Active view is not a Floor Plan.", exitscript=True)
    views = [doc.ActiveView]

elif view_scope == view_scope_options[1]:
    views = forms.SelectFromList.show(
        floor_plan_views,
        name_attr="Name",
        title="Select Floor Plan Views",
        multiselect=True
    )

    if not views:
        forms.alert("No Floor Plan views selected.", exitscript=True)

elif view_scope == view_scope_options[2]:
    views = floor_plan_views

# ------------------------------------------------------------
# Apply grid bubble logic
# ------------------------------------------------------------
with revit.Transaction("Toggle Grid Bubbles (Floor Plans Only)"):
    for view in views:
        grids = (
            FilteredElementCollector(doc, view.Id)
            .OfClass(Grid)
            .ToElements()
        )

        for grid in grids:
            orientation = get_grid_orientation(grid)
            if not orientation:
                continue

            # Vertical grids → Top / Bottom
            if orientation == "Vertical" and bubble_choice in (bubble_options[0], bubble_options[2]):
                if grid.IsBubbleVisibleInView(DatumEnds.End0, view):
                    grid.HideBubbleInView(DatumEnds.End0, view)

                if not grid.IsBubbleVisibleInView(DatumEnds.End1, view):
                    grid.ShowBubbleInView(DatumEnds.End1, view)

            # Horizontal grids → Left / Right
            if orientation == "Horizontal" and bubble_choice in (bubble_options[1], bubble_options[2]):
                if grid.IsBubbleVisibleInView(DatumEnds.End0, view):
                    grid.HideBubbleInView(DatumEnds.End0, view)

                if not grid.IsBubbleVisibleInView(DatumEnds.End1, view):
                    grid.ShowBubbleInView(DatumEnds.End1, view)

forms.alert(
    "Grid bubbles updated in {} Floor Plan view(s).".format(len(views))
)
