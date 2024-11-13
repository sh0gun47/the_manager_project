import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def create_value_added_charts():
    # Read the data
    df = pd.read_csv('data/trans/player_index.csv')
    manager_history = pd.read_csv('data/trans/manager_history.csv')
    
    # Filter managers by end_date
    recent_managers = manager_history[
        pd.to_datetime(manager_history['end_date']) >= '2019-11-13'
    ]['manager_id'].unique()
    
    # Filter player data for these managers
    df = df[df['manager_id'].isin(recent_managers)]
    
    # Calculate manager tenures
    manager_history['start_date'] = pd.to_datetime(manager_history['start_date'])
    manager_history['end_date'] = pd.to_datetime(manager_history['end_date'])
    manager_history['years_in_charge'] = (manager_history['end_date'] - manager_history['start_date']).dt.days / 365.25
    
    # Calculate value added for each managerial stint first
    stint_totals = df.groupby(['manager_id', 'manager_name']).agg({
        'start_value': 'sum',
        'peak_value': 'sum'
    }).reset_index()
    
    stint_totals['value_added'] = stint_totals['peak_value'] - stint_totals['start_value']
    
    # Now aggregate at manager level
    manager_totals = stint_totals.groupby('manager_name').agg({
        'value_added': 'sum',
        'start_value': 'sum'
    }).reset_index()
    
    # Add tenure information
    manager_years = manager_history.groupby('manager_name')['years_in_charge'].sum().reset_index()
    manager_totals = manager_totals.merge(manager_years, on='manager_name')
    
    # Calculate final metrics
    manager_totals['value_added_millions'] = (manager_totals['value_added'] / 1000000).round(1)
    manager_totals['value_added_pct'] = ((manager_totals['value_added'] / manager_totals['start_value']) * 100).round(1)
    manager_totals['value_added_pct_per_year'] = (manager_totals['value_added_pct'] / manager_totals['years_in_charge']).round(1)
    
    # Sort dataframes
    manager_abs = manager_totals.sort_values('value_added_millions', ascending=False)
    manager_pct = manager_totals.sort_values('value_added_pct', ascending=False)
    manager_annual = manager_totals.sort_values('value_added_pct_per_year', ascending=False)
    
    # Create absolute value chart
    fig1 = px.bar(
        manager_abs,
        x='manager_name',
        y='value_added_millions',
        text='value_added_millions',
        title='Total Value Added by Manager (Peak Value - Start Value)',
        labels={
            'manager_name': 'Manager',
            'value_added_millions': 'Value Added (Million €)'
        },
        category_orders={"manager_name": manager_abs['manager_name'].tolist()}
    )
    
    fig1.update_traces(texttemplate='€%{text}M', textposition='outside')
    fig1.update_layout(
        xaxis_tickangle=-45,
        height=800,
        width=1400,
        showlegend=False,
        title_x=0.5,
        title_font_size=20,
        margin=dict(b=100)
    )
    
    # Create total percentage chart
    fig2 = px.bar(
        manager_pct,
        x='manager_name',
        y='value_added_pct',
        text='value_added_pct',
        title='Total Percentage Value Added by Manager ((Peak Value - Start Value) / Start Value)',
        labels={
            'manager_name': 'Manager',
            'value_added_pct': 'Value Added (%)'
        },
        category_orders={"manager_name": manager_pct['manager_name'].tolist()}
    )
    
    fig2.update_traces(texttemplate='%{text}%', textposition='outside')
    fig2.update_layout(
        xaxis_tickangle=-45,
        height=800,
        width=1400,
        showlegend=False,
        title_x=0.5,
        title_font_size=20,
        margin=dict(b=100)
    )
    
    # Create annualized percentage chart
    fig3 = px.bar(
        manager_annual,
        x='manager_name',
        y='value_added_pct_per_year',
        text='value_added_pct_per_year',
        title='Annualized Percentage Value Added by Manager (% Increase Per Year)',
        labels={
            'manager_name': 'Manager',
            'value_added_pct_per_year': 'Value Added (% per Year)'
        },
        category_orders={"manager_name": manager_annual['manager_name'].tolist()}
    )
    
    fig3.update_traces(texttemplate='%{text}%', textposition='outside')
    fig3.update_layout(
        xaxis_tickangle=-45,
        height=800,
        width=1400,
        showlegend=False,
        title_x=0.5,
        title_font_size=20,
        margin=dict(b=100)
    )
    
    return fig1, fig2, fig3

# Streamlit app
st.title('Premier League Manager Analysis')

# Display all three charts
fig1, fig2, fig3 = create_value_added_charts()
st.plotly_chart(fig1, use_container_width=False)
st.plotly_chart(fig2, use_container_width=False)
st.plotly_chart(fig3, use_container_width=False)
