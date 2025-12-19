"""
pytest 配置文件
定义全局 fixtures 和测试配置
"""

import os
import sys
from pathlib import Path

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))


# ==================== 测试数据 Fixtures ====================

@pytest.fixture
def sample_price_data():
    """生成样本价格数据"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    np.random.seed(42)

    data = {
        'time': dates,
        'open': 100 + np.random.randn(len(dates)).cumsum(),
        'high': 102 + np.random.randn(len(dates)).cumsum(),
        'low': 98 + np.random.randn(len(dates)).cumsum(),
        'close': 100 + np.random.randn(len(dates)).cumsum(),
        'volume': np.random.randint(1000000, 10000000, len(dates)),
        'tick_volume': np.random.randint(10000, 100000, len(dates)),
    }

    df = pd.DataFrame(data)

    # 确保 high >= low, high >= open/close, low <= open/close
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)

    return df


@pytest.fixture
def sample_news_data():
    """生成样本新闻数据"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    np.random.seed(42)

    # 每天 1-3 条新闻
    news_data = []
    for date in dates:
        num_news = np.random.randint(1, 4)
        for _ in range(num_news):
            news_data.append({
                'published_date': date,
                'title': f'Sample news on {date.date()}',
                'summary': 'This is a sample news summary for testing purposes.',
                'sentiment_score': np.random.uniform(-1, 1),
                'sentiment_label': np.random.choice(['positive', 'negative', 'neutral']),
            })

    return pd.DataFrame(news_data)


@pytest.fixture
def sample_features_data(sample_price_data):
    """生成样本特征数据 (包含基础特征)"""
    df = sample_price_data.copy()

    # 添加一些基础特征
    df['return'] = df['close'].pct_change()
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    df['ema_5'] = df['close'].ewm(span=5, adjust=False).mean()
    df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['sma_5'] = df['close'].rolling(window=5).mean()
    df['sma_20'] = df['close'].rolling(window=20).mean()

    return df


@pytest.fixture
def sample_labels_data():
    """生成样本标签数据"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    np.random.seed(42)

    data = {
        'entry_time': dates,
        'exit_time': dates + timedelta(days=5),
        'label': np.random.choice([-1, 0, 1], size=len(dates), p=[0.3, 0.2, 0.5]),
        'return': np.random.randn(len(dates)) * 0.02,
        'holding_period': np.random.randint(1, 10, len(dates)),
        'triggered_barrier': np.random.choice(['upper', 'lower', 'vertical'], len(dates)),
    }

    return pd.DataFrame(data)


# ==================== 路径 Fixtures ====================

@pytest.fixture
def temp_data_lake(tmp_path):
    """创建临时数据湖目录结构"""
    data_lake = tmp_path / 'data_lake'

    # 创建目录结构
    (data_lake / 'raw' / 'market_data').mkdir(parents=True)
    (data_lake / 'raw' / 'news').mkdir(parents=True)
    (data_lake / 'processed' / 'features').mkdir(parents=True)
    (data_lake / 'processed' / 'labels').mkdir(parents=True)

    return data_lake


@pytest.fixture
def project_root():
    """返回项目根目录路径"""
    return Path(__file__).parent.parent


# ==================== 配置 Fixtures ====================

@pytest.fixture
def sample_config():
    """返回样本配置字典"""
    return {
        'data_lake_path': '/tmp/test_data_lake',
        'assets': [
            {
                'symbol': 'AAPL.US',
                'name': 'Apple Inc.',
                'type': 'stock',
                'exchange': 'NASDAQ',
            },
            {
                'symbol': 'BTC-USD',
                'name': 'Bitcoin',
                'type': 'crypto',
                'exchange': 'COINBASE',
            },
        ],
        'features': {
            'basic': {
                'returns': True,
                'moving_averages': [5, 20, 60],
                'rsi': [14],
                'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            },
            'advanced': {
                'fractional_diff': True,
                'rolling_stats': True,
                'sentiment_momentum': True,
            },
        },
        'labeling': {
            'method': 'triple_barrier',
            'upper_barrier': 0.02,
            'lower_barrier': -0.02,
            'max_holding_period': 5,
        },
        'monitoring': {
            'dq_score_weights': {
                'completeness': 0.30,
                'accuracy': 0.25,
                'consistency': 0.20,
                'timeliness': 0.15,
                'validity': 0.10,
            },
            'dq_score_warning': 70,
            'dq_score_critical': 50,
        },
    }


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_yfinance_ticker(monkeypatch, sample_price_data):
    """Mock yfinance Ticker 对象"""
    class MockTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, period=None, start=None, end=None, interval='1d'):
            df = sample_price_data.copy()
            df.index = df['time']
            df = df.drop(columns=['time'])
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Tick_volume']
            return df

    def mock_ticker_init(symbol):
        return MockTicker(symbol)

    # 如果 yfinance 可用，则 mock 它
    try:
        import yfinance as yf
        monkeypatch.setattr(yf, 'Ticker', mock_ticker_init)
    except ImportError:
        pass

    return MockTicker


# ==================== 测试标记 ====================

def pytest_configure(config):
    """配置自定义标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "slow: 运行时间较长的测试"
    )
    config.addinivalue_line(
        "markers", "requires_data: 需要真实数据的测试"
    )
