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
try:
    config_path = Path(__file__).parent / 'auth_config.yaml'
    with open(config_path, encoding='utf-8') as file:
        config = yaml.safe_load(file)

    authenticator = Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
except FileNotFoundError:
    logger.error(f"Auth config not found: {config_path}")
    raise
except Exception as e:
    logger.error(f"Failed to load auth config: {e}")
    raise

# Configure Streamlit page
st.set_page_config(
    page_title="信号仪表盘",
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
    # TASK #036-REFIX: Use Session State pattern instead of return values
    authenticator.login(location='main', key='Login')

    # Check authentication status from session state
    if st.session_state.get("authentication_status") is False:
        st.error('用户名或密码错误')
        return
    elif st.session_state.get("authentication_status") is None:
        st.warning('请输入账户密码登录')
        return

    # User is authenticated - render dashboard
    # Logout button in sidebar
    authenticator.logout(button_name='登出', location='sidebar', key='Logout')

    # Get user info from session state
    name = st.session_state.get("name", "User")
    username = st.session_state.get("username", "unknown")

    # Title
    st.title("🤖 信号验证仪表盘")
    st.markdown("**Task #019.01**: 可视化交易机器人信号，验证决策质量")
    st.markdown(f"**登录用户**: {name}")
    st.markdown("---")

    # Sidebar: File upload and risk controls
    with st.sidebar:
        st.header("⚙️ 配置面板")

        # Risk Management Controls (TASK #033)
        st.markdown("---")
        st.header("🚨 风险管理")

        # Kill Switch Status
        try:
            kill_switch = get_kill_switch()
            is_active = kill_switch.is_active()

            if is_active:
                st.error("🛑 **紧急制动激活**")
                status = kill_switch.get_status()
                st.write(f"**原因**: {status.get('activation_reason', 'Unknown')}")
                st.write(f"**时间**: {status.get('activation_time', 'Unknown')}")

                # Reset button
                if st.button("🔴 手动复位（管理员）", key="reset_kill_switch"):
                    if kill_switch.reset():
                        st.success("✅ 紧急制动已复位")
                        st.balloons()
                    else:
                        st.error("❌ 紧急制动复位失败")
            else:
                st.success("✅ 紧急制动: 未激活")
                st.markdown(">交易系统正常运行")

        except Exception as e:
            st.warning(f"⚠️ 无法加载紧急制动状态: {str(e)}")

        st.markdown("---")

        # File uploader
        uploaded_file = st.file_uploader(
            "上传交易日志文件",
            type=['log', 'txt'],
            help="选择来自Task #018.01的logs/trading.log"
        )

    # Load and parse log file
    # TASK #037-REFIX: Implement three-tier fallback (uploaded → cache → default)
    try:
        # Initialize log cache in session state if not exists
        if "log_cache" not in st.session_state:
            st.session_state.log_cache = None

        log_content = None

        # 1. Try Uploaded File
        if uploaded_file is not None:
            try:
                # Reset file pointer to beginning (in case it was read before)
                if hasattr(uploaded_file, 'seek'):
                    uploaded_file.seek(0)

                # Read file content
                if hasattr(uploaded_file, 'read'):
                    raw_content = uploaded_file.read()
                    if isinstance(raw_content, bytes):
                        log_content = raw_content.decode('utf-8')
                    else:
                        log_content = raw_content
                else:
                    log_content = uploaded_file.read_text()

                # Cache the content for subsequent reruns
                st.session_state.log_cache = log_content

            except Exception as e:
                # File read failed, fall through to cache/default
                logger.warning(f"Failed to read uploaded file: {e}")
                pass

        # 2. Try Cache
        if log_content is None and st.session_state.log_cache is not None:
            log_content = st.session_state.log_cache
            logger.info("Using cached log content")

        # 3. Try Default Local File (Final Fallback)
        if log_content is None:
            default_path = Path("logs/trading.log")
            if default_path.exists():
                log_content = default_path.read_text(encoding='utf-8')
                st.session_state.log_cache = log_content  # Cache it!
                st.toast("✅ 已加载默认日志文件", icon="📁")
                logger.info(f"Loaded default log file: {default_path}")
            else:
                logger.error("Default log file not found")

        # 4. Final Check
        if not log_content:
            st.error("❌ 无可用日志文件（上传、缓存或默认）。")
            st.info("请上传交易日志文件开始使用。")
            st.stop()

        # Create temporary file
        temp_log = Path("/tmp/trading_temp.log")
        temp_log.write_text(log_content)

        # Parse log
        parser = TradeLogParser(str(temp_log))
        df_events = parser.parse_log()

        if df_events.empty:
            st.error("❌ 日志文件中未找到事件。请检查文件格式。")
            return

        # Get summary
        summary = parser.get_summary()

        # Display summary metrics
        st.header("📊 核心指标概览")

        cols = st.columns(4)
        with cols[0]:
            st.metric(
                "Tick总数",
                summary['total_ticks'],
                help="收到的市场Tick事件"
            )

        with cols[1]:
            st.metric(
                "信号总数",
                summary['total_signals'],
                help="生成的交易信号"
            )

        with cols[2]:
            st.metric(
                "交易总数",
                summary['total_trades'],
                help="执行的订单"
            )

        with cols[3]:
            st.metric(
                "策略胜率",
                f"{summary['win_rate']:.1f}%",
                help="盈利平仓交易的百分比",
                delta=f"{summary['avg_pnl']:+.2f}% 平均"
            )

        # Signal breakdown
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("买入信号", summary['buy_signals'])
        with col2:
            st.metric("卖出信号", summary['sell_signals'])
        with col3:
            st.metric("持仓信号", summary['hold_signals'])

        # Trade status breakdown
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("持仓交易", summary['open_trades'])
        with col2:
            st.metric("平仓交易", summary['closed_trades'])
        with col3:
            avg_pnl_color = "positive" if summary['avg_pnl'] > 0 else "negative"
            st.metric("平均盈亏", f"{summary['avg_pnl']:+.2f}%")

        st.markdown("---")

        # Candlestick chart with signals
        st.header("📈 K线走势图")

        # Get unique symbols
        ticks = df_events[df_events['event_type'] == 'TICK'].copy()
        available_symbols = ticks['symbol'].unique() if not ticks.empty else []

        if len(available_symbols) > 0:
            selected_symbol = st.selectbox(
                "选择交易品种",
                available_symbols,
                index=0,
                help="选择要可视化的品种"
            )

            timeframe = st.select_slider(
                "时间周期",
                options=['15min', '30min', '1H', '4H', '1D'],
                value='1H',
                help="K线聚合时间周期"
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
                            name='买入信号',
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
                    yaxis_title="价格",
                    xaxis_title="时间",
                    template="plotly_white",
                    height=600,
                    hovermode='x unified'
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"无{selected_symbol}可用的OHLC数据")
        else:
            st.warning("日志文件中未找到Tick数据")

        st.markdown("---")

        # Trades table
        st.header("📋 交易历史记录")

        trades = parser.extract_trades()
        if not trades.empty:
            # Format for display
            trades_display = trades.copy()

            if 'entry_time' in trades_display.columns:
                trades_display['entry_time'] = trades_display['entry_time'].dt.strftime('%H:%M:%S')
            if 'exit_time' in trades_display.columns:
                trades_display['exit_time'] = trades_display['exit_time'].dt.strftime('%H:%M:%S')
            if 'entry_price' in trades_display.columns:
                fmt_price = lambda x: f"{x:.5f}"
                trades_display['entry_price'] = trades_display['entry_price'].apply(fmt_price)
            if 'exit_price' in trades_display.columns:
                fmt_exit = lambda x: f"{x:.5f}" if pd.notna(x) else "-"
                trades_display['exit_price'] = trades_display['exit_price'].apply(fmt_exit)
            if 'pnl' in trades_display.columns:
                fmt_pnl = lambda x: f"{x:+.2f}%" if pd.notna(x) else "-"
                trades_display['pnl'] = trades_display['pnl'].apply(fmt_pnl)

            st.dataframe(trades_display, use_container_width=True, hide_index=True)
        else:
            st.info("未找到完成的交易")

        st.markdown("---")

        # Event timeline
        st.header("📅 事件追踪链路")

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
        st.error(f"❌ 处理日志文件出错: {str(e)}")
        logger.exception("Dashboard error")
        import traceback
        st.write(traceback.format_exc())


if __name__ == "__main__":
    main()
