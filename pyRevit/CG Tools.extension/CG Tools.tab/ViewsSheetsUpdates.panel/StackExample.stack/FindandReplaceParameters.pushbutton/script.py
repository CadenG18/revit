# -*- coding: utf-8 -*-
__title__  = "Select Titleblocks on Floor Plan Sheets"
__author__ = "Caden Gabel"
__doc__ = (
    "Selects titleblocks on sheets that contain Floor Plan views. "
    "Optionally filters sheets by a user-defined text value."
)

from pyrevit import revit, forms
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewSheet,
    Viewport,
    ViewType,
    BuiltInCategory
)

doc = revit.doc

# ------------------------------------------------------------
# Ask user how to filter
# ------------------------------------------------------------
options = [
    "Select ALL sheets with floor plans",
    "Filter sheets with floor plans by text value"
]

choice = forms.CommandSwitchWindow.show(
    options,
    message="How would you like to select sheets?"
)

if not choice:
    forms.alert("No option selected.", exitscript=True)

filter_text = None
if choice == options[1]:
    filter_text = forms.ask_for_string(
        prompt="Enter text to filter Sheet Number or Sheet Name:",
        title="Sheet Filter"
    )

    if not filter_text:
        forms.alert("No filter text provided.", exitscript=True)

    filter_text = filter_text.lower()

# ------------------------------------------------------------
# Collect all sheets
# ------------------------------------------------------------
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()

titleblocks = []

# ------------------------------------------------------------
# Find titleblocks on sheets with Floor Plans
# ------------------------------------------------------------
for sheet in sheets:
    viewports = FilteredElementCollector(doc, sheet.Id) \
        .OfClass(Viewport) \
        .ToElements()

    has_floor_plan = False

    for vp in viewports:
        view = doc.GetElement(vp.ViewId)
        if view and view.ViewType == ViewType.FloorPlan:
            has_floor_plan = True
            break

    if not has_floor_plan:
        continue

    # Optional name/number filter
    if filter_text:
        if (
            filter_text not in sheet.SheetNumber.lower()
            and filter_text not in sheet.Name.lower()
        ):
            continue

    # Collect titleblocks placed on the sheet
    tblocks = (
        FilteredElementCollector(doc, sheet.Id)
        .OfCategory(BuiltInCategory.OST_TitleBlocks)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    titleblocks.extend(tblocks)

# ------------------------------------------------------------
# Select titleblocks in Revit
# ------------------------------------------------------------
if not titleblocks:
    forms.alert("No titleblocks found matching criteria.", exitscript=True)

revit.get_selection().set_to(titleblocks)

forms.alert(
    "Selected {} titleblock(s) on Floor Plan sheets.".format(len(titleblocks))
)
