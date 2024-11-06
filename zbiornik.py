import plotly.express as pl
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State

# Initial parameters
INITIAL_A = 1.5
INITIAL_BETA = 0.035
INITIAL_T_SIM = 3600.0
INITIAL_H_ZAD = 1.25
INITIAL_K_P = 0.02

# Other fixed parameters
T_p = 0.1
T_i = 0.5
U_min = 0
U_max = 10
Qd_max = 0.05
Qd_min = 0

app = Dash(__name__)

# App layout
app.layout = html.Div(children=[
    html.H1(children='Tank Simulation'),

    # Sliders for adjusting parameters
    html.Label('Adjust Tank Cross-Section (A)'),
    dcc.Slider(id='A-slider', min=0.5, max=5.0, step=0.1, value=INITIAL_A, marks={i: str(i) for i in range(1, 6)}),

    html.Label('Adjust Beta Parameter (beta)'),
    dcc.Slider(id='beta-slider', min=0.01, max=0.1, step=0.001, value=INITIAL_BETA,
               marks={round(i, 2): str(round(i, 2)) for i in [0.01, 0.03, 0.05, 0.07, 0.1]}),

    html.Label('Adjust Simulation Time (t_sim)'),
    dcc.Slider(id='t_sim-slider', min=1000, max=5000, step=100, value=INITIAL_T_SIM,
               marks={i: str(i) for i in range(1000, 5001, 1000)}),

    html.Label('Adjust Desired Water Level (h_zad)'),
    dcc.Slider(id='h_zad-slider', min=0.5, max=3.0, step=0.1, value=INITIAL_H_ZAD,
               marks={i: str(i) for i in range(1, 4)}),

    html.Label('Adjust Regulator Gain (k_p)'),
    dcc.Slider(id='k_p-slider', min=0.01, max=0.1, step=0.001, value=INITIAL_K_P,
               marks={round(i, 2): str(round(i, 2)) for i in [0.01, 0.03, 0.05, 0.07, 0.1]}),

    # Reset Button
    html.Button('Reset to Initial Values', id='reset-button', n_clicks=0),

    # Graphs to display
    html.Div(style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}, children=[
        dcc.Graph(id='water-level-graph'),
        dcc.Graph(id='flow-rate-graph'),
        dcc.Graph(id='voltage-graph')
    ])
])


# Function to perform simulation with adjustable parameters
def simulate_tank(A, beta, t_sim, h_zad, k_p):
    Qd = [0]  # inflow rate
    h = [0.0]  # level of fluid in tank
    t = [0.0]  # times
    u = [k_p]  # control values
    e = [h_zad - h[0]]
    Q_out = [beta * h[0] ** 0.5]  # outflow
    N = int(t_sim / T_p) + 1

    def calculate_U(e_i, e):
        return (k_p * e_i) + (k_p * T_p / T_i) * sum(e)

    def calculate_Qd(u):
        return ((Qd_max - Qd_min) / (U_max - U_min)) * (u - U_min) + Qd_min

    for _ in range(N):
        t.append(t[-1] + T_p)
        e.append(h_zad - h[_])
        U = min(U_max, max(U_min, calculate_U(e[_ + 1], e)))
        u.append(U)
        Qd.append(calculate_Qd(U))
        Q_out.append(beta * h[_] ** 0.5)
        h.append((Qd[_] - beta * h[-1] ** 0.5) * T_p / A + h[-1])

    return t, h, Qd, Q_out, u


# Callback to update the graphs based on slider values
@app.callback(
    [Output('water-level-graph', 'figure'),
     Output('flow-rate-graph', 'figure'),
     Output('voltage-graph', 'figure')],
    [Input('A-slider', 'value'),
     Input('beta-slider', 'value'),
     Input('t_sim-slider', 'value'),
     Input('h_zad-slider', 'value'),
     Input('k_p-slider', 'value')]
)
def update_graphs(A, beta, t_sim, h_zad, k_p):
    # Run simulation with updated parameters
    t, h, Qd, Q_out, u = simulate_tank(A, beta, t_sim, h_zad, k_p)

    # Create figures for each graph
    water_level_fig = pl.line(pd.DataFrame({'Time': t, 'Water Level': h}),
                              x='Time', y='Water Level',
                              title="Water Level Over Time",
                              labels={'Time': 'Time (s)', 'Water Level': 'Water Level (h)'})

    flow_rate_fig = pl.line(pd.DataFrame({
        'Time': t,
        'Q_in': Qd,
        'Q_out': Q_out
    }).melt(id_vars='Time', value_vars=['Q_in', 'Q_out'], var_name='Flow type', value_name='Flow rate'),
                            x='Time', y='Flow rate', color='Flow type',
                            title="Inflow and Outflow Over Time",
                            labels={'Flow rate': 'Flow rate (m³/s)', 'Time': 'Time(s)'}).update_layout(
        legend_title_text='Flow Type')

    voltage_fig = pl.line(pd.DataFrame({'Time': t, 'Voltage': u}),
                          x='Time', y='Voltage',
                          title='Control PI Voltage Over Time',
                          labels={'Voltage': 'Control Voltage(U)', 'Time': 'Time (s)'})

    return water_level_fig, flow_rate_fig, voltage_fig


# Callback to reset sliders to initial values when reset button is clicked
@app.callback(
    [Output('A-slider', 'value'),
     Output('beta-slider', 'value'),
     Output('t_sim-slider', 'value'),
     Output('h_zad-slider', 'value'),
     Output('k_p-slider', 'value')],
    [Input('reset-button', 'n_clicks')]
)
def reset_sliders(n_clicks):
    # Reset each slider to its initial value
    return INITIAL_A, INITIAL_BETA, INITIAL_T_SIM, INITIAL_H_ZAD, INITIAL_K_P


# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)
