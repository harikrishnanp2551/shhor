import streamlit as st
import pandas as pd
import holoviews as hv
from holoviews import opts, dim
from streamlit_bokeh import streamlit_bokeh
from bokeh.models import HoverTool

hv.extension('bokeh')

st.set_page_config(
    page_title="Hate Speech Co-occurrence Analysis",
    page_icon="📊",
    layout="wide"
)

st.title("Interactive Hate Speech Co-occurrence Analysis")
st.markdown("""
Explore how different categories of hate speech co-occur. 
Manipulate the minimum connection threshold to filter displayed relationships. 
Use both the **Chord Chart** and **Heatmap** for complementary views.
""")

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path, index_col=0)
        # Drop 'general' category
        if 'general' in df.columns:
            df = df.drop('general', axis=1).drop('general', axis=0)
        return df
    except Exception as e:
        st.error(f"Error loading matrix: {e}")
        return None

# Sidebar controls
st.sidebar.header("Controls")
data_matrix = load_data('matrix.csv')
if data_matrix is not None:
    min_strength = st.sidebar.slider(
        "Minimum Connection Strength", 
        min_value=0, max_value=int(data_matrix.values.max()), value=50, step=1, 
        help="Filter chord connections above threshold."
    )

    # Color mapping for clarity and style
    category_colors = {
        'queerphobic': '#e6194b', 'communal': '#3cb44b', 'political': '#ffe119',
        'sexist': '#4363d8', 'casteist': '#f58231', 'racist': '#911eb4', 'ablelist': '#46f0f0'
    }

    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("Chord Chart")
        nodes_df = pd.DataFrame(data_matrix.index, columns=['name']).reset_index().rename(columns={'index': 'id'})
        links = data_matrix.stack().reset_index()
        links.columns = ['source_name', 'target_name', 'value']
        name_to_id = {name: i for i, name in enumerate(data_matrix.index)}
        links['source'] = links['source_name'].map(name_to_id)
        links['target'] = links['target_name'].map(name_to_id)
        links_filtered = links[(links['source'] != links['target']) & (links['value'] >= min_strength)]

        nodes_dataset = hv.Dataset(nodes_df, 'id', 'name')
        links_dataset = hv.Dataset(links_filtered, kdims=['source', 'target'], vdims=['value', 'source_name', 'target_name'])

        hover_chord = HoverTool(tooltips=[
            ('Connection', '@source_name → @target_name'),
            ('Co-occurrences', '@value')
        ])
        chord_chart = hv.Chord((links_dataset, nodes_dataset)).opts(
            opts.Chord(
                node_color=dim('name').categorize(category_colors, default='grey'),
                edge_color=dim('source_name').categorize(category_colors, default='grey'),
                labels='name',
                label_text_font_size='10pt',
                width=700, height=700,
                tools=[hover_chord]
            )
        )
        bokeh_chord = hv.render(chord_chart, backend='bokeh')
        streamlit_bokeh(bokeh_chord, use_container_width=True)

    with col2:
        st.header("Co-occurrence Heatmap")
        heatmap = hv.HeatMap((data_matrix.columns, data_matrix.index, data_matrix)).opts(
            opts.HeatMap(
                width=400, height=400,
                xrotation=45,
                colorbar=True,
                cmap='viridis',
                tools=['hover'],
                title="Heatmap of Co-occurrences"
            )
        )
        bokeh_heatmap = hv.render(heatmap, backend='bokeh')
        streamlit_bokeh(bokeh_heatmap, use_container_width=True)
else:
    st.warning("Could not load matrix data; please check 'matrix.csv'.")
