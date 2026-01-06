#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signal Verification Dashboard & Risk Management Control (Streamlit)

TASK #019.01: Signal Verification Dashboard
TASK #033: Web Dashboard & DingTalk ActionCard Integration

Visualize trading bot signals, performance metrics, and provide
real-time risk management controls including Kill Switch activation.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import logging
import yaml
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
from streamlit_authenticator import Authenticate

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.reporting.log_parser import TradeLogParser
from src.risk import get_kill_switch
from src.dashboard import send_risk_alert, send_kill_switch_alert
from src.config import DASHBOARD_PUBLIC_URL

logger = logging.getLogger(__name__)

# Load authentication configuration (TASK #036)
config_path = Path(__file__).parent / 'auth_config.yaml'
with open(config_path) as file:
    config = yaml.safe_load(file)

authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Configure Streamlit page
st.set_page_config(
    page_title="Signal Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .metric-label {
        color: #808080;
        font-size: 14px;
        font-weight: 600;
    }
    .metric-value {
        color: #1f77b4;
        font-size: 32px;
        font-weight: 700;
    }
    .positive {
        color: #26a65b;
    }
    .negative {
        color: #e74c3c;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main Streamlit application"""

    # Authentication (TASK #036: Application-Layer Authentication)
    # TASK #036-FIX: Fixed API signature - location must be keyword argument
    name, authentication_status, username = authenticator.login(location='main', key='Login')

    if authentication_status == False:
        st.error('Username/password is incorrect')
        return
    elif authentication_status == None:
        st.warning('Please enter your username and password')
        return

    # Logout button in sidebar
    authenticator.logout(button_name='Logout', location='sidebar', key='Logout')

    # Title
    st.title("🤖 Signal Verification Dashboard")
    st.markdown("**Task #019.01**: Visualize trading bot signals and verify decision quality")
    st.markdown(f"**Logged in as**: {name}")
    st.markdown("---")

    # Sidebar: File upload and risk controls
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Risk Management Controls (TASK #033)
        st.markdown("---")
        st.header("🚨 Risk Management")

        # Kill Switch Status
        try:
            kill_switch = get_kill_switch()
            is_active = kill_switch.is_active()

            if is_active:
                st.error("🛑 **KILL SWITCH ACTIVE**")
                status = kill_switch.get_status()
                st.write(f"**Reason**: {status.get('activation_reason', 'Unknown')}")
                st.write(f"**Time**: {status.get('activation_time', 'Unknown')}")

                # Reset button
                if st.button("🔴 Manual Reset (Admin)", key="reset_kill_switch"):
                    if kill_switch.reset():
                        st.success("✅ Kill switch reset successfully")
                        st.balloons()
                    else:
                        st.error("❌ Failed to reset kill switch")
            else:
                st.success("✅ Kill Switch: INACTIVE")
                st.markdown(">Trading system operational")

        except Exception as e:
            st.warning(f"⚠️ Could not load kill switch status: {str(e)}")

        st.markdown("---")

        # File uploader
        uploaded_file = st.file_uploader(
            "Upload Trading Log File",
            type=['log', 'txt'],
            help="Select logs/trading.log from Task #018.01"
        )

        if uploaded_file is None:
            # Try to load default file
            default_log = Path("logs/trading.log")
            if default_log.exists():
                with open(default_log, 'rb') as f:
                    uploaded_file = f
                st.success(f"✅ Loaded default: {default_log}")
            else:
                st.warning("📁 No log file loaded. Upload one to begin.")
                return

    # Load and parse log file
    try:
        # Save uploaded file temporarily
        if hasattr(uploaded_file, 'read'):
            log_content = uploaded_file.read()
            if isinstance(log_content, bytes):
                log_content = log_content.decode('utf-8')
        else:
            log_content = uploaded_file.read_text()

        # Create temporary file
        temp_log = Path("/tmp/trading_temp.log")
        temp_log.write_text(log_content)

        # Parse log
        parser = TradeLogParser(str(temp_log))
        df_events = parser.parse_log()

        if df_events.empty:
            st.error("❌ No events found in log file. Please check the file format.")
            return

        # Get summary
        summary = parser.get_summary()

        # Display summary metrics
        st.header("📊 Summary Metrics")

        cols = st.columns(4)
        with cols[0]:
            st.metric(
                "Total Ticks",
                summary['total_ticks'],
                help="Market tick events received"
            )

        with cols[1]:
            st.metric(
                "Total Signals",
                summary['total_signals'],
                help="Trading signals generated"
            )

        with cols[2]:
            st.metric(
                "Total Trades",
                summary['total_trades'],
                help="Orders executed"
            )

        with cols[3]:
            st.metric(
                "Win Rate",
                f"{summary['win_rate']:.1f}%",
                help="% of profitable closed trades",
                delta=f"{summary['avg_pnl']:+.2f}% avg"
            )

        # Signal breakdown
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Buy Signals", summary['buy_signals'])
        with col2:
            st.metric("Sell Signals", summary['sell_signals'])
        with col3:
            st.metric("Hold Signals", summary['hold_signals'])

        # Trade status breakdown
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Open Trades", summary['open_trades'])
        with col2:
            st.metric("Closed Trades", summary['closed_trades'])
        with col3:
            avg_pnl_color = "positive" if summary['avg_pnl'] > 0 else "negative"
            st.metric("Avg P&L", f"{summary['avg_pnl']:+.2f}%")

        st.markdown("---")

        # Candlestick chart with signals
        st.header("📈 Candlestick Chart")

        # Get unique symbols
        ticks = df_events[df_events['event_type'] == 'TICK'].copy()
        available_symbols = ticks['symbol'].unique() if not ticks.empty else []

        if len(available_symbols) > 0:
            selected_symbol = st.selectbox(
                "Select Symbol",
                available_symbols,
                index=0,
                help="Choose symbol to visualize"
            )

            timeframe = st.select_slider(
                "Timeframe",
                options=['15min', '30min', '1H', '4H', '1D'],
                value='1H',
                help="Candlestick aggregation period"
            )

            # Generate OHLC
            ohlc = parser.generate_ohlc(symbol=selected_symbol, timeframe=timeframe)

            if not ohlc.empty:
                # Get signals for this symbol
                signals = df_events[df_events['symbol'] == selected_symbol].copy()
                buy_signals = signals[signals['event_type'] == 'PRED']
                buy_signals = buy_signals[buy_signals['signal'] == 1]

                # Create candlestick chart
                fig = go.Figure(data=[go.Candlestick(
                    x=ohlc.index,
                    open=ohlc['open'],
                    high=ohlc['high'],
                    low=ohlc['low'],
                    close=ohlc['close'],
                    name='OHLC'
                )])

                # Add buy signal markers
                if not buy_signals.empty:
                    buy_ticks = buy_signals[buy_signals['timestamp'].isin(ticks['timestamp'])]
                    if not buy_ticks.empty:
                        fig.add_trace(go.Scatter(
                            x=buy_ticks['timestamp'],
                            y=buy_ticks['price'],
                            mode='markers',
                            name='Buy Signal',
                            marker=dict(
                                size=10,
                                color='blue',
                                symbol='diamond',
                                line=dict(width=2, color='darkblue')
                            )
                        ))

                # Customize layout
                fig.update_layout(
                    title=f"{selected_symbol} @ {timeframe}",
                    yaxis_title="Price",
                    xaxis_title="Time",
                    template="plotly_white",
                    height=600,
                    hovermode='x unified'
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No OHLC data available for {selected_symbol}")
        else:
            st.warning("No tick data found in log file")

        st.markdown("---")

        # Trades table
        st.header("📋 Trade History")

        trades = parser.extract_trades()
        if not trades.empty:
            # Format for display
            trades_display = trades.copy()

            if 'entry_time' in trades_display.columns:
                trades_display['entry_time'] = trades_display['entry_time'].dt.strftime('%H:%M:%S')
            if 'exit_time' in trades_display.columns:
                trades_display['exit_time'] = trades_display['exit_time'].dt.strftime('%H:%M:%S')
            if 'entry_price' in trades_display.columns:
                trades_display['entry_price'] = trades_display['entry_price'].apply(lambda x: f"{x:.5f}")
            if 'exit_price' in trades_display.columns:
                trades_display['exit_price'] = trades_display['exit_price'].apply(lambda x: f"{x:.5f}" if pd.notna(x) else "-")
            if 'pnl' in trades_display.columns:
                trades_display['pnl'] = trades_display['pnl'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "-")

            st.dataframe(trades_display, use_container_width=True, hide_index=True)
        else:
            st.info("No completed trades found")

        st.markdown("---")

        # Event timeline
        st.header("📅 Event Timeline")

        events_display = df_events.copy()
        events_display['timestamp'] = events_display['timestamp'].dt.strftime('%H:%M:%S')

        # Select columns to display
        display_cols = ['timestamp', 'event_type', 'symbol']
        if 'price' in events_display.columns:
            display_cols.append('price')
        if 'signal_name' in events_display.columns:
            display_cols.append('signal_name')
        if 'side' in events_display.columns:
            display_cols.append('side')

        display_cols = [c for c in display_cols if c in events_display.columns]
        events_display = events_display[display_cols]

        st.dataframe(events_display, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"❌ Error processing log file: {str(e)}")
        logger.exception("Dashboard error")
        import traceback
        st.write(traceback.format_exc())


if __name__ == "__main__":
    main()
