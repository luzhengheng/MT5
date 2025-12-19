"""
FinBERT 情感分析器 - MVP 版本
对新闻进行金融情感分析
"""

import os
import logging
from typing import List, Dict, Union
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """FinBERT 情感分析器"""

    def __init__(self, model_path: str = None, device: str = 'cpu', batch_size: int = 32):
        """
        Args:
            model_path: 模型路径，如果为 None 则从 HuggingFace 下载
            device: 'cpu' 或 'cuda'
            batch_size: 批处理大小
        """
        self.device = device
        self.batch_size = batch_size

        # 如果指定了本地路径且存在，使用本地模型
        if model_path and Path(model_path).exists():
            logger.info(f"从本地加载 FinBERT 模型: {model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        else:
            # 否则从 HuggingFace 下载
            logger.info("从 HuggingFace 下载 FinBERT 模型（首次使用会较慢）")
            model_name = "ProsusAI/finbert"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

            # 可选：保存到本地
            if model_path:
                Path(model_path).mkdir(parents=True, exist_ok=True)
                self.tokenizer.save_pretrained(model_path)
                self.model.save_pretrained(model_path)
                logger.info(f"模型已保存到: {model_path}")

        self.model.to(device)
        self.model.eval()

        # 标签映射
        self.label_map = {0: 'positive', 1: 'negative', 2: 'neutral'}

        logger.info(f"FinBERT 模型初始化完成，设备: {device}")

    def analyze_single(self, text: str) -> Dict[str, Union[str, float]]:
        """分析单条文本的情感

        Args:
            text: 输入文本

        Returns:
            {'label': 'positive/negative/neutral', 'score': 0.95, 'confidence': 0.95}
        """
        if not text or not text.strip():
            return {'label': 'neutral', 'score': 0.0, 'confidence': 0.0}

        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors='pt',
                truncation=True,
                max_length=512,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # 推理
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=1)

            # 获取预测结果
            predicted_class = torch.argmax(probs, dim=1).item()
            confidence = probs[0][predicted_class].item()

            label = self.label_map[predicted_class]

            # 将情感转换为分数 (positive: +1, negative: -1, neutral: 0)
            score_map = {'positive': 1.0, 'negative': -1.0, 'neutral': 0.0}
            score = score_map[label] * confidence

            return {
                'label': label,
                'score': score,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"情感分析失败: {e}")
            return {'label': 'neutral', 'score': 0.0, 'confidence': 0.0}

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Union[str, float]]]:
        """批量分析文本情感

        Args:
            texts: 文本列表

        Returns:
            情感结果列表
        """
        results = []

        # 过滤空文本
        valid_texts = [(i, text) for i, text in enumerate(texts) if text and text.strip()]
        valid_indices = [i for i, _ in valid_texts]
        valid_text_list = [text for _, text in valid_texts]

        if not valid_text_list:
            return [{'label': 'neutral', 'score': 0.0, 'confidence': 0.0}] * len(texts)

        try:
            # 分批处理
            for i in range(0, len(valid_text_list), self.batch_size):
                batch_texts = valid_text_list[i:i + self.batch_size]

                # Tokenize 批次
                inputs = self.tokenizer(
                    batch_texts,
                    return_tensors='pt',
                    truncation=True,
                    max_length=512,
                    padding=True
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # 推理
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits = outputs.logits
                    probs = torch.softmax(logits, dim=1)

                # 解析结果
                for j in range(len(batch_texts)):
                    predicted_class = torch.argmax(probs[j]).item()
                    confidence = probs[j][predicted_class].item()

                    label = self.label_map[predicted_class]
                    score_map = {'positive': 1.0, 'negative': -1.0, 'neutral': 0.0}
                    score = score_map[label] * confidence

                    results.append({
                        'label': label,
                        'score': score,
                        'confidence': confidence
                    })

            # 将结果映射回原始索引（包括空文本）
            full_results = [{'label': 'neutral', 'score': 0.0, 'confidence': 0.0}] * len(texts)
            for idx, result in zip(valid_indices, results):
                full_results[idx] = result

            return full_results

        except Exception as e:
            logger.error(f"批量情感分析失败: {e}")
            return [{'label': 'neutral', 'score': 0.0, 'confidence': 0.0}] * len(texts)

    def analyze_news_dataframe(
        self,
        df: pd.DataFrame,
        text_column: str = 'title',
        show_progress: bool = True
    ) -> pd.DataFrame:
        """分析新闻 DataFrame 的情感

        Args:
            df: 新闻 DataFrame
            text_column: 文本列名（默认使用 title）
            show_progress: 是否显示进度条

        Returns:
            添加了情感分析结果的 DataFrame
        """
        if df.empty:
            return df

        df = df.copy()

        # 提取文本
        texts = df[text_column].fillna('').tolist()

        # 批量分析
        all_results = []
        batches = range(0, len(texts), self.batch_size)

        if show_progress:
            batches = tqdm(batches, desc="情感分析")

        for i in batches:
            batch_texts = texts[i:i + self.batch_size]
            batch_results = self.analyze_batch(batch_texts)
            all_results.extend(batch_results)

        # 添加结果到 DataFrame
        df['sentiment_label'] = [r['label'] for r in all_results]
        df['sentiment_score'] = [r['score'] for r in all_results]
        df['sentiment_confidence'] = [r['confidence'] for r in all_results]

        # 计算成功率
        success_rate = (df['sentiment_confidence'] > 0).mean()
        logger.info(f"情感分析完成，成功率: {success_rate:.2%}")

        return df

    def analyze_ticker_level_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算每个 ticker 的情感（简化版：使用标题情感）

        Args:
            df: 包含 ticker_list 和情感分数的 DataFrame

        Returns:
            添加了 ticker 级别情感的 DataFrame
        """
        df = df.copy()

        # 简化版：直接使用整体情感作为每个 ticker 的情感
        # 完整版需要提取每个 ticker 相关的句子单独分析
        def create_sentiment_dict(row):
            if not row['ticker_list'] or len(row['ticker_list']) == 0:
                return {}

            # 为每个 ticker 赋予相同的情感分数
            sentiment_dict = {
                ticker: row['sentiment_score']
                for ticker in row['ticker_list']
            }
            return sentiment_dict

        df['sentiment_per_ticker'] = df.apply(create_sentiment_dict, axis=1)

        return df


def main():
    """主函数示例"""
    # 创建情感分析器
    model_path = "/opt/mt5-crs/var/cache/models/finbert"
    analyzer = SentimentAnalyzer(model_path=model_path, device='cpu', batch_size=16)

    # 测试样例
    test_texts = [
        "Apple reports record quarterly revenue, beating analyst expectations.",
        "Tesla stock plunges on disappointing delivery numbers.",
        "The Federal Reserve maintains interest rates unchanged.",
    ]

    print("\n=== 单条分析测试 ===")
    for text in test_texts:
        result = analyzer.analyze_single(text)
        print(f"文本: {text}")
        print(f"结果: {result}")
        print()

    # 测试 DataFrame 分析
    print("\n=== DataFrame 分析测试 ===")
    test_df = pd.DataFrame({
        'title': test_texts,
        'ticker_list': [['AAPL'], ['TSLA'], []]
    })

    result_df = analyzer.analyze_news_dataframe(test_df)
    result_df = analyzer.analyze_ticker_level_sentiment(result_df)

    print(result_df[['title', 'sentiment_label', 'sentiment_score', 'sentiment_per_ticker']])


if __name__ == '__main__':
    main()
