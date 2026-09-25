import math
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="Belt Drive Transmission Design Checker",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Belt Drive Transmission Design Checker")
st.caption(
    "Flat Belt / V-Belt — angle of lap, belt length, speed ratio "
    "and maximum power before slipping"
)

st.subheader("Input Parameters")
c1, c2 = st.columns(2)

with c1:
    belt_type = st.selectbox("Belt Type", ["Flat Belt", "V-Belt"])
    D1 = st.number_input(
        "Driver Pulley Diameter D₁ (mm)",
        min_value=0.01, value=200.0, step=1.0
    )
    D2 = st.number_input(
        "Follower Pulley Diameter D₂ (mm)",
        min_value=0.01, value=400.0, step=1.0
    )
    N1 = st.number_input(
        "Driver Speed N₁ (RPM)",
        min_value=0.01, value=1440.0, step=10.0
    )
    C = st.number_input(
        "Centre Distance C (mm)",
        min_value=0.01, value=1000.0, step=10.0
    )

with c2:
    mu = st.number_input(
        "Coefficient of Friction μ",
        min_value=0.0001, value=0.30, step=0.01, format="%.4f"
    )
    T = st.number_input(
        "Maximum Belt Tension T (N)",
        min_value=0.01, value=1000.0, step=10.0
    )
    m = st.number_input(
        "Belt Mass per Unit Length m (kg/m)",
        min_value=0.0, value=0.50, step=0.05
    )
    groove_angle = st.number_input(
        "V-Belt Groove Angle (degrees)",
        min_value=0.1, max_value=179.9, value=40.0, step=1.0,
        disabled=(belt_type == "Flat Belt")
    )


def calculate_belt_drive(D1, D2, N1, C, mu, T, m, groove_angle, belt_type):
    if D1 <= 0 or D2 <= 0 or N1 <= 0 or C <= 0:
        raise ValueError(
            "Pulley diameters, RPM and centre distance must be positive."
        )
    if mu <= 0:
        raise ValueError("Coefficient of friction must be positive.")
    if T <= 0:
        raise ValueError("Maximum belt tension must be positive.")
    if m < 0:
        raise ValueError("Belt mass per unit length cannot be negative.")
    if belt_type == "V-Belt" and not (0 < groove_angle < 180):
        raise ValueError(
            "V-Belt groove angle must be between 0° and 180°."
        )

    x = (D2 - D1) / (2 * C)
    if abs(x) > 1:
        raise ValueError(
            "Invalid geometry: |(D₂ − D₁)/(2C)| must be ≤ 1."
        )

    theta = math.pi - 2 * math.asin(x)
    L = (
        math.pi / 2 * (D1 + D2)
        + 2 * C
        + (D2 - D1) ** 2 / (4 * C)
    )
    speed_ratio = D1 / D2
    N2 = N1 * D1 / D2
    v = math.pi * (D1 / 1000) * N1 / 60
    Tc = m * v ** 2

    if T <= Tc:
        raise ValueError(
            f"Maximum belt tension T = {T:.3f} N must be greater "
            f"than centrifugal tension Tc = {Tc:.3f} N."
        )

    if belt_type == "Flat Belt":
        tension_ratio = math.exp(mu * theta)
    else:
        tension_ratio = math.exp(
            (mu * theta) / math.sin(math.radians(groove_angle / 2))
        )

    T1 = T - Tc
    T2 = T1 / tension_ratio
    power_kw = (T1 - T2) * v / 1000

    return theta, L, speed_ratio, N2, v, Tc, T1, T2, power_kw


