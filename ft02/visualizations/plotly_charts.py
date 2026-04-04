import json
import plotly.graph_objects as go

def generate_interactive_charts(business: dict) -> dict:
    charts = {}
    
    # ── 1. Sales Chart ──
    sales_data = business.get("sales_data", {})
    monthly_sales = sales_data.get("monthly_sales", [])
    if monthly_sales:
        x_vals = list(range(1, len(monthly_sales) + 1))
        y_vals = [s / 100000 for s in monthly_sales]
        fig_sales = go.Figure()
        fig_sales.add_trace(go.Scatter(
            x=x_vals, y=y_vals, mode='lines', 
            name='Monthly Sales', line=dict(color='#2196F3', width=2),
            fill='tozeroy', fillcolor='rgba(33, 150, 243, 0.1)',
            hovertemplate='Month: %{x}<br>Sales: Rs. %{y:.2f}L<extra></extra>'
        ))
        
        spikes = sales_data.get("sudden_sales_spikes", [])
        if spikes:
            spike_x = [m + 1 for m in spikes if m < len(monthly_sales)]
            spike_y = [monthly_sales[m] / 100000 for m in spikes if m < len(monthly_sales)]
            fig_sales.add_trace(go.Scatter(
                x=spike_x, y=spike_y, mode='markers', 
                marker=dict(color='#F44336', size=12, line=dict(color='white', width=2)),
                name='Anomalous Spike', hovertemplate='Spike at Month %{x}<extra></extra>'
            ))
        fig_sales.update_layout(
            title="Monthly Sales Trend", 
            xaxis_title="Month", 
            yaxis_title="Sales (Rs. Lakhs)", 
            margin=dict(l=40, r=40, b=40, t=40),
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter, sans-serif")
        )
        charts["sales"] = json.loads(fig_sales.to_json())

    # ── 2. Turnover Chart (Bar Chart side by side substitute) ──
    if monthly_sales:
        fig_turnover = go.Figure()
        fig_turnover.add_trace(go.Bar(
            x=x_vals, y=y_vals, marker_color='#2196F3', name='Revenue',
            hovertemplate='Month %{x}<br>Rs. %{y:.2f}L<extra></extra>'
        ))
        fig_turnover.update_layout(
            title="Monthly Revenue Bars", 
            xaxis_title="Month",
            yaxis_title="Revenue (Rs. Lakhs)",
            margin=dict(l=40, r=40, b=40, t=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter, sans-serif")
        )
        charts["turnover"] = json.loads(fig_turnover.to_json())

    # ── 3. Risk Radar ──
    features = business.get("_credit_features", {})
    if features:
        dimensions = {
            "GST Compliance": features.get("gst_compliance_score", 0.5),
            "Financial Stability": features.get("turnover_stability", 0.5),
            "Vendor Diversification": features.get("vendor_diversification", 0.5),
            "Repayment Reliability": features.get("repayment_ratio", 0.5),
            "Sales Stability": 1.0 - min(features.get("sales_volatility", 0.5), 1.0),
            "Sector Safety": 1.0 - features.get("sector_risk", 0.5),
        }
        categories = list(dimensions.keys())
        values = list(dimensions.values())
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself', fillcolor='rgba(33, 150, 243, 0.2)',
            line=dict(color='#2196F3', width=2),
            marker=dict(size=8),
            name="Business"
        ))
        fig_radar.update_layout(
            title="Risk Assessment Radar",
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=False,
            margin=dict(l=40, r=40, b=40, t=60),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter, sans-serif")
        )
        charts["radar"] = json.loads(fig_radar.to_json())

    # ── 4. Credit Gauge ──
    score = business.get("credit_score", 300)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Credit Score", 'font': {'size': 16}},
        gauge={
            'axis': {'range': [300, 900]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [300, 500], 'color': "rgba(244, 67, 54, 0.3)"},
                {'range': [500, 700], 'color': "rgba(255, 152, 0, 0.3)"},
                {'range': [700, 900], 'color': "rgba(76, 175, 80, 0.3)"}
            ],
            'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': score}
        }
    ))
    fig_gauge.update_layout(
        margin=dict(l=20, r=20, b=20, t=40),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif")
    )
    charts["gauge"] = json.loads(fig_gauge.to_json())

    # ── 5. Fraud Network ──
    network_data = business.get("network_data", {})
    edges = network_data.get("edges", [])
    circular = network_data.get("circular_trades", [])
    if edges:
        import networkx as nx
        G = nx.DiGraph()
        for e in edges:
            G.add_edge(e["source"], e["target"], weight=e.get("weight", 1), edge_type=e.get("type", "unknown"))
            
        try:
            pos = nx.spring_layout(G, seed=42)
        except Exception:
            pos = nx.circular_layout(G)
        
        edge_x, edge_y = [], []
        circ_x, circ_y = [], []
        mid_x, mid_y, mid_text = [], [], []
        
        for u, v, data in G.edges(data=True):
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            if data.get("edge_type") == "circular":
                circ_x.extend([x0, x1, None])
                circ_y.extend([y0, y1, None])
                amt = 0
                for ct in circular:
                    if u in ct.get("path", []) and v in ct.get("path", []):
                        amt = ct.get("rotated_funds", 0)
                mid_x.append((x0 + x1) / 2)
                mid_y.append((y0 + y1) / 2)
                mid_text.append(f"<b>Rs.{amt:,} Loop</b>")
            else:
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
        norm_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color='#aaa'), hoverinfo='none', mode='lines')
        circ_trace = go.Scatter(x=circ_x, y=circ_y, line=dict(width=3.5, color='#F44336'), hoverinfo='none', mode='lines')
        label_trace = go.Scatter(x=mid_x, y=mid_y, mode='text', text=mid_text, textposition="top center",
                                 textfont=dict(color='#F44336', size=11, family="Inter, sans-serif"))

        node_x, node_y, node_text, node_color = [], [], [], []
        main_gstin = business["business_identity"]["gstin"]
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            is_circular = any(node in ct.get("path", []) for ct in circular)
            if node == main_gstin:
                node_color.append('#2196F3') # Blue for target
                node_text.append(f"Target: {node}")
            elif is_circular:
                node_color.append('#F44336') # Red for fraud ring participants
                node_text.append(f"Ring Participant: {node}")
            else:
                node_color.append('#4CAF50' if str(node).startswith('V') else '#FF9800')
                node_text.append(f"Entity: {node}")

        node_trace = go.Scatter(
            x=node_x, y=node_y, mode='markers', hoverinfo='text', text=node_text,
            marker=dict(showscale=False, color=node_color, size=15, line=dict(color='white', width=1.5)))

        fig_network = go.Figure(data=[norm_trace, circ_trace, label_trace, node_trace])
        fig_network.update_layout(
            title="Vendor & Client Fraud Topology",
            showlegend=False, hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        charts["network"] = json.loads(fig_network.to_json())

    return charts
