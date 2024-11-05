import plotly.express as pl
import pandas as pd
from dash import Dash, dcc, html

# Starting parameters
A = 1.5  # cross-section of the tank
beta = 0.035  # beta parameter
t_sim = 3600.0  # simulation time
T_p = 0.1  # sampling time
T_i = 0.5  # doubling time
U_pi = 1  # control quantity for PI controller
U_min = 0  # bottom bound
U_max = 10  # upper bound
Qd_max = 0.05  # flow upper bound
Qd_min = 0  # flow bottom bound
k_p = 0.02  # regulator gain
h_zad = 1.25

Qd = [0]  # inflow rate
h = [0.0]  # level of fluid in tank
t = [0.0]  # times
u = [k_p]  # control values
e = [h_zad - h[0]]

Q_out = [beta * h[0] ** 0.5]  # outflow
N = int(t_sim / T_p) + 1


def calculate_U(e_i, e):
    u = (k_p * e_i) + (k_p * T_p / T_i) * sum(e)
    return u


def calculate_Qd(u):
    return ((Qd_max - Qd_min) / (U_max - U_min)) * (u - U_min) + Qd_min


for _ in range(N):
    t.append(t[-1] + T_p)

    e.append(h_zad - h[_])
    U = min(U_max, max(U_min, calculate_U(e[_ + 1], e)))  # Current voltage
    u.append(U)
    Qd.append(calculate_Qd(U))
    Q_out.append(beta * h[_] ** 0.5)
    h.append((Qd[_] - beta * h[-1] ** 0.5) * T_p / A + h[-1])


print(h[-10: -1])

# Define app Dash
app = Dash(__name__)

# App layout
app.layout = html.Div(children=[
    html.H1(children='Tank Simulation'),
    html.Div(style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}, children=[
        # plot h(t)
        dcc.Graph(
            id='water-level-graph',
            style={'height': '800px', 'width': '100%'},
            figure=pl.line(pd.DataFrame({'Time': t, 'Water Level': h}),
                           x='Time', y='Water Level',
                           title="Water Level Over Time",
                           labels={'Time': 'Time (s)', 'Water Level': 'Water Level (h)'})
        ),
        # plot Q_d(t) and Q_out(t)
        dcc.Graph(
            id='flow-rate-graph',
            style={'height': '800px', 'width': '100%'},
            figure=pl.line(pd.DataFrame({
                'Time': t,
                'Q_in': Qd,
                'Q_out': Q_out
            }).melt(id_vars='Time', value_vars=['Q_in', 'Q_out'], var_name='Flow type', value_name='Flow rate'),
                x='Time', y='Flow rate', color='Flow type',
                title="Inflow and Outflow Over Time",
                labels={'Flow rate': 'Flow rate (m³/s)', 'Time': 'Time(s)'})
        ),
        # plot U_pi(t)
        dcc.Graph(
            id='voltage-graph',
            style={'height': '800px', 'width': '100%'},
            figure=pl.line(pd.DataFrame({'Time': t, 'Voltage': u}),
                           x='Time', y='Voltage',
                           title='Control PI Voltage Over Time',
                           labels={'Voltage': 'Control Voltage(U)', 'Time': 'Time (s)'})
        )
    ])
])

# Start server
if __name__ == '__main__':
    app.run_server(debug=True)
