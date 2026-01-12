from typing import Dict, List, Tuple

STANDARD_RECIPES: Dict[str, Dict[str, Dict[str, str]]] = {
    "etch": {
        "poly_si": {
            "chuck_temp": "60 °C",
            "pressure": "10 mTorr",
            "rf_power": "600 W",
            "bias_power": "120 W",
            "cl2_flow": "80 sccm",
            "hbr_flow": "40 sccm",
            "ar_flow": "100 sccm",
            "time": "45 s",
        },
        "metal": {
            "chuck_temp": "50 °C",
            "pressure": "6 mTorr",
            "rf_power": "450 W",
            "bias_power": "160 W",
            "bcl3_flow": "35 sccm",
            "cl2_flow": "70 sccm",
            "ar_flow": "120 sccm",
            "time": "55 s",
        },
    },
    "deposition": {
        "ild_cvd": {
            "temp": "380 °C",
            "pressure": "3 Torr",
            "precursor": "TEOS",
            "o2_flow": "600 sccm",
            "he_flow": "1000 sccm",
            "rf_power": "250 W",
            "thickness": "800 nm",
        },
        "metal_pvd": {
            "temp": "120 °C",
            "pressure": "4 mTorr",
            "target": "AlCu",
            "ar_flow": "60 sccm",
            "dc_power": "8 kW",
            "thickness": "500 nm",
        },
    },
    "lithography": {
        "contact": {
            "resist": "193i CAR",
            "post_apply_bake": "110 °C / 60 s",
            "exposure_dose": "22 mJ/cm²",
            "focus_offset": "0.00 µm",
            "post_exposure_bake": "95 °C / 60 s",
            "develop": "TMAH 2.38% / 60 s",
        },
        "line_space": {
            "resist": "EUV CAR",
            "post_apply_bake": "120 °C / 60 s",
            "exposure_dose": "27 mJ/cm²",
            "focus_offset": "0.02 µm",
            "post_exposure_bake": "95 °C / 60 s",
            "develop": "TMAH 2.38% / 55 s",
        },
    },
    "cmp": {
        "ild": {
            "head_pressure": "3.0 psi",
            "platen_speed": "60 rpm",
            "slurry_flow": "200 ml/min",
            "backpressure": "0.2 psi",
            "pad_temp": "28 °C",
            "removal_rate": "120 nm/min",
        },
        "copper": {
            "head_pressure": "2.5 psi",
            "platen_speed": "70 rpm",
            "slurry_flow": "180 ml/min",
            "backpressure": "0.25 psi",
            "pad_temp": "30 °C",
            "removal_rate": "150 nm/min",
        },
    },
    "implant": {
        "n_well": {
            "species": "Phosphorus",
            "energy": "60 keV",
            "dose": "2e13 cm^-2",
            "tilt": "7 °",
            "twist": "27 °",
        },
        "p_well": {
            "species": "Boron",
            "energy": "20 keV",
            "dose": "5e12 cm^-2",
            "tilt": "7 °",
            "twist": "27 °",
        },
    },
}

# Allowable windows for selected parameters; (low, high, unit)
PROCESS_WINDOWS: Dict[str, Dict[str, Dict[str, Tuple[float, float, str]]]] = {
    "etch": {
        "poly_si": {
            "pressure": (8, 12, "mTorr"),
            "rf_power": (550, 650, "W"),
            "bias_power": (100, 140, "W"),
        },
        "metal": {
            "pressure": (5, 8, "mTorr"),
            "rf_power": (420, 500, "W"),
            "bias_power": (140, 180, "W"),
        },
    },
    "lithography": {
        "contact": {
            "exposure_dose": (21, 23, "mJ/cm²"),
            "focus_offset": (-0.02, 0.02, "µm"),
        },
        "line_space": {
            "exposure_dose": (26, 28, "mJ/cm²"),
            "focus_offset": (-0.015, 0.035, "µm"),
        },
    },
    "cmp": {
        "copper": {
            "head_pressure": (2.2, 2.8, "psi"),
            "platen_speed": (60, 80, "rpm"),
            "slurry_flow": (160, 200, "ml/min"),
        }
    },
}

