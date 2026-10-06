# -*- coding: utf-8 -*-
__title__ = "Filter Based on Parameter Value"
__author__ = "Caden Gabel"
__doc__ = "Selects elements in current view based on parameter matching or containing a certain value."

from pyrevit import revit, DB, forms
from System.Collections.Generic import List

doc = revit.doc
uidoc = revit.uidoc

# -----------------------------
# User Inputs
# -----------------------------

category_scope = forms.CommandSwitchWindow.show(
    ["3D Model Elements", "Detail/Annotation Elements (Drafting Views)"],
    message="Choose what type of elements to search:"
)
if not category_scope:
    forms.alert("Cancelled.")
    import sys; sys.exit()

param_name = forms.ask_for_string(
    prompt="Enter the parameter name to search by:",
    default="Type Mark"
)
if not param_name:
    import sys; sys.exit()

match_mode = forms.CommandSwitchWindow.show(
    ["Equals", "Contains"],
    message="Choose match type:"
)
if not match_mode:
    import sys; sys.exit()

search_value = forms.ask_for_string(
    prompt="Enter the value to match:",
    default=""
)
if not search_value:
    import sys; sys.exit()

search_value = search_value.strip().lower()

# -----------------------------
# Category Setup
# -----------------------------

def get_safe_categories(cat_names):
    cats = []
    for name in cat_names:
        if hasattr(DB.BuiltInCategory, name):
            cats.append(getattr(DB.BuiltInCategory, name))
    return cats

detail_category_names = [
    "OST_DetailComponents",
    "OST_Lines",
    "OST_TextNotes",
    "OST_FilledRegion",
    "OST_GenericAnnotation",
    "OST_DetailGroups",
    "OST_Symbols",
    "OST_InsulationLines"
]

detail_categories = get_safe_categories(detail_category_names)

# -----------------------------
# Collect Elements (Current View only)
# -----------------------------

if category_scope == "3D Model Elements":
    collector = DB.FilteredElementCollector(doc, doc.ActiveView.Id)
    elements = list(collector.WhereElementIsNotElementType().ToElements())
    elements.extend(list(DB.FilteredElementCollector(doc).WhereElementIsElementType().ToElements()))
else:
    elements = []
    for cat in detail_categories:
        try:
            view_collector = DB.FilteredElementCollector(doc, doc.ActiveView.Id)
            elems = view_collector.OfCategory(cat).WhereElementIsNotElementType().ToElements()
            elements.extend(list(elems))
        except Exception:
            pass

# -----------------------------
# Filter by Parameter
# -----------------------------

matched_elements = []

for el in elements:
    param = el.LookupParameter(param_name)
    val = None
    if param:
        try:
            val = param.AsString() or param.AsValueString()
        except:
            val = None

    if not val:
        try:
            symbol = doc.GetElement(el.GetTypeId())
            if symbol:
                param = symbol.LookupParameter(param_name)
                if param:
                    val = param.AsString() or param.AsValueString()
        except:
            pass

    if not val:
        continue

    val = val.strip().lower()

    if match_mode == "Equals" and val == search_value:
        matched_elements.append(el)
    elif match_mode == "Contains" and search_value in val:
        matched_elements.append(el)

# -----------------------------
# Handle Results
# -----------------------------

if not matched_elements:
    forms.alert("No elements found with that parameter value.", title="No Matches")
    import sys; sys.exit()

# -----------------------------
# Build Checklist Data — show category + parameter value (no ID)
# -----------------------------

checklist_data = []
element_display_map = {}

for el in matched_elements:
    cat = el.Category.Name if el.Category else "No Category"

    param_val = ""
    param = el.LookupParameter(param_name)
    if param:
        try:
            param_val = param.AsString() or param.AsValueString() or ""
        except:
            param_val = ""

    if not param_val:
        try:
            symbol = doc.GetElement(el.GetTypeId())
            if symbol:
                p2 = symbol.LookupParameter(param_name)
                if p2:
                    param_val = p2.AsString() or p2.AsValueString() or ""
        except:
            pass

    param_val = param_val.strip() if param_val else "(no value)"

    display_str = "{} | {}: {}".format(cat, param_name, param_val)
    checklist_data.append(display_str)

    # support duplicates — group multiple elements under same display label
    if display_str not in element_display_map:
        element_display_map[display_str] = []
    element_display_map[display_str].append(el)

# -----------------------------
# Show Checklist Window
# -----------------------------

selected_items = forms.SelectFromList.show(
    checklist_data,
    title="Select Elements to Keep",
    multiselect=True,
    button_name="Finalize Selection"
)

if not selected_items:
    import sys; sys.exit()

# Map selected strings back to all elements with that label
final_selection_ids = []
for display_str in selected_items:
    for el in element_display_map.get(display_str, []):
        final_selection_ids.append(el.Id)

# -----------------------------
# Set Final Selection (quietly)
# -----------------------------
uidoc.Selection.SetElementIds(List[DB.ElementId](final_selection_ids))
