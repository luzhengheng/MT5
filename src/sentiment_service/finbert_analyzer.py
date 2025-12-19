"""FinBERT 情感分析器

使用预训练的 FinBERT 模型进行金融文本情感分析
"""
import logging
import os
from typing import Dict, List, Tuple, Optional
from functools import lru_cache

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

logger = logging.getLogger(__name__)


class FinBERTAnalyzer:
    """FinBERT 情感分析器

    功能：
    1. 加载预训练的 FinBERT 模型
    2. 对金融新闻文本进行情感分析
    3. 返回情感标签和分数（positive/negative/neutral）
    4. 支持批量处理
    5. 结果缓存（避免重复分析）
    """

    # 可用的 FinBERT 模型
    AVAILABLE_MODELS = {
        'finbert': 'ProsusAI/finbert',              # 通用金融情感分析
        'finbert-tone': 'yiyanghkust/finbert-tone',  # 语气分析
    }

    SENTIMENT_LABELS = ['positive', 'negative', 'neutral']

    def __init__(
        self,
        model_name: str = 'finbert',
        device: Optional[str] = None,
        cache_dir: Optional[str] = None,
    ):
        """初始化分析器

        Args:
            model_name: 模型名称，可选 'finbert' 或 'finbert-tone'
            device: 设备，'cpu' 或 'cuda'，None则自动检测
            cache_dir: 模型缓存目录
        """
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model_name: {model_name}. "
                f"Available: {list(self.AVAILABLE_MODELS.keys())}"
            )

        self.model_name = model_name
        self.model_path = self.AVAILABLE_MODELS[model_name]

        # 确定设备
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device

        # 缓存目录 (优先使用 FHS 标准路径)
        if cache_dir is None:
            # 优先使用项目缓存目录
            cache_dir = '/opt/mt5-crs/var/cache/models'
            if not os.path.exists(cache_dir):
                cache_dir = os.path.expanduser('~/.cache/finbert')

        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        logger.info(f"初始化 FinBERT 分析器: model={model_name}, device={self.device}")

        # 加载模型和分词器
        self._load_model()

        self.analysis_count = 0

    def _load_model(self):
        """加载模型和分词器"""
        try:
            logger.info(f"正在加载模型: {self.model_path}")

            # 尝试从本地缓存加载 (手动下载的模型)
            local_model_path = os.path.join(self.cache_dir, 'ProsusAI--finbert')
            use_local = os.path.exists(local_model_path)

            if use_local:
                logger.info(f"使用本地模型: {local_model_path}")
                model_source = local_model_path
                load_kwargs = {'local_files_only': True}
            else:
                logger.info(f"从 HuggingFace 下载模型...")
                model_source = self.model_path
                load_kwargs = {'cache_dir': self.cache_dir}

            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_source,
                **load_kwargs
            )

            # 加载模型
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_source,
                **load_kwargs
            )

            # 移动到指定设备
            self.model.to(self.device)

            # 设置为评估模式
            self.model.eval()

            logger.info(f"✓ 模型加载成功")

        except Exception as e:
            logger.error(f"✗ 模型加载失败: {e}", exc_info=True)
            raise

    @torch.no_grad()
    def analyze(
        self,
        text: str,
        return_all_scores: bool = False
    ) -> Dict[str, any]:
        """分析单条文本的情感

        Args:
            text: 输入文本
            return_all_scores: 是否返回所有标签的分数

        Returns:
            {
                'sentiment': 'positive'|'negative'|'neutral',
                'score': 0.85,  # 主要情感的分数
                'confidence': 0.92,  # 置信度（最大概率）
                'all_scores': {'positive': 0.85, 'negative': 0.05, 'neutral': 0.10}  # 可选
            }
        """
        if not text or not text.strip():
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0
            }

        try:
            # 分词
            inputs = self.tokenizer(
                text,
                return_tensors='pt',
                truncation=True,
                max_length=512,
                padding=True
            )

            # 移动到设备
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # 推理
            outputs = self.model(**inputs)
            logits = outputs.logits

            # 计算概率
            probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

            # 获取最大概率的标签
            predicted_class = int(np.argmax(probs))
            sentiment = self.SENTIMENT_LABELS[predicted_class]
            confidence = float(probs[predicted_class])

            # 计算情感分数（positive - negative，范围 -1 到 1）
            score = float(probs[0] - probs[1])  # positive - negative

            self.analysis_count += 1

            result = {
                'sentiment': sentiment,
                'score': score,
                'confidence': confidence
            }

            if return_all_scores:
                result['all_scores'] = {
                    label: float(prob)
                    for label, prob in zip(self.SENTIMENT_LABELS, probs)
                }

            logger.debug(
                f"分析完成: sentiment={sentiment}, score={score:.3f}, "
                f"confidence={confidence:.3f}"
            )

            return result

        except Exception as e:
            logger.error(f"情感分析失败: {e}", exc_info=True)
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'error': str(e)
            }

    def analyze_with_ticker_context(
        self,
        text: str,
        ticker: str,
        context_window: int = 200
    ) -> Dict[str, any]:
        """分析文本中特定 ticker 的情感

        提取 ticker 相关的文本片段进行分析

        Args:
            text: 完整文本
            ticker: 目标 ticker
            context_window: 上下文窗口大小（字符数）

        Returns:
            情感分析结果
        """
        # 查找 ticker 在文本中的位置
        ticker_positions = []

        # 搜索 $TICKER 格式
        search_patterns = [
            f'${ticker}',
            f' {ticker} ',
            f' {ticker},',
            f' {ticker}.',
            ticker.lower(),
        ]

        for pattern in search_patterns:
            start = 0
            while True:
                pos = text.find(pattern, start)
                if pos == -1:
                    break
                ticker_positions.append(pos)
                start = pos + 1

        # 如果找到 ticker，提取相关片段
        if ticker_positions:
            # 使用第一个出现位置
            pos = ticker_positions[0]

            # 提取上下文
            start = max(0, pos - context_window)
            end = min(len(text), pos + len(ticker) + context_window)

            context_text = text[start:end].strip()

            logger.debug(
                f"提取 ticker '{ticker}' 上下文: "
                f"{context_text[:100]}..."
            )

            # 分析上下文
            result = self.analyze(context_text, return_all_scores=True)
            result['ticker'] = ticker
            result['context_used'] = True

            return result
        else:
            # 如果没有找到 ticker，分析整篇文本
            logger.debug(f"未找到 ticker '{ticker}'，分析整篇文本")

            result = self.analyze(text, return_all_scores=True)
            result['ticker'] = ticker
            result['context_used'] = False

            return result

    def analyze_batch(
        self,
        texts: List[str],
        batch_size: int = 8
    ) -> List[Dict[str, any]]:
        """批量分析文本

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            分析结果列表
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]

            for text in batch_texts:
                result = self.analyze(text)
                results.append(result)

        return results

    def get_stats(self) -> Dict[str, any]:
        """获取统计信息"""
        return {
            'model_name': self.model_name,
            'model_path': self.model_path,
            'device': self.device,
            'analysis_count': self.analysis_count,
        }


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== FinBERT 情感分析测试 ===\n")

    # 初始化分析器
    analyzer = FinBERTAnalyzer(model_name='finbert')

    # 测试用例
    test_cases = [
        "Apple stock surges to new high as iPhone sales exceed expectations",
        "Tesla faces major challenges as production delays continue",
        "Microsoft announces new cloud services, neutral market reaction",
        "Amazon reports strong earnings, beating analyst estimates significantly",
        "Google's ad revenue disappoints, shares fall 5%",
    ]

    print("分析结果：\n")

    for i, text in enumerate(test_cases, 1):
        result = analyzer.analyze(text, return_all_scores=True)

        print(f"{i}. 文本: {text}")
        print(f"   情感: {result['sentiment']}")
        print(f"   分数: {result['score']:.3f}")
        print(f"   置信度: {result['confidence']:.3f}")
        print(f"   详细分数: {result.get('all_scores', {})}")
        print()

    # 统计
    stats = analyzer.get_stats()
    print(f"统计信息: {stats}")
