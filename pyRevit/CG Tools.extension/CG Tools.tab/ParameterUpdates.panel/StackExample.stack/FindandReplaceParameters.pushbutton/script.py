# -*- coding: utf-8 -*-
__title__ = "Find & Replace Parameter Text"
__author__ = "Caden Gabel"
__doc__ = "Finds and replaces text within a selected text parameter for selected elements."

from Autodesk.Revit.DB import Transaction
from pyrevit import revit, forms, script

# --- Collect selected elements ---
uidoc = revit.uidoc
doc = revit.doc
selection = [doc.GetElement(elId) for elId in uidoc.Selection.GetElementIds()]

if not selection:
    forms.alert("Please select one or more elements before running the script.", title="No Selection")
    script.exit()

# --- Collect all unique text parameter names from selection ---
text_param_names = set()
for el in selection:
    for param in el.Parameters:
        try:
            if param.StorageType.ToString() == "String":
                text_param_names.add(param.Definition.Name)
        except:
            pass

if not text_param_names:
    forms.alert("No text-type parameters found in the selected elements.", title="No Text Parameters")
    script.exit()

# --- Ask user to choose parameter from dropdown ---
param_name = forms.SelectFromList.show(
    sorted(list(text_param_names)),
    title="Select a Text Parameter",
    button_name="Select Parameter"
)

if not param_name:
    script.exit()

# --- Ask for find and replace strings ---
find_text = forms.ask_for_string(prompt="Find text:")
if find_text is None:
    script.exit()

replace_text = forms.ask_for_string(prompt="Replace with:")
if replace_text is None:
    script.exit()

# --- Perform find/replace ---
count = 0
with Transaction(doc, "Find and Replace Parameter Text") as t:
    t.Start()
    for el in selection:
        param = el.LookupParameter(param_name)
        if param and param.StorageType.ToString() == "String":
            current_value = param.AsString() or ""
            if find_text in current_value:
                new_value = current_value.replace(find_text, replace_text)
                param.Set(new_value)
                count += 1
    t.Commit()

forms.alert("Updated {} element(s).".format(count), title="Find & Replace Complete")
