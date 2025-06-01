# HoseInfoMaster-NX
Automate pipe measurements in NX: Centerlines | Diameters | Lengths

# NX TubeMetrics 🛠️

[![NX Version](https://img.shields.io/badge/NX-2027%20|%202306-blue)](https://www.plm.automation.siemens.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange)](https://github.com/yourusername/NX-TubeMetrics)

Python-powered automation for hose/tube/pipe measurements in Siemens NX.

Features ✨
- *One-click centerlines* using Virtual Curve Centerline
- *Smart diameter detection* (OD/ID with deformation handling)
- *Auto-length annotation* on curves
- *NX Journal-ready* implementation


# Sample workflow
component = selection.get_selected_component()
centerline = create_virtual_curve(component)
annotate_length(centerline)
diameter = measure_diameter(edge, measurement_type='OD')

# Installation 📥
Copy the .py file to your NX journal or execute it directly on the journal "play"

# Supported Versions
NX Version	Tested
2027	✅ Yes
2306	✅ Yes
Other	⚠️ Maybe

# How It Works:
1- Select hose/tube component
2- Run script → Auto-generates centerline
3- Select edge → Returns OD/ID measurement
4- Annotations appear on model

# Development 🧑‍💻
diff
- Current Limitations:
+ Only works with simple cylindrical tubes
+ Needs more error handling
+ Not on loop

# Contact 📧
For questions/suggestions:
argendiaz1108@gmail.com

License 📜
MIT © 2024 [Argentina Diaz Alvarado] - See LICENSE for details.
