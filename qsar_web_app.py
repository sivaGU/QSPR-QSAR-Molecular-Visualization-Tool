import streamlit as st
import os
from pathlib import Path
import base64
import subprocess
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Page configuration
st.set_page_config(
    page_title="QSPR/QSAR Molecular Visualization Tool",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    body {
        background: #f4f6fa;
    }
    .main-header {
        font-size: 2.8rem;
        font-weight: 900;
        color: #2563eb;
        text-align: center;
        margin-bottom: 0.2rem;
        letter-spacing: -1px;
    }
    .sub-header {
        font-size: 1.25rem;
        color: #4b5563;
        text-align: center;
        margin-bottom: 2.5rem;
        font-weight: 400;
    }
    .receptor-card {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        padding: 2.2rem 2rem 2rem 2rem;
        border-radius: 18px;
        color: white;
        text-align: center;
        box-shadow: 0 6px 24px rgba(239,68,68,0.08);
        margin-bottom: 1.5rem;
    }
    .receptor-card-beta {
        background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%);
        padding: 2.2rem 2rem 2rem 2rem;
        border-radius: 18px;
        color: white;
        text-align: center;
        box-shadow: 0 6px 24px rgba(20,184,166,0.08);
        margin-bottom: 1.5rem;
    }
    .info-block {
        background: rgba(255, 255, 255, 0.18);
        padding: 1.1rem 1.5rem;
        border-radius: 12px;
        margin: 1.2rem 0.5rem 1.2rem 0;
        display: inline-block;
        font-size: 1.1rem;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .stButton > button {
        background: linear-gradient(90deg, #2563eb 0%, #1e40af 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.7rem 2.2rem;
        font-weight: bold;
        font-size: 1.1rem;
        margin-top: 0.7rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 2px 8px rgba(37,99,235,0.08);
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #1e40af 0%, #2563eb 100%);
        transform: translateY(-2px) scale(1.04);
    }
    .viewer-container {
        border: 2px solid #e5e7eb;
        border-radius: 16px;
        padding: 18px 18px 0 18px;
        margin: 32px 0 24px 0;
        background: #f9fafb;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }
    .ngl-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    .stSelectbox > div {
        font-size: 1.1rem;
        font-weight: 500;
    }
    .stSidebar {
        background: #f1f5f9 !important;
    }
    .stSidebar [data-testid="stSidebarNav"] {
        margin-top: 2rem;
    }
    .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar h4 {
        color: #2563eb !important;
    }
    .st-expanderHeader {
        font-size: 1.1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def get_ligand_list(folder_name):
    folder_path = Path(folder_name)
    if not folder_path.exists():
        return []
    ligands = []
    
    # Handle different file naming patterns
    if "T50" in folder_name:
        # T50 files: either *_top_complex.pdb or *_out_complex.pdb
        for file in folder_path.glob("*_complex.pdb"):
            ligand_name = file.stem.replace("_top_complex", "").replace("_out_complex", "")
            ligands.append(ligand_name)
    else:
        # CE files: combined_*_out.pdb
        for file in folder_path.glob("combined_*.pdb"):
            ligand_name = file.stem.replace("combined_", "").replace("_out", "")
            ligands.append(ligand_name)
    
    return sorted(ligands)

def create_ngl_viewer(pdb_content, structure_name):
    pdb_encoded = base64.b64encode(pdb_content.encode()).decode()
    html_code = f"""
    <div class='viewer-container'>
        <div id='ngl-viewer' style='width: 100%; height: 520px; border: 1px solid #ddd; border-radius: 12px;'></div>
    </div>
    <script src='https://unpkg.com/ngl@0.10.4/dist/ngl.js'></script>
    <script>
        var stage = new NGL.Stage("ngl-viewer");
        stage.setParameters({{ backgroundColor: "white" }});
        
        var pdbData = atob("{pdb_encoded}");
        stage.loadFile(new Blob([pdbData], {{type: "chemical/x-pdb"}}), {{ext: "pdb"}}).then(function (component) {{
            // Default representation - let NGL Viewer decide based on PDB content
            component.addRepresentation("cartoon");
            
            // Try different selections for ligands
            component.addRepresentation("ball+stick", {{ sele: "hetero" }});
            component.addRepresentation("ball+stick", {{ sele: "UNL" }});
            component.addRepresentation("ball+stick", {{ sele: "not protein" }});
            
            component.autoView();
        }});
        
        // Prevent page scroll when zooming
        var viewerDiv = document.getElementById("ngl-viewer");
        viewerDiv.addEventListener('wheel', function(event) {{
            event.preventDefault();
        }}, {{ passive: false }});
    </script>
    """
    return html_code

def open_pdb_file(file_path):
    try:
        if sys.platform == "win32":
            os.startfile(str(file_path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(file_path)])
        else:
            subprocess.run(["xdg-open", str(file_path)])
        return True
    except Exception as e:
        st.error(f"Could not open the PDB file. Error: {str(e)}")
        return False

def show_ce_ligand_comparison():
    import pandas as pd
    import plotly.graph_objects as go
    st.markdown("## CE Ligand Comparison: Alpha vs Beta Docking Scores")
    st.markdown("Compare the docking scores for each commonly exposed ligand between ERα and ERβ.")

    # Updated data matching the provided table
    data = [
        {"CASRN": "39239-77-5", "Alpha Docking Score": -9.9, "Beta Docking Score": -9.7, "Difference (Alpha - Beta)": -0.2},
        {"CASRN": "67905-19-5", "Alpha Docking Score": -9.8, "Beta Docking Score": -10.4, "Difference (Alpha - Beta)": 0.6},
        {"CASRN": "4980-53-4", "Alpha Docking Score": -9.8, "Beta Docking Score": -9.3, "Difference (Alpha - Beta)": -0.5},
        {"CASRN": "34395-24-9", "Alpha Docking Score": -9.8, "Beta Docking Score": -10.0, "Difference (Alpha - Beta)": 0.2},
        {"CASRN": "307-55-1", "Alpha Docking Score": -9.7, "Beta Docking Score": -9.2, "Difference (Alpha - Beta)": -0.5},
        {"CASRN": "2144-54-9", "Alpha Docking Score": -9.6, "Beta Docking Score": -9.6, "Difference (Alpha - Beta)": 0.0},
        {"CASRN": "17741-60-5", "Alpha Docking Score": -9.6, "Beta Docking Score": -9.2, "Difference (Alpha - Beta)": -0.4},
        {"CASRN": "60699-51-6", "Alpha Docking Score": -9.5, "Beta Docking Score": -9.9, "Difference (Alpha - Beta)": 0.4},
        {"CASRN": "30046-31-2", "Alpha Docking Score": -9.5, "Beta Docking Score": -9.7, "Difference (Alpha - Beta)": 0.2},
        {"CASRN": "307-35-7", "Alpha Docking Score": -9.4, "Beta Docking Score": -8.6, "Difference (Alpha - Beta)": -0.8},
        {"CASRN": "375-95-1", "Alpha Docking Score": -9.3, "Beta Docking Score": -8.6, "Difference (Alpha - Beta)": -0.7},
        {"CASRN": "335-76-2", "Alpha Docking Score": -9.3, "Beta Docking Score": -9.1, "Difference (Alpha - Beta)": -0.2},
        {"CASRN": "31506-32-8", "Alpha Docking Score": -9.3, "Beta Docking Score": -8.4, "Difference (Alpha - Beta)": -0.9},
        {"CASRN": "865-86-1", "Alpha Docking Score": -9.2, "Beta Docking Score": -9.0, "Difference (Alpha - Beta)": -0.2},
        {"CASRN": "68758-57-6", "Alpha Docking Score": -9.2, "Beta Docking Score": -9.8, "Difference (Alpha - Beta)": 0.6},
        {"CASRN": "507-63-1", "Alpha Docking Score": -9.2, "Beta Docking Score": -8.5, "Difference (Alpha - Beta)": -0.7},
        {"CASRN": "2043-54-1", "Alpha Docking Score": -9.2, "Beta Docking Score": -9.4, "Difference (Alpha - Beta)": 0.2},
        {"CASRN": "4151-50-2", "Alpha Docking Score": -9.1, "Beta Docking Score": -8.4, "Difference (Alpha - Beta)": -0.7},
        {"CASRN": "27619-90-5", "Alpha Docking Score": -9.1, "Beta Docking Score": -8.8, "Difference (Alpha - Beta)": -0.3},
        {"CASRN": "25268-77-3", "Alpha Docking Score": -9.1, "Beta Docking Score": -8.7, "Difference (Alpha - Beta)": -0.4},
        {"CASRN": "68957-62-0", "Alpha Docking Score": -9.0, "Beta Docking Score": -8.2, "Difference (Alpha - Beta)": -0.8},
        {"CASRN": "335-71-7", "Alpha Docking Score": -9.0, "Beta Docking Score": -8.2, "Difference (Alpha - Beta)": -0.8},
        {"CASRN": "27905-45-9", "Alpha Docking Score": -9.0, "Beta Docking Score": -8.4, "Difference (Alpha - Beta)": -0.6},
        {"CASRN": "2043-53-0", "Alpha Docking Score": -9.0, "Beta Docking Score": -8.4, "Difference (Alpha - Beta)": -0.6},
        {"CASRN": "1996-88-9", "Alpha Docking Score": -9.0, "Beta Docking Score": -9.0, "Difference (Alpha - Beta)": 0.0},
        {"CASRN": "376-14-7", "Alpha Docking Score": -8.9, "Beta Docking Score": -8.5, "Difference (Alpha - Beta)": -0.4},
        {"CASRN": "21652-58-4", "Alpha Docking Score": -8.9, "Beta Docking Score": -8.5, "Difference (Alpha - Beta)": -0.4},
        {"CASRN": "678-39-7", "Alpha Docking Score": -8.8, "Beta Docking Score": -8.4, "Difference (Alpha - Beta)": -0.4},
        {"CASRN": "335-67-1", "Alpha Docking Score": -8.8, "Beta Docking Score": -8.2, "Difference (Alpha - Beta)": -0.6},
        {"CASRN": "68555-76-0", "Alpha Docking Score": -8.7, "Beta Docking Score": -8.0, "Difference (Alpha - Beta)": -0.7},
        {"CASRN": "376-27-2", "Alpha Docking Score": -8.7, "Beta Docking Score": -7.7, "Difference (Alpha - Beta)": -1.0},
        {"CASRN": "335-66-0", "Alpha Docking Score": -8.7, "Beta Docking Score": -8.1, "Difference (Alpha - Beta)": -0.6},
        {"CASRN": "6014-75-1", "Alpha Docking Score": -8.6, "Beta Docking Score": -10.1, "Difference (Alpha - Beta)": 1.5},
        {"CASRN": "1691-99-2", "Alpha Docking Score": -8.6, "Beta Docking Score": -8.2, "Difference (Alpha - Beta)": -0.4},
        {"CASRN": "68084-62-8", "Alpha Docking Score": -8.5, "Beta Docking Score": -8.4, "Difference (Alpha - Beta)": -0.1},
        {"CASRN": "16517-11-6", "Alpha Docking Score": -8.5, "Beta Docking Score": -8.2, "Difference (Alpha - Beta)": -0.3},
        {"CASRN": "65104-65-6", "Alpha Docking Score": -8.4, "Beta Docking Score": -8.6, "Difference (Alpha - Beta)": 0.2},
        {"CASRN": "27619-91-6", "Alpha Docking Score": -8.4, "Beta Docking Score": -9.4, "Difference (Alpha - Beta)": 1.0},
        {"CASRN": "65104-67-8", "Alpha Docking Score": -8.3, "Beta Docking Score": -9.4, "Difference (Alpha - Beta)": 1.1},
        {"CASRN": "67584-56-9", "Alpha Docking Score": -8.2, "Beta Docking Score": -7.9, "Difference (Alpha - Beta)": -0.3},
        {"CASRN": "59071-10-2", "Alpha Docking Score": -8.2, "Beta Docking Score": -8.0, "Difference (Alpha - Beta)": -0.2},
        {"CASRN": "68555-75-9", "Alpha Docking Score": -7.9, "Beta Docking Score": -8.0, "Difference (Alpha - Beta)": 0.1},
        {"CASRN": "68958-60-1", "Alpha Docking Score": -7.8, "Beta Docking Score": -7.9, "Difference (Alpha - Beta)": 0.1},
        {"CASRN": "34362-49-7", "Alpha Docking Score": -7.8, "Beta Docking Score": -9.6, "Difference (Alpha - Beta)": 1.8},
        {"CASRN": "65510-55-6", "Alpha Docking Score": -7.6, "Beta Docking Score": -9.6, "Difference (Alpha - Beta)": 2.0},
        {"CASRN": "13252-13-6", "Alpha Docking Score": -7.2, "Beta Docking Score": -8.0, "Difference (Alpha - Beta)": 0.8},
        {"CASRN": "307-24-4", "Alpha Docking Score": -7.1, "Beta Docking Score": -7.6, "Difference (Alpha - Beta)": 0.5},
        {"CASRN": "67584-57-0", "Alpha Docking Score": -6.9, "Beta Docking Score": -8.3, "Difference (Alpha - Beta)": 1.4},
        {"CASRN": "423-82-5", "Alpha Docking Score": -6.9, "Beta Docking Score": -8.3, "Difference (Alpha - Beta)": 1.4},
        {"CASRN": "68958-61-2", "Alpha Docking Score": -6.8, "Beta Docking Score": -7.9, "Difference (Alpha - Beta)": 1.1},
        {"CASRN": "65530-62-3", "Alpha Docking Score": -6.2, "Beta Docking Score": -6.9, "Difference (Alpha - Beta)": 0.7},
        {"CASRN": "82113-65-3", "Alpha Docking Score": -6.1, "Beta Docking Score": -6.7, "Difference (Alpha - Beta)": 0.6},
        {"CASRN": "375-22-4", "Alpha Docking Score": -5.8, "Beta Docking Score": -6.5, "Difference (Alpha - Beta)": 0.7},
        {"CASRN": "65530-61-2", "Alpha Docking Score": -5.3, "Beta Docking Score": -5.6, "Difference (Alpha - Beta)": 0.3},
        {"CASRN": "422-64-0", "Alpha Docking Score": -5.3, "Beta Docking Score": -5.3, "Difference (Alpha - Beta)": 0.0},
        {"CASRN": "118400-71-8", "Alpha Docking Score": -7.7, "Beta Docking Score": -7.6, "Difference (Alpha - Beta)": -0.1},
        {"CASRN": "27619-97-2", "Alpha Docking Score": -8.6, "Beta Docking Score": -8.0, "Difference (Alpha - Beta)": -0.6},
        {"CASRN": "377-73-1", "Alpha Docking Score": -6.5, "Beta Docking Score": -6.5, "Difference (Alpha - Beta)": 0.0},
        {"CASRN": "68140-18-1", "Alpha Docking Score": -4.8, "Beta Docking Score": -5.0, "Difference (Alpha - Beta)": 0.2},
        {"CASRN": "68298-80-6", "Alpha Docking Score": -6.6, "Beta Docking Score": -7.4, "Difference (Alpha - Beta)": 0.8},
        {"CASRN": "68298-81-7", "Alpha Docking Score": -7.9, "Beta Docking Score": -7.9, "Difference (Alpha - Beta)": 0.0},
        {"CASRN": "68555-74-8", "Alpha Docking Score": -7.9, "Beta Docking Score": -7.4, "Difference (Alpha - Beta)": -0.5},
        {"CASRN": "97659-47-7", "Alpha Docking Score": -9.9, "Beta Docking Score": -10.3, "Difference (Alpha - Beta)": 0.4},
        {"CASRN": "61660-12-6", "Alpha Docking Score": -6.5, "Beta Docking Score": -6.5, "Difference (Alpha - Beta)": 0.0},
        {"CASRN": "65530-66-7", "Alpha Docking Score": -5.8, "Beta Docking Score": -6.0, "Difference (Alpha - Beta)": 0.2},
        {"CASRN": "78560-44-8", "Alpha Docking Score": -6.2, "Beta Docking Score": -6.5, "Difference (Alpha - Beta)": 0.3},
        {"CASRN": "83048-65-1", "Alpha Docking Score": -6.0, "Beta Docking Score": -6.3, "Difference (Alpha - Beta)": 0.3},
        {"CASRN": "21615-47-4", "Alpha Docking Score": -6.5, "Beta Docking Score": -6.8, "Difference (Alpha - Beta)": 0.3},
        {"CASRN": "65530-63-4", "Alpha Docking Score": -6.0, "Beta Docking Score": -6.3, "Difference (Alpha - Beta)": 0.3}
    ]
    df = pd.DataFrame(data)
    st.markdown("### 📋 Docking Score Comparison Table")
    st.dataframe(df, use_container_width=True)

    # Scatter plot: Alpha vs Beta docking score
    st.markdown("### 🎯 Scatter Plot: Alpha vs Beta Docking Score")
    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(
        x=df['Alpha Docking Score'],
        y=df['Beta Docking Score'],
        mode='markers',
        marker=dict(color='#2563eb', size=8, opacity=0.7),
        text=df['CASRN'],
        showlegend=False
    ))
    fig_scatter.add_trace(go.Scatter(
        x=[df['Alpha Docking Score'].min(), df['Alpha Docking Score'].max()],
        y=[df['Alpha Docking Score'].min(), df['Alpha Docking Score'].max()],
        mode='lines',
        line=dict(color='gray', dash='dash'),
        name='y=x (Equal Score)'
    ))
    fig_scatter.update_layout(
        title="Alpha vs Beta Docking Score (CE Ligands)",
        xaxis_title="Alpha Docking Score",
        yaxis_title="Beta Docking Score",
        height=400,
        xaxis=dict(range=[df['Alpha Docking Score'].min()-0.5, df['Alpha Docking Score'].max()+0.5], fixedrange=True),
        yaxis=dict(range=[df['Beta Docking Score'].min()-0.5, df['Beta Docking Score'].max()+0.5], fixedrange=True),
        dragmode=False
    )
    st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

    # Histogram of differences
    st.markdown("### 🧬 Histogram: Alpha - Beta Docking Score Differences")
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=df['Difference (Alpha - Beta)'],
        marker_color="#14b8a6",
        nbinsx=20,
        showlegend=False
    ))
    fig_hist.update_layout(
        title="Distribution of Docking Score Differences (Alpha - Beta)",
        xaxis_title="Alpha - Beta Docking Score",
        yaxis_title="Ligand Count",
        height=350,
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True),
        dragmode=False
    )
    st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

    st.markdown("### 💡 Key Insights")
    st.info(f"""
    - The CE ligands show a wide range of docking score differences between Alpha and Beta receptors.
    - Some ligands (like 65510-55-6, 34362-49-7) show significantly better binding to Beta than Alpha.
    - The distribution of differences shows both positive and negative values, indicating receptor-specific binding preferences.
    - Most ligands show moderate differences (within ±1.0 kcal/mol), with a few outliers showing larger differences.
    """)