def make_3d_belt_figure(D1, D2, C, belt_type):
    """Create an interactive 3D schematic of two pulleys and an open belt."""

    # Scale all dimensions to metres for a visually consistent 3D scene.
    r1 = max(D1 / 2000.0, 0.03)
    r2 = max(D2 / 2000.0, 0.03)
    center_distance = max(C / 1000.0, 0.1)

    # Keep the displayed pulley sizes inside a practical viewing range.
    scale = min(1.0, center_distance / max(3.0 * max(r1, r2), 0.1))
    r1 *= scale
    r2 *= scale
    Cvis = center_distance

    # Pulley centers in the X direction; pulley axis is Y.
    x1 = -Cvis / 2
    x2 = Cvis / 2

    fig = go.Figure()

    def add_pulley(cx, radius, label):
        n = 48
        rings = 16
        theta = [2 * math.pi * i / n for i in range(n)]
        yvals = [-0.12 + 0.24 * j / (rings - 1) for j in range(rings)]

        xs, ys, zs = [], [], []
        for y in yvals:
            for a in theta:
                xs.append(cx + radius * math.cos(a))
                ys.append(y)
                zs.append(radius * math.sin(a))

        ii, jj, kk = [], [], []
        for j in range(rings - 1):
            for i in range(n):
                a = j * n + i
                b = j * n + (i + 1) % n
                c = (j + 1) * n + (i + 1) % n
                d = (j + 1) * n + i
                ii.extend([a, a])
                jj.extend([b, c])
                kk.extend([c, d])

        fig.add_trace(go.Mesh3d(
            x=xs, y=ys, z=zs,
            i=ii, j=jj, k=kk,
            opacity=0.92,
            flatshading=False,
            color="#777777",
            name=label,
            hoverinfo="skip",
            showscale=False
        ))

        # Hub
        hub_r = radius * 0.22
        hub_x, hub_y, hub_z = [], [], []
        for y in [-0.17, 0.17]:
            for a in theta:
                hub_x.append(cx + hub_r * math.cos(a))
                hub_y.append(y)
                hub_z.append(hub_r * math.sin(a))

        fig.add_trace(go.Mesh3d(
            x=hub_x, y=hub_y, z=hub_z,
            alphahull=0,
            opacity=1.0,
            color="#444444",
            name=f"{label} hub",
            hoverinfo="skip",
            showscale=False
        ))

        fig.add_trace(go.Scatter3d(
            x=[cx], y=[0], z=[0],
            mode="text",
            text=[label],
            textposition="top center",
            showlegend=False,
            hoverinfo="skip"
        ))

    add_pulley(x1, r1, "Driver")
    add_pulley(x2, r2, "Follower")

    # Open-belt path in the X-Z plane.  Tangent points are computed
    # for the two pulley radii, giving a more realistic schematic.
    dr = r2 - r1
    if abs(dr) < Cvis:
        alpha = math.asin(dr / Cvis)
    else:
        alpha = 0.0

    # Tangent points for an open belt.
    p1_top = (x1 + r1 * math.sin(alpha), r1 * math.cos(alpha))
    p2_top = (x2 + r2 * math.sin(alpha), r2 * math.cos(alpha))
    p1_bot = (x1 - r1 * math.sin(alpha), -r1 * math.cos(alpha))
    p2_bot = (x2 - r2 * math.sin(alpha), -r2 * math.cos(alpha))

    # Straight upper and lower runs.
    belt_x = [p1_top[0], p2_top[0]]
    belt_z = [p1_top[1], p2_top[1]]
    belt_y = [0.19, 0.19]

    fig.add_trace(go.Scatter3d(
        x=belt_x, y=belt_y, z=belt_z,
        mode="lines",
        line=dict(color="#222222", width=8),
        name="Belt",
        hoverinfo="skip"
    ))

    fig.add_trace(go.Scatter3d(
        x=[p1_bot[0], p2_bot[0]],
        y=[-0.19, -0.19],
        z=[p1_bot[1], p2_bot[1]],
        mode="lines",
        line=dict(color="#222222", width=8),
        showlegend=False,
        hoverinfo="skip"
    ))

    # Wrap around driver.
    a_start = math.atan2(p1_top[1], p1_top[0] - x1)
    a_end = math.atan2(p1_bot[1], p1_bot[0] - x1)
    if a_end > a_start:
        a_end -= 2 * math.pi
    a = [a_start + (a_end - a_start) * i / 60 for i in range(61)]

    fig.add_trace(go.Scatter3d(
        x=[x1 + r1 * math.cos(t) for t in a],
        y=[0.19] * len(a),
        z=[r1 * math.sin(t) for t in a],
        mode="lines",
        line=dict(color="#222222", width=8),
        showlegend=False,
        hoverinfo="skip"
    ))

    # Wrap around follower.
    a_start = math.atan2(p2_top[1], p2_top[0] - x2)
    a_end = math.atan2(p2_bot[1], p2_bot[0] - x2)
    if a_end < a_start:
        a_end += 2 * math.pi
    a = [a_start + (a_end - a_start) * i / 60 for i in range(61)]

    fig.add_trace(go.Scatter3d(
        x=[x2 + r2 * math.cos(t) for t in a],
        y=[-0.19] * len(a),
        z=[r2 * math.sin(t) for t in a],
        mode="lines",
        line=dict(color="#222222", width=8),
        showlegend=False,
        hoverinfo="skip"
    ))

    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            xaxis=dict(title="Centre distance direction", showgrid=True),
            yaxis=dict(title="Pulley width", showgrid=True),
            zaxis=dict(title="Pulley radius direction", showgrid=True),
            aspectmode="data",
            camera=dict(eye=dict(x=1.7, y=1.4, z=1.25))
        ),
        legend=dict(orientation="h", y=1.02, x=0)
    )

    fig.add_annotation(
        text=f"{belt_type} • D₁={D1:.0f} mm • D₂={D2:.0f} mm • C={C:.0f} mm",
        xref="paper", yref="paper", x=0.5, y=0.01,
        showarrow=False
    )

    return fig


