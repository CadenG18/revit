# -*- coding: utf-8 -*-
__title__ = "Open Panel Schedule"
__author__ = "ChatGPT"

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
)
from pyrevit import revit, forms

doc = revit.doc
uidoc = revit.uidoc

# -----------------------------
# Get selected element
# -----------------------------
sel_ids = uidoc.Selection.GetElementIds()
if not sel_ids:
    forms.alert("Please select a circuited electrical fixture.", exitscript=True)

elem = doc.GetElement(list(sel_ids)[0])

# -----------------------------
# Get MEP model
# -----------------------------
mep = getattr(elem, "MEPModel", None)
if not mep:
    forms.alert("Selected element has no MEP model.", exitscript=True)

# -----------------------------
# Get electrical systems
# -----------------------------
systems = mep.GetElectricalSystems()
if not systems or systems.Count == 0:
    forms.alert("Selected element is not circuited.", exitscript=True)

circuit = list(systems)[0]

# -----------------------------
# Get panelboard
# -----------------------------
panel = circuit.BaseEquipment
if not panel:
    forms.alert("Circuit is not assigned to a panel.", exitscript=True)

# -----------------------------
# Get Panel Schedule Name (VERSION-SAFE)
# -----------------------------
param = panel.LookupParameter("Panel Schedule Name")

if not param:
    forms.alert(
        "Panel does not have a 'Panel Schedule Name' parameter:\n{}".format(panel.Name),
        exitscript=True
    )

panel_schedule_name = param.AsString()

if not panel_schedule_name:
    forms.alert(
        "Panel Schedule Name is empty for panel:\n{}".format(panel.Name),
        exitscript=True
    )

# -----------------------------
# Find panel schedule view by name
# -----------------------------
panel_schedule_view = None

for view in FilteredElementCollector(doc).OfClass(View):
    if view.Name == panel_schedule_name:
        panel_schedule_view = view
        break

if not panel_schedule_view:
    forms.alert(
        "Panel Schedule view not found:\n{}".format(panel_schedule_name),
        exitscript=True
    )

# -----------------------------
# Open panel schedule
# -----------------------------
uidoc.ActiveView = panel_schedule_view
