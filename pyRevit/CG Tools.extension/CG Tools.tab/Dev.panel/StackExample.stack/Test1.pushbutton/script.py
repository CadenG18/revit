# -*- coding: utf-8 -*-
__title__ = "Combine Text Parameters"
__author__ = "Caden Gabel"
__doc__ = "Combines multiple editable text parameters into a writable text parameter using a dash separator."

from pyrevit import revit, forms
from Autodesk.Revit.DB import Transaction, StorageType

doc = revit.doc


def get_editable_text_param_names(element):
    """Return editable text parameter names (instance + type)."""
    names = set()

    # Instance parameters
    for p in element.Parameters:
        if (
            not p.IsReadOnly
            and p.Definition
            and p.StorageType == StorageType.String
        ):
            names.add(p.Definition.Name)

    # Type parameters
    type_elem = doc.GetElement(element.GetTypeId())
    if type_elem:
        for p in type_elem.Parameters:
            if (
                not p.IsReadOnly
                and p.Definition
                and p.StorageType == StorageType.String
            ):
                names.add(p.Definition.Name)

    return names


def get_writable_instance_text_param_names(element):
    """Return writable instance-only text parameter names."""
    names = set()
    for p in element.Parameters:
        if (
            not p.IsReadOnly
            and p.Definition
            and p.StorageType == StorageType.String
        ):
            names.add(p.Definition.Name)
    return names


def get_param_value(element, param_name):
    """Return text parameter value (instance first, then type)."""
    param = element.LookupParameter(param_name)

    if not param:
        type_elem = doc.GetElement(element.GetTypeId())
        if type_elem:
            param = type_elem.LookupParameter(param_name)

    if not param or not param.HasValue:
        return ""

    return param.AsString() or ""


def filter_params_with_any_value(elements, param_names):
    """Return parameter names that have at least one non-empty value."""
    valid_params = set()

    for name in param_names:
        for elem in elements:
            if get_param_value(elem, name):
                valid_params.add(name)
                break

    return sorted(valid_params)


def set_param_value(element, param_name, value):
    """Set value on writable instance text parameter."""
    param = element.LookupParameter(param_name)
    if (
        param
        and not param.IsReadOnly
        and param.StorageType == StorageType.String
    ):
        param.Set(value)
        return True
    return False


# -------------------- MAIN --------------------

elements = revit.get_selection()
if not elements:
    forms.alert("Please select elements before running the script.", exitscript=True)

# Build candidate parameter lists from first element
source_candidates = get_editable_text_param_names(elements[0])
target_candidates = get_writable_instance_text_param_names(elements[0])

# Filter out parameters that are empty across all selected elements
source_param_names = filter_params_with_any_value(elements, source_candidates)
target_param_names = filter_params_with_any_value(elements, target_candidates)

if not source_param_names:
    forms.alert("No text parameters with values found on selected elements.", exitscript=True)

if not target_param_names:
    forms.alert("No writable instance text parameters with values found.", exitscript=True)

# Ask for number of parameters to combine
param_count_str = forms.ask_for_string(
    prompt="Enter number of parameters to combine:",
    default="2",
    title="Parameter Count"
)

if not param_count_str or not param_count_str.isdigit():
    forms.alert("Invalid number entered.", exitscript=True)

param_count = int(param_count_str)
if param_count < 1:
    forms.alert("Must combine at least one parameter.", exitscript=True)

# Select source parameters in order
source_params = []
for i in range(param_count):
    selected = forms.SelectFromList.show(
        source_param_names,
        title="Select Source Text Parameter {0} of {1}".format(i + 1, param_count),
        multiselect=False
    )

    if not selected:
        forms.alert("Parameter selection cancelled.", exitscript=True)

    source_params.append(selected)

# Select target parameter
target_param = forms.SelectFromList.show(
    target_param_names,
    title="Select Target Text Parameter",
    multiselect=False
)

if not target_param:
    forms.alert("No target parameter selected.", exitscript=True)

separator = "-" if param_count > 1 else ""

t = Transaction(doc, "Combine Text Parameters")
t.Start()

updated_count = 0

for elem in elements:
    values = []

    for p in source_params:
        val = get_param_value(elem, p)
        if val:
            values.append(val)

    if not values:
        continue

    combined_value = separator.join(values)

    if set_param_value(elem, target_param, combined_value):
        updated_count += 1

t.Commit()

forms.alert(
    "Updated {0} element(s).\n\nTarget Parameter:\n{1}\n\nSource Parameters:\n{2}".format(
        updated_count,
        target_param,
        ", ".join(source_params)
    ),
    title="Complete"
)