def show_chemical_descriptor_analysis():
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    st.markdown("## Chemical Descriptor Analysis")
    st.markdown("Property distributions and trends based on normalized coefficients across QSPR models.")

    # Updated descriptor coefficients from the provided table
    data = [
        ["# of H-Bond Acceptors", 0.0408, 0.1842, -0.4964, -0.3563],
        ["# of H-Bond Donors", -0.0322, 0.0363, -0.0487, -0.0212],
        ["LogD", 0.2422, 0.8252, 0.1923, -0.3679],
        ["Average Mass", 49.2514, 30.1649, -4.1092, 7.8995],
        ["Density", 0.0219, 0.0420, 0.0513, 0.0445],
        ["F- Max", 0.0011, -0.0048, -0.0043, 0.0034],
        ["HOMO", -0.0449, -0.0459, 0.7999, 0.1153],
        ["LUMO", 0.0434, 0.1306, 0.1539, 0.3954],
        ["Polar Surface Area", -0.9347, 0.2707, 10.6211, 4.1924],
        ["Surface Tension", -1.3549, -1.3352, -2.3411, -1.5560],
        ["# of Freely Rotating Bonds", -2.3991, -3.3561, 1.0370, 2.6684],
    ]
    df = pd.DataFrame(data, columns=[
        "Descriptor",
        "Top Binders ERα",
        "Top Binders ERβ", 
        "Commonly Exposed ERα",
        "Commonly Exposed ERβ"
    ])
    st.markdown("### 📋 QSPR Model Coefficients Table")
    st.dataframe(df, use_container_width=True)

    # Heatmap
    st.markdown("### 🔥 Descriptor Coefficient Heatmap")
    st.write("This heatmap shows the direction (red=negative, green=positive) and strength (color intensity) of each descriptor's normalized coefficient in each model. Values are standardized to allow comparison across different descriptor scales.")
    
    # Create a copy of the dataframe for heatmap visualization
    heatmap_df = df.set_index("Descriptor").T.copy()
    
    # Calculate percentiles for better color scaling (excluding extreme outliers)
    all_values = heatmap_df.values.flatten()
    p5 = np.percentile(all_values, 5)
    p95 = np.percentile(all_values, 95)
    
    # Use a more balanced color scale range
    color_range = max(abs(p5), abs(p95))
    
    fig_heatmap = px.imshow(
        heatmap_df,
        color_continuous_scale=["#ef4444", "#f9fafb", "#22c55e"],
        aspect="auto",
        labels=dict(x="Descriptor", y="Model", color="Normalized Coefficient"),
        zmin=-color_range, 
        zmax=color_range
    )
    fig_heatmap.update_layout(
        height=400,
        xaxis_title="Descriptor",
        yaxis_title="Model",
        coloraxis_colorbar=dict(title="Normalized Coefficient Value"),
        dragmode=False
    )
    st.plotly_chart(fig_heatmap, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})
    
    # Add a note about the color scaling
    st.caption("💡 **Color Scale Note**: The heatmap uses percentile-based scaling to better visualize coefficient patterns. Extreme values (like Average Mass) are scaled to show relative importance while maintaining visibility of other descriptors.")

    # Top Influencers
    st.markdown("### ⭐ Top Influential Descriptors per Model")
    st.write("For each model, the top 3 positive and top 3 negative normalized coefficients are shown. This highlights the most important features for binding affinity prediction.")
    models = ["Top Binders ERα", "Top Binders ERβ", "Commonly Exposed ERα", "Commonly Exposed ERβ"]
    for model in models:
        st.markdown(f"#### {model} Model")
        top_pos = df.nlargest(3, model)[["Descriptor", model]]
        top_neg = df.nsmallest(3, model)[["Descriptor", model]]
        top = pd.concat([top_pos, top_neg])
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=top["Descriptor"],
            x=top[model],
            orientation='h',
            marker_color=["#22c55e" if v >= 0 else "#ef4444" for v in top[model]],
            showlegend=False
        ))
        fig_bar.update_layout(
            title=f"Top Influential Descriptors ({model})",
            xaxis_title="Normalized Coefficient Value",
            yaxis_title="Descriptor",
            height=350,
            yaxis=dict(autorange="reversed", fixedrange=True),
            xaxis=dict(fixedrange=True),
            dragmode=False
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

    st.markdown("### 💡 Key Insights")
    st.info("""
    - **Normalized Coefficients**: All values are standardized to allow meaningful comparison across different descriptor scales and units.
    - **Model-Specific Patterns**: Top Binders and Commonly Exposed models show distinct descriptor importance patterns.
    - **Receptor Differences**: ERα and ERβ models exhibit different coefficient patterns, indicating receptor-specific binding preferences.
    - **Key Descriptors**: Average Mass, Polar Surface Area, and # of Freely Rotating Bonds show the largest coefficient magnitudes across models.
    - **Directional Effects**: Positive coefficients indicate increased binding affinity, while negative coefficients suggest decreased binding.
    - **Scale Differences**: Some descriptors (like Average Mass) have much larger coefficient values due to their measurement scales, highlighting the importance of normalization.
    """)

def show_qsar_results():
    import pandas as pd
    st.markdown("## QSAR Results: Large Set Model Performance")
    st.markdown("Explore the performance of large set QSAR models for ERα and ERβ, including the effect of outlier removal.")

    # Updated R² summary table with Train and Test values
    r2_data = [
        ["Alpha", "Original", 0.461, 0.385],
        ["Alpha", "10% Outliers Removed", 0.556, 0.528],
        ["Alpha", "20% Outliers Removed", 0.713, 0.704],
        ["Beta", "Original", 0.488, 0.446],
        ["Beta", "10% Outliers Removed", 0.554, 0.522],
        ["Beta", "20% Outliers Removed", 0.687, 0.679],
    ]
    df_r2 = pd.DataFrame(r2_data, columns=["Receptor", "Refinement Step", "R² (Train)", "R² (Test)"])
    st.markdown("### 📊 Model R² Summary Table")
    st.dataframe(df_r2, use_container_width=True)

    # Model improvement visualization
    st.markdown("### 📈 Model Improvement Analysis")
    st.markdown("Visual comparison of R² improvements across refinement steps for Alpha and Beta receptors, showing both training and test performance.")
    
    import plotly.graph_objects as go
    
    # Create grouped bar chart with Train and Test values
    fig = go.Figure()
    
    # Alpha Train data
    alpha_data = df_r2[df_r2['Receptor'] == 'Alpha']
    fig.add_trace(go.Bar(
        name='Alpha Train',
        x=alpha_data['Refinement Step'],
        y=alpha_data['R² (Train)'],
        marker_color='#3b82f6',
        text=alpha_data['R² (Train)'].round(3),
        textposition='auto',
    ))
    
    # Alpha Test data
    fig.add_trace(go.Bar(
        name='Alpha Test',
        x=alpha_data['Refinement Step'],
        y=alpha_data['R² (Test)'],
        marker_color='#60a5fa',
        text=alpha_data['R² (Test)'].round(3),
        textposition='auto',
    ))
    
    # Beta Train data
    beta_data = df_r2[df_r2['Receptor'] == 'Beta']
    fig.add_trace(go.Bar(
        name='Beta Train',
        x=beta_data['Refinement Step'],
        y=beta_data['R² (Train)'],
        marker_color='#ef4444',
        text=beta_data['R² (Train)'].round(3),
        textposition='auto',
    ))
    
    # Beta Test data
    fig.add_trace(go.Bar(
        name='Beta Test',
        x=beta_data['Refinement Step'],
        y=beta_data['R² (Test)'],
        marker_color='#f87171',
        text=beta_data['R² (Test)'].round(3),
        textposition='auto',
    ))
    
    fig.update_layout(
        title="R² Improvement Across Refinement Steps (Train vs Test)",
        xaxis_title="Refinement Step",
        yaxis_title="R² Value",
        barmode='group',
        height=500,
        showlegend=True,
        yaxis=dict(range=[0, 0.8]),
        plot_bgcolor='white',
        paper_bgcolor='white',
    )
    
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})
    
    # Improvement summary
    st.markdown("#### Key Performance Metrics:")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        alpha_train_improvement = ((alpha_data.iloc[2]['R² (Train)'] - alpha_data.iloc[0]['R² (Train)']) / alpha_data.iloc[0]['R² (Train)'] * 100).round(1)
        st.metric("Alpha Train Improvement", f"{alpha_train_improvement}%", f"0.461 → 0.713")
    
    with col2:
        alpha_test_improvement = ((alpha_data.iloc[2]['R² (Test)'] - alpha_data.iloc[0]['R² (Test)']) / alpha_data.iloc[0]['R² (Test)'] * 100).round(1)
        st.metric("Alpha Test Improvement", f"{alpha_test_improvement}%", f"0.385 → 0.704")
    
    with col3:
        beta_train_improvement = ((beta_data.iloc[2]['R² (Train)'] - beta_data.iloc[0]['R² (Train)']) / beta_data.iloc[0]['R² (Train)'] * 100).round(1)
        st.metric("Beta Train Improvement", f"{beta_train_improvement}%", f"0.488 → 0.687")
    
    with col4:
        beta_test_improvement = ((beta_data.iloc[2]['R² (Test)'] - beta_data.iloc[0]['R² (Test)']) / beta_data.iloc[0]['R² (Test)'] * 100).round(1)
        st.metric("Beta Test Improvement", f"{beta_test_improvement}%", f"0.446 → 0.679")

