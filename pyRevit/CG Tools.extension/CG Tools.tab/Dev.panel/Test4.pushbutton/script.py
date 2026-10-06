# -*- coding: utf-8 -*-
__title__ = "Apply View Template Properties to Floor Plans"
__author__ = "Caden Gabel"
__doc__ = "Apply selected view template *properties* to all Floor Plan views without changing the view's assigned template."

from pyrevit import revit, forms
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewType
)

doc = revit.doc

# ------------------------------------------------------------
# Collect all view templates
# ------------------------------------------------------------
templates = [
    v for v in FilteredElementCollector(doc)
    .OfClass(View)
    if v.IsTemplate
]

if not templates:
    forms.alert("No view templates found in this model.", exitscript=True)

# ------------------------------------------------------------
# User selects a template
# ------------------------------------------------------------
template = forms.SelectFromList.show(
    templates,
    name_attr="Name",
    title="Select View Template to APPLY (properties only)",
    multiselect=False
)

if not template:
    forms.alert("No template selected.", exitscript=True)

# ------------------------------------------------------------
# Collect all Floor Plan views (non-templates)
# ------------------------------------------------------------
floor_plans = [
    v for v in FilteredElementCollector(doc)
    .OfClass(View)
    if not v.IsTemplate and v.ViewType == ViewType.FloorPlan
]

if not floor_plans:
    forms.alert("No Floor Plan views found.", exitscript=True)

# ------------------------------------------------------------
# Apply template parameters
# ------------------------------------------------------------
with revit.Transaction("Apply View Template Properties to Floor Plans"):
    for view in floor_plans:
        # This copies template settings WITHOUT assigning the template
        view.ApplyViewTemplateParameters(template)

forms.alert(
    "Applied template properties from:\n\n"
    "'{}'\n\n"
    "to {} Floor Plan views.".format(template.Name, len(floor_plans))
)
