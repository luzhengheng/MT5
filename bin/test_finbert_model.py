#!/usr/bin/env python3
"""测试 FinBERT 模型加载和情感分析功能"""
import os
import sys
import logging

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_model():
    """测试模型加载和推理"""
    model_path = '/opt/mt5-crs/var/cache/models/ProsusAI--finbert'

    logger.info("=" * 60)
    logger.info("FinBERT 模型测试")
    logger.info("=" * 60)
    logger.info(f"模型路径: {model_path}")
    logger.info("")

    try:
        # 加载分词器
        logger.info("[1/4] 加载分词器...")
        tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        logger.info("✓ 分词器加载成功")

        # 加载模型
        logger.info("[2/4] 加载模型...")
        model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            local_files_only=True
        )
        logger.info("✓ 模型加载成功")

        # 设置为评估模式
        model.eval()

        # 测试样本
        test_texts = [
            "The company's revenue increased by 25% this quarter, beating analyst expectations.",
            "The stock price plummeted after the CEO resigned amid scandal.",
            "The quarterly report showed mixed results with flat growth.",
        ]

        logger.info("[3/4] 运行情感分析测试...")
        logger.info("")

        sentiment_labels = ['positive', 'negative', 'neutral']

        for i, text in enumerate(test_texts, 1):
            logger.info(f"测试样本 {i}:")
            logger.info(f"  文本: {text[:80]}...")

            # 分词
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

            # 推理
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=1)
                predicted_class = torch.argmax(probs, dim=1).item()
                confidence = probs[0][predicted_class].item()

            sentiment = sentiment_labels[predicted_class]
            logger.info(f"  情感: {sentiment} (置信度: {confidence:.2%})")
            logger.info(f"  概率分布: positive={probs[0][0]:.2%}, negative={probs[0][1]:.2%}, neutral={probs[0][2]:.2%}")
            logger.info("")

        logger.info("[4/4] 性能测试...")
        import time
        test_text = "The market showed strong performance today."
        inputs = tokenizer(test_text, return_tensors="pt", padding=True, truncation=True)

        # 预热
        with torch.no_grad():
            _ = model(**inputs)

        # 计时
        start = time.time()
        num_runs = 10
        for _ in range(num_runs):
            with torch.no_grad():
                _ = model(**inputs)
        elapsed = time.time() - start
        avg_time = elapsed / num_runs

        logger.info(f"✓ 平均推理时间: {avg_time*1000:.1f} ms ({num_runs} 次运行)")
        logger.info("")

        logger.info("=" * 60)
        logger.info("✓ 所有测试通过!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("模型已就绪，可以用于生产环境")

        return True

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_model()
    sys.exit(0 if success else 1)
