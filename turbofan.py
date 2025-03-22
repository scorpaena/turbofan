import os
from enum import Enum
import tempfile
from datetime import datetime

import cadquery as cq
import streamlit as st
import pyvista as pv
from stpyvista import stpyvista as stv
from cquav.turbofan import AirfoilSection, Turbofan, get_refined_airfoils_collection


TOLERANCE = 0.1
REFINED_AIRFOILS_COLLECTION = get_refined_airfoils_collection()


class Tessellation(Enum):
    COARSE = 1e-3
    MEDIUM = 1e-4
    FINE = 1e-5


def generate_temp_file(model, file_format, tessellation):
    """Generates a temporary file with the specified STL or STEP format."""
    if file_format.lower() == "stl":
        file_suffix = ".stl"
        export_type = cq.exporters.ExportTypes.STL

    elif file_format.lower() == "step":
        file_suffix = ".step"
        export_type = cq.exporters.ExportTypes.STEP
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmpfile:
        cq.exporters.export(model, tmpfile.name, exportType=export_type, tolerance=getattr(Tessellation, tessellation.upper()).value)
        return tmpfile.name

@st.cache_data
def generate_and_export_turbofan_cached(
    _root_curve,
    _middle_curve,
    _tip_curve,
    root_chord_ratio,
    root_twist,
    middle_chord_ratio,
    middle_offset_distance,
    middle_twist,
    tip_chord_ratio,
    tip_offset_distance,
    tip_twist,
    file_format,
    tessellation,
    vanes_count,
    hub_diameter,
    center_hole_diameter
):
    sections = [
        AirfoilSection(_root_curve, root_chord_ratio, 0, root_twist),
        AirfoilSection(_middle_curve, middle_chord_ratio, middle_offset_distance, middle_twist),
        AirfoilSection(_tip_curve, tip_chord_ratio, middle_offset_distance + tip_offset_distance, tip_twist)
    ]
    turbofan = Turbofan(
        sections=sections,
        vanes_count=vanes_count,
        center_hole_diameter=center_hole_diameter,
        hub_diameter=hub_diameter
    ).build_turbofan()
    return generate_temp_file(turbofan, file_format, tessellation)


# ----------------------- Streamlit UI ----------------------- #

# Streamlit UI for parameter inputs
st.set_page_config(layout='wide')
col1, col2, col3 = st.columns([2, 2, 4])
with col1:
    st.header("Turbofan Model Generator")
    st.subheader("Root airfoil profile selection:")
    family_root = st.selectbox("Choose a profile family:", list(REFINED_AIRFOILS_COLLECTION.keys()), key="root_family")
    root_curve_id = REFINED_AIRFOILS_COLLECTION[family_root]
    st.divider()

    st.subheader("Middle airfoil profile selection:")
    family_middle = st.selectbox("Choose a profile family:", list(REFINED_AIRFOILS_COLLECTION.keys()), key="middle_family")
    middle_curve_id = REFINED_AIRFOILS_COLLECTION[family_middle]
    st.divider()

    st.subheader("Tip airfoil profile selection:")
    family_tip = st.selectbox("Choose a profile family:", list(REFINED_AIRFOILS_COLLECTION.keys()), key="tip_family")
    tip_curve_id = REFINED_AIRFOILS_COLLECTION[family_tip]

with col2:
    tessellation_value = st.select_slider('Surface quality', options=[t.name.lower() for t in Tessellation])
    blades_count = st.slider('Blades count (items)', min_value=2, max_value=10, value=2, step=1)
    hub_dia = st.slider('Turbofan hub diameter', min_value=2.0, max_value=5.0, value=2.0, step=0.25)
    center_hole_dia = st.slider('Turbofan center hole diameter', min_value=0.5, max_value=hub_dia-0.5, value=1.0, step=0.25)
    root_twist_angle = st.slider('Root section twist angle (degree)', min_value=-90, max_value=0, value=-20, step=1)
    middle_twist_angle = st.slider('Middle section twist angle (degree)', min_value=-90, max_value=0, value=-12, step=1)
    tip_twist_angle = st.slider('Tip section twist angle (degree)', min_value=-90, max_value=0, value=-3, step=1)

    root_chord = st.slider('Root section chord (ratio)', min_value=0.1, max_value=2.0, value=0.6, step=0.1)
    middle_chord = st.slider('Middle section chord (ratio)', min_value=0.1, max_value=2.0, value=1.0, step=0.1)
    tip_chord = st.slider('Tip section chord (ratio)', min_value=0.1, max_value=2.0, value=0.3, step=0.1)

    middle_offset = st.slider('Middle section offset', min_value=1, max_value=10, value=2, step=1)
    tip_offset = st.slider('Tip section offset', min_value=1, max_value=10, value=3, step=1)


# ----------------------- Visualization ----------------------- #
file_path_stl = generate_and_export_turbofan_cached(
    _root_curve=root_curve_id,
    _middle_curve=middle_curve_id,
    _tip_curve=tip_curve_id,
    root_chord_ratio=root_chord,
    root_twist=root_twist_angle,
    middle_chord_ratio=middle_chord,
    middle_offset_distance=middle_offset,
    middle_twist=middle_twist_angle,
    tip_chord_ratio=tip_chord,
    tip_offset_distance=tip_offset,
    tip_twist=tip_twist_angle,
    file_format="stl",
    tessellation=tessellation_value,
    vanes_count=blades_count,
    hub_diameter=hub_dia,
    center_hole_diameter=center_hole_dia,
)


file_path_step = generate_and_export_turbofan_cached(
    _root_curve=root_curve_id,
    _middle_curve=middle_curve_id,
    _tip_curve=tip_curve_id,
    root_chord_ratio=root_chord,
    root_twist=root_twist_angle,
    middle_chord_ratio=middle_chord,
    middle_offset_distance=middle_offset,
    middle_twist=middle_twist_angle,
    tip_chord_ratio=tip_chord,
    tip_offset_distance=tip_offset,
    tip_twist=tip_twist_angle,
    file_format="step",
    tessellation=tessellation_value,
    vanes_count=blades_count,
    hub_diameter=hub_dia,
    center_hole_diameter=center_hole_dia,
)

if os.getenv("OS_TYPE") != "windows":
    pv.start_xvfb()

mesh = pv.read(file_path_stl)

plotter = pv.Plotter(window_size=[500, 500])
plotter.add_mesh(mesh)
plotter.view_isometric()
plotter.set_background("#0e1117")

with col3:
    stv(plotter, key=f"turbofan_{datetime.now()}")
    with open(file_path_stl, 'rb') as stl_file:
        st.download_button(
            label="Download STL File",
            data=stl_file,
            file_name="gear.stl",
            mime="application/vnd.ms-pki.stl",
        )
    with open(file_path_step, 'rb') as step_file:
        st.download_button(
            label=f"Download STEP File",
            data=step_file,
            file_name=f"gear.step",
            mime="application/step",
        )
