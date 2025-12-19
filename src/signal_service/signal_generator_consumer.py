"""信号生成消费者

从 mt5:events:news_filtered 消费过滤后的新闻，
为每个 ticker 生成交易信号，
发布到 mt5:events:signals
"""
import logging
import sys
import os
import uuid
from typing import Dict, Any, List
from datetime import datetime, timedelta

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from event_bus.base_consumer import BaseEventConsumer
from event_bus.base_producer import BaseEventProducer
from event_bus.config import redis_config
from signal_service.risk_manager import RiskManager, RiskConfig

logger = logging.getLogger(__name__)


class SignalGeneratorConsumer(BaseEventConsumer):
    """信号生成消费者

    功能：
    1. 从 mt5:events:news_filtered 消费过滤后的新闻
    2. 为每个 ticker_sentiment 生成独立的交易信号
    3. 信号方向：positive → BUY, negative → SELL
    4. 计算手数、止损止盈
    5. 发布到 mt5:events:signals
    """

    def __init__(
        self,
        account_balance: float = 10000.0,
        signal_expiry_hours: int = 4,
        risk_config: RiskConfig = None,
    ):
        """初始化消费者

        Args:
            account_balance: 账户余额（用于计算手数）
            signal_expiry_hours: 信号有效期（小时）
            risk_config: 风险配置
        """
        # 初始化基类
        super().__init__(
            stream_key=redis_config.STREAM_NEWS_FILTERED,
            consumer_group=redis_config.CONSUMER_GROUP_SIGNAL_GENERATOR,
            consumer_name='signal_generator_consumer_1',
            auto_ack=True,
            block_ms=5000,
            batch_size=10,
        )

        # 配置
        self.account_balance = account_balance
        self.signal_expiry_hours = signal_expiry_hours

        # 初始化风险管理器
        self.risk_manager = RiskManager(config=risk_config or RiskConfig())

        # 初始化输出生产者
        self.output_producer = BaseEventProducer(
            stream_key=redis_config.STREAM_SIGNALS
        )

        # 统计
        self.news_processed = 0
        self.signals_generated = 0
        self.signals_buy = 0
        self.signals_sell = 0

        logger.info(
            f"SignalGeneratorConsumer 已初始化: "
            f"account=${account_balance}, "
            f"expiry={signal_expiry_hours}h"
        )

    def process_event(self, event_id: str, event_data: Dict[str, Any]) -> bool:
        """处理单条过滤后的新闻

        Args:
            event_id: 事件ID
            event_data: 过滤后的新闻数据

        Returns:
            处理是否成功
        """
        try:
            self.news_processed += 1

            logger.info(f"\n处理新闻: {event_id}")
            logger.info(f"  标题: {event_data.get('title', 'N/A')}")

            # 获取 ticker 情感列表
            ticker_sentiments = event_data.get('ticker_sentiment', [])

            if not ticker_sentiments:
                logger.warning("  跳过：没有 ticker_sentiment 数据")
                return True

            logger.info(f"  包含 {len(ticker_sentiments)} 个 ticker")

            # 为每个 ticker 生成信号
            generated_count = 0
            current_date = datetime.utcnow().strftime('%Y-%m-%d')

            for ticker_sentiment in ticker_sentiments:
                ticker = ticker_sentiment.get('ticker')
                sentiment = ticker_sentiment.get('sentiment')
                score = ticker_sentiment.get('score', 0.0)
                confidence = ticker_sentiment.get('confidence', 0.0)

                # 检查是否可以生成信号（每日限制）
                if not self.risk_manager.can_generate_signal(ticker, current_date):
                    logger.info(f"    {ticker}: 达到每日信号数限制，跳过")
                    continue

                # 生成信号
                signal = self._generate_signal(
                    news_id=event_data.get('news_id'),
                    ticker=ticker,
                    sentiment=sentiment,
                    score=score,
                    confidence=confidence,
                    news_title=event_data.get('title', ''),
                    news_link=event_data.get('link', ''),
                )

                # 发布信号
                message_id = self.output_producer.produce(
                    signal,
                    event_type='trading_signal'
                )

                if message_id:
                    generated_count += 1
                    self.signals_generated += 1

                    if signal['direction'] == 'BUY':
                        self.signals_buy += 1
                    else:
                        self.signals_sell += 1

                    # 记录已生成
                    self.risk_manager.record_signal(ticker, current_date)

                    logger.info(
                        f"    ✓ {ticker}: {signal['direction']} "
                        f"{signal['lot_size']} lots, SL={signal['stop_loss']}, "
                        f"TP={signal['take_profit']} → {message_id}"
                    )
                else:
                    logger.warning(f"    ✗ {ticker}: 信号发布失败")

            logger.info(f"  本条新闻生成 {generated_count} 个信号")

            # 每处理10条打印统计
            if self.news_processed % 10 == 0:
                self._log_stats()

            return True

        except Exception as e:
            logger.error(f"处理新闻失败: {e}", exc_info=True)
            return False

    def _generate_signal(
        self,
        news_id: str,
        ticker: str,
        sentiment: str,
        score: float,
        confidence: float,
        news_title: str,
        news_link: str,
    ) -> Dict[str, Any]:
        """生成交易信号

        Args:
            news_id: 新闻ID
            ticker: 股票代码
            sentiment: 情感标签（positive/negative/neutral）
            score: 情感分数（-1到1）
            confidence: 置信度（0到1）
            news_title: 新闻标题
            news_link: 新闻链接

        Returns:
            交易信号数据
        """
        # 1. 确定交易方向
        if sentiment == 'positive':
            direction = 'BUY'
        elif sentiment == 'negative':
            direction = 'SELL'
        else:
            direction = 'BUY'  # neutral 默认 BUY

        # 2. 计算手数
        lot_size = self.risk_manager.calculate_lot_size(
            ticker=ticker,
            sentiment_score=score,
            confidence=confidence,
            account_balance=self.account_balance
        )

        # 3. 计算止损止盈
        sl_tp = self.risk_manager.calculate_sl_tp(
            ticker=ticker,
            direction=direction,
            sentiment_score=score
        )

        # 4. 计算信号有效期
        created_at = datetime.utcnow()
        expiry_at = created_at + timedelta(hours=self.signal_expiry_hours)

        # 5. 生成信号ID
        signal_id = str(uuid.uuid4())

        # 6. 构造信号数据
        signal = {
            # 基本信息
            'signal_id': signal_id,
            'ticker': ticker,
            'direction': direction,

            # 交易参数
            'lot_size': lot_size,
            'stop_loss': sl_tp['stop_loss'],      # 点数
            'take_profit': sl_tp['take_profit'],  # 点数
            'entry_price': 0.0,  # 待 MT5 执行时填充

            # 时间信息
            'created_at': created_at.isoformat() + 'Z',
            'expiry_at': expiry_at.isoformat() + 'Z',

            # 来源信息
            'source': 'news_sentiment',
            'news_id': news_id,
            'news_title': news_title,
            'news_link': news_link,

            # 情感信息
            'sentiment': sentiment,
            'sentiment_score': score,
            'confidence': confidence,

            # 原因说明
            'reason': self._build_reason(
                ticker, sentiment, score, confidence, news_title
            ),

            # 资产分类
            'asset_class': self.risk_manager.classify_asset(ticker).value,

            # 状态
            'status': 'pending',  # pending/executed/expired/cancelled
        }

        return signal

    def _build_reason(
        self,
        ticker: str,
        sentiment: str,
        score: float,
        confidence: float,
        news_title: str
    ) -> str:
        """构建信号原因说明

        Args:
            ticker: 股票代码
            sentiment: 情感
            score: 分数
            confidence: 置信度
            news_title: 新闻标题

        Returns:
            原因字符串
        """
        reason = (
            f"{sentiment.upper()} sentiment detected for {ticker} "
            f"(score={score:.2f}, confidence={confidence:.2f}) "
            f"from news: \"{news_title[:100]}...\""
        )
        return reason

    def _log_stats(self):
        """打印统计信息"""
        buy_ratio = (self.signals_buy / self.signals_generated * 100
                     if self.signals_generated > 0 else 0)
        sell_ratio = (self.signals_sell / self.signals_generated * 100
                      if self.signals_generated > 0 else 0)

        logger.info(
            f"\n=== 统计 ===\n"
            f"  已处理新闻: {self.news_processed}\n"
            f"  已生成信号: {self.signals_generated}\n"
            f"    - BUY: {self.signals_buy} ({buy_ratio:.1f}%)\n"
            f"    - SELL: {self.signals_sell} ({sell_ratio:.1f}%)\n"
            f"  风险管理: {self.risk_manager.get_stats()}\n"
        )

    def close(self):
        """关闭资源"""
        self._log_stats()
        self.output_producer.close()
        super().close()


if __name__ == "__main__":
    # 测试运行
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=== 启动 SignalGeneratorConsumer ===")
    logger.info("提示：请先运行 news_filter_consumer 发布一些过滤后的新闻")
    logger.info("按 Ctrl+C 停止\n")

    # 自定义风险配置
    risk_config = RiskConfig(
        base_risk_percent=1.0,
        max_lot_size=1.0,
        max_signals_per_day=20,
        max_signals_per_ticker=3
    )

    consumer = SignalGeneratorConsumer(
        account_balance=10000.0,
        signal_expiry_hours=4,
        risk_config=risk_config
    )

    try:
        consumer.start()
    except KeyboardInterrupt:
        logger.info("\n收到停止信号")
    finally:
        consumer.close()
