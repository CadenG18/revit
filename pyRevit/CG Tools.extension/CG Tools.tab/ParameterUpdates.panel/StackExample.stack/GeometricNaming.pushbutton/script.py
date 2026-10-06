# -*- coding: utf-8 -*-
__title__ = "Coordinate Naming"
__author__ = "Caden Gabel"
__doc__ = "Lets user rename elements from left to right or top to bottom numerically with a user defined prefix and numbering method."

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import ObjectType
from pyrevit import revit, forms

doc = revit.doc
uidoc = revit.uidoc

# --- STEP 1: Select Elements ---
selection = uidoc.Selection
picked_refs = selection.PickObjects(ObjectType.Element, "Select elements to rename")
elements = [doc.GetElement(r.ElementId) for r in picked_refs]

if not elements:
    forms.alert("No elements selected.", exitscript=True)


# --- STEP 2: Collect Available Editable String Parameters ---
param_names = set()
for elem in elements:
    for param in elem.Parameters:
        if param.StorageType == StorageType.String and not param.IsReadOnly:
            param_names.add(param.Definition.Name)

if not param_names:
    forms.alert("No editable text parameters found on selected elements.", exitscript=True)

param_names = sorted(list(param_names))


# --- STEP 3: Let User Pick Parameter ---
param_name = forms.SelectFromList.show(
    param_names,
    multiselect=False,
    title="Select Parameter to Rename",
    button_name="Select Parameter"
)

if not param_name:
    forms.alert("No parameter selected.", exitscript=True)


# --- STEP 4: Choose Rename Order ---
order_choice = forms.CommandSwitchWindow.show(
    ["Left to Right", "Top to Bottom"],
    message="Choose renaming order:"
)
if not order_choice:
    forms.alert("No order selected.", exitscript=True)


# --- STEP 5: Ask for Prefix ---
prefix = forms.ask_for_string(
    default="GENERATOR-",
    prompt="Enter the prefix for naming (e.g., 'GENERATOR-'):",
    title="Name Prefix"
)
if prefix is None:
    forms.alert("No prefix entered.", exitscript=True)


# --- STEP 6: Ask for Number Range ---
start_num = forms.ask_for_string(
    default="101",
    prompt="Enter starting number (e.g., 101):",
    title="Start Number"
)
end_num = forms.ask_for_string(
    default="108",
    prompt="Enter ending number (e.g., 108):",
    title="End Number"
)

try:
    start_num = int(start_num)
    end_num = int(end_num)
except:
    forms.alert("Invalid number input. Must be integers.", exitscript=True)


# --- STEP 7: Ask for Number Padding ---
pad_digits = forms.ask_for_string(
    default="0",
    prompt="Enter number of digits for numbering (e.g., 2 for 01, 3 for 001). Enter 0 for none:",
    title="Number Padding"
)

try:
    pad_digits = int(pad_digits)
    if pad_digits < 0:
        pad_digits = 0
except:
    pad_digits = 0


# --- STEP 8: Sort Elements by Chosen Order ---
def get_xyz(elem):
    loc = elem.Location
    if hasattr(loc, "Point") and loc.Point:
        return loc.Point
    elif hasattr(loc, "Curve") and loc.Curve:
        return loc.Curve.Evaluate(0.5, True)
    else:
        return XYZ(0, 0, 0)

if order_choice == "Left to Right":
    elements.sort(key=lambda e: get_xyz(e).X)
else:
    elements.sort(key=lambda e: get_xyz(e).Y, reverse=True)  # Top to bottom


# --- STEP 9: Apply Renaming ---
t = Transaction(doc, "Rename Elements by Position")
t.Start()

counter = start_num
for elem in elements:
    param = elem.LookupParameter(param_name)
    if param and not param.IsReadOnly:
        if pad_digits > 0:
            num_str = str(counter).zfill(pad_digits)
        else:
            num_str = str(counter)
        new_value = "{}{}".format(prefix, num_str)
        param.Set(new_value)
        counter += 1
    else:
        print("Skipped element {} — parameter not found or read-only.".format(elem.Id))

t.Commit()


# --- STEP 10: Report ---
forms.alert(
    "Renamed {} elements using parameter '{}'\n\nFrom {}{} to {}{}.".format(
        len(elements),
        param_name,
        prefix,
        str(start_num).zfill(pad_digits) if pad_digits > 0 else start_num,
        prefix,
        str(min(end_num, start_num + len(elements) - 1)).zfill(pad_digits) if pad_digits > 0 else min(end_num, start_num + len(elements) - 1)
    ),
    title="Renaming Complete"
)