if st.button("Calculate", type="primary", use_container_width=True):
    try:
        (
            theta, L, speed_ratio, N2, v, Tc,
            T1, T2, power_kw
        ) = calculate_belt_drive(
            D1, D2, N1, C, mu, T, m, groove_angle, belt_type
        )

        st.success("Calculation completed successfully.")

        st.subheader("Results")
        st.table([
            {"Parameter": "Angle of Lap", "Value": f"{math.degrees(theta):.3f}°"},
            {"Parameter": "Belt Length", "Value": f"{L:.3f} mm"},
            {"Parameter": "Speed Ratio (N₂/N₁)", "Value": f"{speed_ratio:.5f}"},
            {"Parameter": "Follower Speed N₂", "Value": f"{N2:.3f} RPM"},
            {"Parameter": "Belt Speed", "Value": f"{v:.3f} m/s"},
            {"Parameter": "Centrifugal Tension", "Value": f"{Tc:.3f} N"},
            {"Parameter": "Tight-Side Effective Tension", "Value": f"{T1:.3f} N"},
            {"Parameter": "Slack-Side Tension", "Value": f"{T2:.3f} N"},
            {"Parameter": "Maximum Power Before Slip", "Value": f"{power_kw:.3f} kW"},
        ])

        st.subheader("Interactive 3D Belt & Pulley Diagram")
        st.plotly_chart(
            make_3d_belt_figure(D1, D2, C, belt_type),
            use_container_width=True,
            config={
                "displayModeBar": True,
                "scrollZoom": True,
                "responsive": True
            }
        )

        st.subheader("Formulas Used")
        formulas = [
            "θ = π − 2 sin⁻¹((D₂ − D₁)/(2C))",
            "L = π/2(D₁ + D₂) + 2C + (D₂ − D₁)²/(4C)",
            "N₂ = N₁ × D₁ / D₂",
            "v = πD₁N₁ / 60  (D₁ in metres)",
            "Tc = mv²",
        ]

        if belt_type == "Flat Belt":
            formulas.append("T₁/T₂ = e^(μθ)")
        else:
            formulas.append(
                "T₁/T₂ = e^((μθ)/sin(groove angle/2))"
            )

        formulas.append("Power = (T₁ − T₂)v / 1000  kW")

        for formula in formulas:
            st.code(formula)

    except ValueError as e:
        st.error(str(e))
else:
    st.info("Enter the belt-drive parameters and click Calculate.")
