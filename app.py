import streamlit as st
import pandas as pd
import holoviews as hv
from holoviews import opts, dim
from streamlit_bokeh import streamlit_bokeh
from bokeh.models import HoverTool

# Set holoviews to use the bokeh rendering backend
hv.extension('bokeh')

# --- Page Configuration ---
st.set_page_config(
    page_title="Hate Speech Co-occurrence Analysis",
    page_icon="📊",
    layout="wide"
)

# --- Title and Description ---
st.title("Interactive Analysis of Hate Speech Co-occurrence")
st.markdown("""
This application visualizes the co-occurrence of different categories of hate speech.
The chord chart on the left shows the flow between categories, while the heatmap on the right provides a matrix view of the same data.
""")

# --- Data Loading and Pre-processing ---
@st.cache_data
def load_data(file_path):
    """Loads and prepares the co-occurrence matrix."""
    try:
        # Load the matrix
        df = pd.read_csv(file_path, index_col=0)
        # Improvement: Permanently remove the 'general' category as requested
        if 'general' in df.columns:
            df = df.drop('general', axis=1).drop('general', axis=0)
        return df
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found. Please make sure it's in the correct directory.")
        return None

data_matrix = load_data('matrix.csv')

if data_matrix is not None:

    # --- Sidebar Controls ---
    st.sidebar.header("Chart Controls")
    min_connection_strength = st.sidebar.slider(
        "Minimum Connection Strength",
        min_value=0,
        max_value=int(data_matrix.values.max()),
        value=50,
        help="Filters the Chord Chart to show connections only for co-occurrences greater than this value."
    )

    # --- Page Layout (3/4 for Chord, 1/4 for Heatmap) ---
    col1, col2 = st.columns([3, 1])

    # --- Static Color Mapping ---
    category_colors = {
        'queerphobic': '#e6194b', 'communal': '#3cb44b', 'political': '#ffe119',
        'sexist': '#4363d8', 'casteist': '#f58231', 'racist': '#911eb4',
        'ablelist': '#46f0f0'
    }

    # --- Column 1: Chord Chart ---
    with col1:
        st.header("Chord Chart Visualization")

        # --- Data Reshaping for Chord Chart ---
        nodes_df = pd.DataFrame(data_matrix.index, columns=['name']).reset_index().rename(columns={'index': 'id'})
        links = data_matrix.stack().reset_index()
        links.columns = ['source_name', 'target_name', 'value']
        name_to_id = {name: i for i, name in enumerate(data_matrix.index)}
        links['source'] = links['source_name'].map(name_to_id)
        links['target'] = links['target_name'].map(name_to_id)

        # Filter links based on the slider
        links_filtered = links[(links['source'] != links['target']) & (links['value'] >= min_connection_strength)]

        nodes_dataset = hv.Dataset(nodes_df, 'id', 'name')
        links_dataset = hv.Dataset(links_filtered, kdims=['source', 'target'], vdims=['value', 'source_name', 'target_name'])

        # --- Chord Chart Creation and Styling ---
        hover_chord = HoverTool(tooltips=[
            ('Connection', '@source_name → @target_name'),
            ('Co-occurrences', '@value')
        ])

        chord_chart = hv.Chord((links_dataset, nodes_dataset)).opts(
            opts.Chord(
                # Improvement: Gradient colors are an inherent behavior in Bokeh's chord plot
                # when both nodes and edges are colored from the same categorical map.
                node_color=dim('name').categorize(category_colors, default='grey'),
                edge_color=dim('source_name').categorize(category_colors, default='grey'),

                labels='name',
                label_text_font_size='10pt',
                width=700,
                height=700,
                tools=[hover_chord]
            )
        )

        # Display the Chord Chart
        bokeh_chord = hv.render(chord_chart, backend='bokeh')
        streamlit_bokeh(bokeh_chord, use_container_width=True)

    # --- Column 2: Heatmap ---
    with col2:
        st.header("Co-occurrence Matrix")

        # Create a HeatMap object from the matrix
        heatmap = hv.HeatMap((data_matrix.columns, data_matrix.index, data_matrix)).opts(
            opts.HeatMap(
                width=400,
                height=400,
                xrotation=45,  # Rotate x-axis labels for readability
                colorbar=True, # Show the color scale
                cmap='viridis',
                tools=['hover'],
                title="Heatmap of Co-occurrences"
            )
        )

        # Display the Heatmap
        bokeh_heatmap = hv.render(heatmap, backend='bokeh')
        streamlit_bokeh(bokeh_heatmap, use_container_width=True)

else:
    st.warning("Could not load data to generate the chart.")

