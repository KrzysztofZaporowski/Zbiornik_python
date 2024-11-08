import plotly.express as pl
import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output, State

# Initial parameters
initial_a = 1.5
initial_beta = 0.035
initial_t_sim = 3600.0
initial_h = 1.25
initial_k_p = 0.02

# Other parameters
T_p = 0.1
T_i = 0.5
U_min = 0  # bottom bound - voltage
U_max = 10  # upper bound - voltage
Qd_max = 0.05  # upper bound
Qd_min = 0  # bottom bound

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Simulation of water level in the tank", style={'textAlign': 'center', 'margin-top': '20px'}),

    html.H2("Setting parameters"),

    html.Div([
        html.Div([
            html.Label("Adjust regulator gain (kₚ)"),
            dcc.Dropdown(
                id='k_p_value',
                options=[
                    {'label': '0.005', 'value': '0.005'},
                    {'label': '0.01', 'value': '0.01'},
                    {'label': '0.015', 'value': '0.015'},
                    {'label': '0.02', 'value': '0.02'},
                    {'label': '0.025', 'value': '0.025'},
                    {'label': '0.03', 'value': '0.03'}
                ],
                value=str(initial_k_p),
                style={'width': '100%'}
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding-right': '10px'}),

        html.Div([
            html.Label("Adjust desired water level (h) [m]"),
            dcc.Dropdown(
                id='h_value',
                options=[
                    {'label': str(value), 'value': str(value)}
                    for value in [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3]
                ],
                value=str(initial_h),
                style={'width': '100%'}
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding-right': '10px'}),

        html.Div([
            html.Label("Adjust beta parameter (beta)"),
            dcc.Dropdown(
                id='beta_value',
                options=[
                    {'label': '0.01', 'value': '0.01'}, {'label': '0.015', 'value': '0.015'},
                    {'label': '0.02', 'value': '0.02'}, {'label': '0.025', 'value': '0.025'},
                    {'label': '0.03', 'value': '0.03'}, {'label': '0.035', 'value': '0.035'},
                    {'label': '0.04', 'value': '0.04'}, {'label': '0.045', 'value': '0.045'},
                    {'label': '0.05', 'value': '0.05'}, {'label': '0.055', 'value': '0.055'},
                    {'label': '0.06', 'value': '0.06'}, {'label': '0.065', 'value': '0.065'},
                    {'label': '0.07', 'value': '0.07'}, {'label': '0.075', 'value': '0.075'},
                    {'label': '0.08', 'value': '0.08'}, {'label': '0.085', 'value': '0.085'},
                    {'label': '0.09', 'value': '0.09'}, {'label': '0.095', 'value': '0.095'},
                    {'label': '0.1', 'value': '0.1'},
                ],
                value=str(initial_beta),
                style={'width': '100%'}
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding-right': '10px'})
    ]),
    html.Br(),
    html.Br(),

    html.Label("Adjust tank cross-section (A) [m²]"),
    dcc.Slider(
        id='a_value',
        min=0.5,
        max=5.0,
        step=0.25,
        value=initial_a,
        marks={i: str(i) for i in range(1, 6)}
    ),

    html.Label("Adjust simulation time (tₛᵢₘ) [s]"),
    dcc.Slider(
        id='t_sim_value',
        min=1000,
        max=5000,
        step=500,
        value=initial_t_sim,
        marks={i: str(i) for i in range(1000, 5001, 500)},
    ),
    html.Button(
        'Reset values',
        id='reset_button',
        n_clicks=0,
        style={'fontSize': '16px', 'marginTop': '20px'}
    ),
    html.Div(style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}, children=[
        html.H3("Plot of water height in the tank over time"),
        dcc.Graph(id='h(t)_plot', style={'height': '500px', 'width': '100%'}),
        html.H3("Graph of water outflow and inflow in the tank over time"),
        dcc.Graph(id='inflow_outflow_graph', style={'height': '500px', 'width': '100%'}),
        html.H3("Control PI voltage over time"),
        dcc.Graph('voltage_graph', style={'height': '500px', 'width': '100%'})
    ])
],
    style={'backgroundColor': 'lightcyan', 'height': '220vh', 'padding': '20px'})


def simulate_tank(A, beta, t_sim, h_zad, k_p):
    Qd = [0]  # inflow rate
    h = [0.0]  # level of fluid in tank
    t = [0.0]  # times
    u = [k_p]  # control values
    e = [h_zad - h[0]]
    Q_out = [beta * h[0] ** 0.5]  # outflow
    N = int(t_sim / T_p) + 1
    e_sum = 0
    u_sum = 0

    def calculate_U(e_i, e):
        return (k_p * e_i) + (k_p * T_p / T_i) * sum(e)

    def calculate_Qd(u):
        return ((Qd_max - Qd_min) / (U_max - U_min)) * (u - U_min) + Qd_min

    for _ in range(N):
        t.append(t[-1] + T_p)
        e.append(h_zad - h[_])
        U = min(U_max, max(U_min, calculate_U(e[_ + 1], e)))
        u_sum += abs(U)
        e_sum += abs(e[_ + 1])
        u.append(U)
        Qd.append(calculate_Qd(U))
        Q_out.append(beta * h[_] ** 0.5)
        h.append((Qd[_] - beta * h[-1] ** 0.5) * T_p / A + h[-1])

    return t, h, Qd, Q_out, u, e_sum, u_sum


previous_trace = {'time': [], 'h': [], 'Qd': [], 'Q_out': [], 'u': []}

# Callback to update the graphs based on slider values
@app.callback(
    [Output('h(t)_plot', 'figure'),
     Output('inflow_outflow_graph', 'figure'),
     Output('voltage_graph', 'figure')],
    [Input('a_value', 'value'),
     Input('beta_value', 'value'),
     Input('t_sim_value', 'value'),
     Input('h_value', 'value'),
     Input('k_p_value', 'value')]
)
def update_graphs(A, beta, t_sim, h_zad, k_p):
    global previous_trace
    A = float(A)
    beta = float(beta)
    t_sim = float(t_sim)
    h_zad = float(h_zad)
    k_p = float(k_p)

    t, h, Qd, Q_out, u, e_sum, u_sum = simulate_tank(A, beta, t_sim, h_zad, k_p)

    # Create figures for each graph
    water_level_fig = pl.line(pd.DataFrame({'Time': t, 'Water level': h}),
                              x='Time', y='Water level',
                              title=f"Water level over time (Cumulative Error: {e_sum:.2f})",
                              labels={'Time': 'Time (s)', 'Water level': 'Water level (m)'})
    if previous_trace['time']:
        water_level_fig.add_scatter(x=previous_trace['time'], y=previous_trace['h'],
                                    mode='lines', line=dict(color='gray', dash='dash'),
                                    name="Previous Water Level")

    flow_rate_fig = pl.line(pd.DataFrame({
        'Time': t,
        'Qᵢₙ': Qd,
        'Qₒᵤₜ': Q_out
    }).melt(id_vars='Time', value_vars=['Qᵢₙ', 'Qₒᵤₜ'], var_name='Flow type', value_name='Flow rate'),
                            x='Time', y='Flow rate', color='Flow type',
                            title="Inflow and outflow over time",
                            labels={'Flow rate': 'Flow rate (m³/s)', 'Time': 'Time(s)'}).update_layout(
        legend_title_text='Flow Type')

    if previous_trace['time']:
        flow_rate_fig.add_scatter(x=previous_trace['time'], y=previous_trace['Qd'],
                                  mode='lines', line=dict(color='gray', dash='dash'),
                                  name="Previous Qᵢₙ")
        flow_rate_fig.add_scatter(x=previous_trace['time'], y=previous_trace['Q_out'],
                                  mode='lines', line=dict(color='darkgray', dash='dash'),
                                  name="Previous Qₒᵤₜ")

    voltage_fig = pl.line(pd.DataFrame({'Time': t, 'Voltage': u}),
                          x='Time', y='Voltage',
                          title=f'Control PI voltage over time (Control Effort: {u_sum:.2f})',
                          labels={'Voltage': 'Control voltage(U)', 'Time': 'Time (s)'})

    if previous_trace['time']:
        voltage_fig.add_scatter(x=previous_trace['time'], y=previous_trace['u'],
                                mode='lines', line=dict(color='gray', dash='dash'),
                                name="Previous Voltage")

    previous_trace = {'time': t, 'h': h, 'Qd': Qd, 'Q_out': Q_out, 'u': u}

    return water_level_fig, flow_rate_fig, voltage_fig


# Callback to reset sliders to initial values when reset button is clicked
@app.callback(
    [Output('a_value', 'value'),
     Output('beta_value', 'value'),
     Output('t_sim_value', 'value'),
     Output('h_value', 'value'),
     Output('k_p_value', 'value')],
    [Input('reset_button', 'n_clicks')]
)
def reset_sliders(n_clicks):
    # Reset each slider to its initial value
    return initial_a, initial_beta, initial_t_sim, initial_h, initial_k_p


# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)