def main():
    st.markdown('<h1 class="main-header">🧬 QSPR/QSAR Molecular Visualization Tool</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Interactive 3D visualization of ERα and ERβ receptor-PFAS ligand structures</p>', unsafe_allow_html=True)
    st.sidebar.title("Navigation")
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "Home"
    
    # Handle page navigation from buttons
    if st.session_state.page != "Home":
        page = st.session_state.page
        st.session_state.page = "Home"  # Reset for next time
    else:
        page = st.sidebar.selectbox(
            "Choose a page:",
            [
                "Home",
                "ERα Receptor",
                "ERβ Receptor",
                "Data Analysis Dashboard",
                "CE Ligand Comparison",
                "Chemical Descriptor Analysis",
                "QSAR Results",
                "About"
            ]
        )
    
    if page == "Home":
        show_home_page()
    elif page == "ERα Receptor":
        show_alpha_page()
    elif page == "ERβ Receptor":
        show_beta_page()
    elif page == "Data Analysis Dashboard":
        show_data_analysis_dashboard()
    elif page == "CE Ligand Comparison":
        show_ce_ligand_comparison()
    elif page == "Chemical Descriptor Analysis":
        show_chemical_descriptor_analysis()
    elif page == "QSAR Results":
        show_qsar_results()
    elif page == "About":
        show_about_page()

def show_home_page():
    st.markdown("## Welcome to QSPR/QSAR Molecular Visualization Tool")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="receptor-card">
            <h2 style='font-size:2rem;font-weight:800;'>🧬 ERα Receptor</h2>
            <p style='font-size:1.1rem;'>Estrogen Receptor Alpha - Primary target for estrogen signaling</p>
            <div class="info-block">
                <strong>138</strong><br>
                <small>Ligands</small>
            </div>
            <div class="info-block">
                <strong>3D</strong><br>
                <small>Visualization</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="receptor-card-beta">
            <h2 style='font-size:2rem;font-weight:800;'>🧬 ERβ Receptor</h2>
            <p style='font-size:1.1rem;'>Estrogen Receptor Beta - Secondary estrogen receptor subtype</p>
            <div class="info-block">
                <strong>138</strong><br>
                <small>Ligands</small>
            </div>
            <div class="info-block">
                <strong>3D</strong><br>
                <small>Visualization</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    ### How to Use This Tool
    1. **Select a Receptor**: Choose between ERα (primary estrogen receptor) or ERβ (secondary estrogen receptor)
    2. **Choose a Ligand**: Select from 138 available PFAS ligands
    3. **Visualize**: Use the embedded 3D viewer or download the PDB file
    ### Available Features
    - **PFAS Ligands**: Each ligand is combined with the selected receptor
    - **3D Visualization**: Interactive molecular viewer built into the browser
    - **Cross-platform**: Works on any device with a web browser
    - **Easy Download**: Direct download links for all combined structures
    """)

def show_alpha_page():
    st.markdown("## 🧬 ERα Receptor Visualization")
    st.markdown("**Estrogen Receptor Alpha - Primary target for estrogen signaling**")
    
    # Select dataset
    dataset = st.selectbox(
        "Choose a dataset:",
        ["Commonly Exposed Set", "Top 50 Set"],
        index=0
    )
    
    # Get ligands based on selected dataset
    if dataset == "Commonly Exposed Set":
        folder_name = "Alpha_CE_Combined"
    else:  # Top 50 Set
        folder_name = "Alpha_T50_Combined"
    
    alpha_ligands = get_ligand_list(folder_name)
    if not alpha_ligands:
        st.error(f"No combined PDB files found in '{folder_name}' folder. Please run the combine_pdb.py script first.")
        return
    
    st.markdown("### Select a Ligand")
    selected_ligand = st.selectbox(
        f"Choose a PFAS ligand to visualize with ERα ({dataset}):",
        alpha_ligands,
        index=0
    )
    if selected_ligand:
        # Different file naming patterns for different datasets
        if dataset == "Top 50 Set":
            file_name = f"{selected_ligand}_top_complex.pdb"
        else:  # Commonly Exposed Set
            file_name = f"combined_{selected_ligand}_out.pdb"
        
        file_path = Path(folder_name) / file_name
        if file_path.exists():
            file_size = file_path.stat().st_size / 1024
            st.info(f"**File Size:** {file_size:.1f} KB")
            pdb_content = file_path.read_text()
            st.download_button(
                label="📁 Download PDB File",
                data=pdb_content,
                file_name=file_name,
                mime="chemical/x-pdb",
                key="alpha_download"
            )
            st.markdown("### 🧬 Interactive 3D Molecular Viewer")
            st.markdown("**Rotate, zoom, and explore the molecular structure directly in your browser**")
            viewer_html = create_ngl_viewer(pdb_content, f"ERα + {selected_ligand}")
            st.components.v1.html(viewer_html, height=600)
            st.markdown("""
            **Viewer Controls:**
            - **Mouse**: Rotate the structure
            - **Scroll**: Zoom in/out (page will not scroll)
            - **Right-click + drag**: Pan the view
            - **Double-click**: Reset view
            """)
            st.markdown("### File Preview")
            with st.expander("View PDB file content (first 50 lines)"):
                lines = pdb_content.split('\n')[:50]
                st.code('\n'.join(lines))
        else:
            st.error(f"❌ Combined PDB file not found: {file_path}")

def show_beta_page():
    st.markdown("## 🧬 ERβ Receptor Visualization")
    st.markdown("**Estrogen Receptor Beta - Secondary estrogen receptor subtype**")
    
    # Select dataset
    dataset = st.selectbox(
        "Choose a dataset:",
        ["Commonly Exposed Set", "Top 50 Set"],
        index=0
    )
    
    # Get ligands based on selected dataset
    if dataset == "Commonly Exposed Set":
        folder_name = "Beta_CE_Combined"
    else:  # Top 50 Set
        folder_name = "Beta_T50_Combined"
    
    beta_ligands = get_ligand_list(folder_name)
    if not beta_ligands:
        st.error(f"No combined PDB files found in '{folder_name}' folder. Please run the combine_pdb.py script first.")
        return
    
    st.markdown("### Select a Ligand")
    selected_ligand = st.selectbox(
        f"Choose a PFAS ligand to visualize with ERβ ({dataset}):",
        beta_ligands,
        index=0
    )
    if selected_ligand:
        # Different file naming patterns for different datasets
        if dataset == "Top 50 Set":
            file_name = f"{selected_ligand}_out_complex.pdb"
        else:  # Commonly Exposed Set
            file_name = f"combined_{selected_ligand}_out.pdb"
        
        file_path = Path(folder_name) / file_name
        if file_path.exists():
            file_size = file_path.stat().st_size / 1024
            st.info(f"**File Size:** {file_size:.1f} KB")
            pdb_content = file_path.read_text()
            st.download_button(
                label="📁 Download PDB File",
                data=pdb_content,
                file_name=file_name,
                mime="chemical/x-pdb",
                key="beta_download"
            )
            st.markdown("### 🧬 Interactive 3D Molecular Viewer")
            st.markdown("**Rotate, zoom, and explore the molecular structure directly in your browser**")
            viewer_html = create_ngl_viewer(pdb_content, f"ERβ + {selected_ligand}")
            st.components.v1.html(viewer_html, height=600)
            st.markdown("""
            **Viewer Controls:**
            - **Mouse**: Rotate the structure
            - **Scroll**: Zoom in/out (page will not scroll)
            - **Right-click + drag**: Pan the view
            - **Double-click**: Reset view
            """)
            st.markdown("### File Preview")
            with st.expander("View PDB file content (first 50 lines)"):
                lines = pdb_content.split('\n')[:50]
                st.code('\n'.join(lines))
        else:
            st.error(f"❌ Combined PDB file not found: {file_path}")

def show_data_analysis_dashboard():
    st.markdown("## 📊 Data Analysis Dashboard")
    st.markdown("**Statistical summaries and visualizations of the 4 datasets**")

    # Real statistics from parsed Excel files (means only)
    summary_data = [
        {
            "Dataset": "CE Ligands",
            "Ligand Count": 69,
            "Alpha Docking Score": "-8.149275362",
            "Beta Docking Score": "-8.253623188",
            "LogP": "5.727246377",
            "MW": "505.3214551",
            "PSA": "41.26086957"
        },
        {
            "Dataset": "Alpha TB",
            "Ligand Count": 69,
            "Alpha Docking Score": "-11.27",
            "Beta Docking Score": "—",
            "LogP": "6.01",
            "MW": "507.02",
            "PSA": "17.08"
        },
        {
            "Dataset": "Beta TB",
            "Ligand Count": 69,
            "Alpha Docking Score": "—",
            "Beta Docking Score": "-11.02608696",
            "LogP": "5.519036232",
            "MW": "568.5555623",
            "PSA": "16.73855072"
        }
    ]
    df_summary = pd.DataFrame(summary_data)
    st.markdown("### 📋 Dataset Comparison")
    st.dataframe(df_summary, use_container_width=True)

    # Prepare data for charts (means only)
    chart_data = pd.DataFrame({
        "Dataset": ["CE Ligands (Alpha)", "CE Ligands (Beta)", "Alpha TB", "Beta TB"],
        "Docking Score Mean": [-8.149275362, -8.253623188, -11.27, -11.02608696],
        "Type": ["CE", "CE", "TB", "TB"],
        "Receptor": ["Alpha", "Beta", "Alpha", "Beta"]
    })

    # Chart: Docking Score Means (no error bars)
    st.markdown("### 🎯 Docking Score Comparison")
    fig_docking = go.Figure()
    colors = ["#2563eb", "#14b8a6", "#f59e42", "#e11d48"]
    for i, row in chart_data.iterrows():
        fig_docking.add_trace(go.Bar(
            x=[row["Dataset"]],
            y=[row["Docking Score Mean"]],
            name=row["Dataset"],
            marker_color=colors[i]
        ))
    min_ds = min(chart_data["Docking Score Mean"])
    max_ds = max(chart_data["Docking Score Mean"])
    fig_docking.update_layout(
        barmode='group',
        title="Average Docking Scores",
        yaxis_title="Docking Score (kcal/mol)",
        xaxis_title="Dataset",
        height=400,
        yaxis=dict(range=[min_ds-0.5, max_ds+0.5], fixedrange=True),
        dragmode=False
    )
    st.plotly_chart(fig_docking, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

    # Chart: Descriptor Comparison (means only)
    st.markdown("### 🧬 Descriptor Comparison")
    desc_data = pd.DataFrame({
        "Dataset": ["CE Ligands", "Alpha TB", "Beta TB"],
        "LogP": [5.727246377, 6.01, 5.519036232],
        "MW": [505.3214551, 507.02, 568.5555623],
        "PSA": [41.26086957, 17.08, 16.73855072]
    })
    # LogP
    fig_logp = go.Figure()
    for i, row in desc_data.iterrows():
        fig_logp.add_trace(go.Bar(
            x=[row["Dataset"]],
            y=[row["LogP"]],
            name=row["Dataset"],
            marker_color=colors[i]
        ))
    min_logp = min(desc_data["LogP"])
    max_logp = max(desc_data["LogP"])
    fig_logp.update_layout(
        barmode='group',
        title="Average LogP",
        yaxis_title="LogP",
        xaxis_title="Dataset",
        height=350,
        yaxis=dict(range=[min_logp-0.5, max_logp+0.5], fixedrange=True),
        dragmode=False
    )
    st.plotly_chart(fig_logp, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})
    # MW
    fig_mw = go.Figure()
    for i, row in desc_data.iterrows():
        fig_mw.add_trace(go.Bar(
            x=[row["Dataset"]],
            y=[row["MW"]],
            name=row["Dataset"],
            marker_color=colors[i]
        ))
    min_mw = min(desc_data["MW"])
    max_mw = max(desc_data["MW"])
    fig_mw.update_layout(
        barmode='group',
        title="Average Molecular Weight",
        yaxis_title="Molecular Weight (g/mol)",
        xaxis_title="Dataset",
        height=350,
        yaxis=dict(range=[min_mw-10, max_mw+10], fixedrange=True),
        dragmode=False
    )
    st.plotly_chart(fig_mw, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})
    # PSA
    fig_psa = go.Figure()
    for i, row in desc_data.iterrows():
        fig_psa.add_trace(go.Bar(
            x=[row["Dataset"]],
            y=[row["PSA"]],
            name=row["Dataset"],
            marker_color=colors[i]
        ))
    min_psa = min(desc_data["PSA"])
    max_psa = max(desc_data["PSA"])
    fig_psa.update_layout(
        barmode='group',
        title="Average Polar Surface Area",
        yaxis_title="Polar Surface Area",
        xaxis_title="Dataset",
        height=350,
        yaxis=dict(range=[min_psa-2, max_psa+2], fixedrange=True),
        dragmode=False
    )
    st.plotly_chart(fig_psa, use_container_width=True, config={"displayModeBar": False, "staticPlot": True})

    st.markdown("### 💡 Key Insights")
    st.info("""
    - **CE Ligands** have moderate LogP values and higher PSA compared to TB sets, with moderate docking scores.
    - **Alpha TB and Beta TB** have similar strong docking scores, but their ligand properties differ.
    - **Beta TB** ligands have lower LogP and PSA but higher MW than Alpha TB.
    """)

def show_about_page():
    st.markdown("## About QSPR/QSAR Molecular Visualization Tool")
    st.markdown("""
    ### Overview
    This tool provides an interactive web-based interface for visualizing QSAR (Quantitative Structure-Activity Relationship) molecular structures, specifically focusing on Estrogen Receptor (ER) interactions with PFAS ligands.
    ### Features
    - **Dual Receptor Support**: ERα and ERβ receptor visualization
    - **PFAS Ligands**: Comprehensive library of per- and polyfluoroalkyl substances
    - **Combined Structures**: Pre-combined receptor-ligand complexes
    - **Embedded 3D Viewer**: Interactive molecular visualization using NGL Viewer
    - **Multiple Output Options**: Download, open with default viewer, or copy file paths
    - **Cross-platform Compatibility**: Works on any device with a web browser
    - **No Installation Required**: Everything works in your browser
    ### Technical Details
    - **File Format**: PDB (Protein Data Bank) format
    - **Combined Files**: Each file contains both receptor and ligand structures
    - **3D Viewer**: NGL Viewer for interactive molecular visualization
    - **File Organization**: 
      - `Alpha Combined/`: ERα receptor + ligand complexes
      - `Beta Combined/`: ERβ receptor + ligand complexes
    ### Viewer Features
    - **Interactive 3D Visualization**: Rotate, zoom, and pan molecular structures
    - **Multiple Representations**: Cartoon and ball+stick views
    - **Color Coding**: Chain-based coloring for easy identification
    - **Hetero Atoms**: Ligands displayed as ball+stick representation
    - **Responsive Design**: Works on desktop, tablet, and mobile devices
    ### Recommended Molecular Viewers (for downloaded files)
    - **PyMOL**: Professional molecular visualization
    - **VMD**: Visual Molecular Dynamics
    - **ChimeraX**: UCSF ChimeraX
    - **Jmol**: Java-based molecular viewer
    - **Online viewers**: NGL Viewer, Mol* Viewer
    ### Usage Instructions
    1. Navigate to the desired receptor page (ERα or ERβ)
    2. Select a ligand from the dropdown menu
    3. Use the embedded 3D viewer to explore the structure
    4. Choose additional actions:
       - Download the PDB file
       - Open with your default molecular viewer
       - Copy the file path for manual access
    ### Data Source
    The combined PDB files are generated from individual receptor and ligand structures, providing ready-to-use complexes for molecular visualization and analysis.
    """)

if __name__ == "__main__":
    main() 