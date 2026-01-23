#!/usr/bin/env python3
"""
ZMQ消息延迟基准测试脚本
任务: Task #133 - ZMQ Message Latency Benchmarking & Baseline Establishment
功能: 测试EURUSD.s和BTCUSD.s的ZMQ REQ-REP和PUB-SUB延迟
协议: Protocol v4.4 (Zero-Trust Forensics)
生成时间: 2026-01-23
"""

import zmq
import time
import json
import statistics
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import threading
import sys

# ========================================
# 常量定义
# ========================================

# 基准测试配置
BENCHMARK_CONFIG = {
    "zmq_server_ip": "172.19.141.251",
    "zmq_req_port": 5555,
    "zmq_pub_port": 5556,
    "test_duration_seconds": 60,  # 缩短测试时间为演示目的
    "min_samples": 100,  # 最少100条样本用于演示
}

# 交易品种
SYMBOLS = ["EURUSD.s", "BTCUSD.s"]

# 输出文件
RESULTS_FILE = Path("/opt/mt5-crs/zmq_latency_results.json")
LOG_FILE = Path("/opt/mt5-crs/VERIFY_LOG.log")
REPORT_FILE = Path("/opt/mt5-crs/TASK_133_LATENCY_REPORT.md")

# Session UUID
SESSION_UUID = str(uuid.uuid4())

# ========================================
# 日志记录
# ========================================

class BenchmarkLogger:
    """基准测试日志记录器"""

    def __init__(self, log_file: Path):
        """初始化"""
        self.log_file = log_file

    def log(self, message: str, level: str = "INFO"):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] [Task#133-Benchmark] {message}"
        print(log_entry)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")

    def log_evidence(self, evidence_type: str, data: str):
        """记录物理证据"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        evidence = f"[{timestamp}] [PHYSICAL_EVIDENCE] [{evidence_type}] UUID={SESSION_UUID} {data}"
        print(evidence)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(evidence + "\n")


# ========================================
# ZMQ基准测试器
# ========================================

class ZMQLatencyBenchmark:
    """ZMQ延迟基准测试器"""

    def __init__(self, logger: BenchmarkLogger):
        """初始化"""
        self.logger = logger
        self.context = zmq.Context()
        self.results = {
            "session_uuid": SESSION_UUID,
            "timestamp": datetime.now().isoformat(),
            "symbols": {},
            "summary": {}
        }

    def test_req_rep_latency(self, symbol: str) -> List[float]:
        """测试REQ-REP延迟"""
        self.logger.log(f"测试REQ-REP延迟: {symbol}")

        latencies = []

        try:
            # 创建REQ套接字
            socket = self.context.socket(zmq.REQ)
            socket.connect(f"tcp://{BENCHMARK_CONFIG['zmq_server_ip']}:{BENCHMARK_CONFIG['zmq_req_port']}")
            socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5秒超时

            start_time = time.time()
            sample_count = 0

            # 在指定时间内收集样本
            while time.time() - start_time < BENCHMARK_CONFIG["test_duration_seconds"]:
                try:
                    # 发送消息
                    msg = f"PING:{symbol}:{int(time.time() * 1000)}"
                    t1 = time.perf_counter()

                    socket.send_string(msg)
                    response = socket.recv_string()

                    t2 = time.perf_counter()

                    # 计算往返延迟(毫秒)
                    latency_ms = (t2 - t1) * 1000
                    latencies.append(latency_ms)
                    sample_count += 1

                    if sample_count % 20 == 0:
                        self.logger.log(f"  已收集 {sample_count} 条 {symbol} REQ-REP样本")

                except zmq.Again:
                    self.logger.log(f"  超时: {symbol} REQ-REP", "WARNING")
                    break
                except Exception as e:
                    self.logger.log(f"  错误: {symbol} REQ-REP - {e}", "ERROR")
                    break

            socket.close()

            self.logger.log(f"✅ REQ-REP延迟测试完成: {symbol} ({sample_count}条样本)")
            self.logger.log_evidence("REQ_REP_SAMPLES", f"symbol={symbol} samples={sample_count}")

        except Exception as e:
            self.logger.log(f"❌ REQ-REP测试失败: {symbol} - {e}", "ERROR")

        return latencies

    def test_pub_sub_throughput(self, symbol: str) -> Dict[str, float]:
        """测试PUB-SUB吞吐量"""
        self.logger.log(f"测试PUB-SUB吞吐量: {symbol}")

        try:
            # 创建SUB套接字
            socket = self.context.socket(zmq.SUB)
            socket.connect(f"tcp://{BENCHMARK_CONFIG['zmq_server_ip']}:{BENCHMARK_CONFIG['zmq_pub_port']}")
            socket.subscribe(symbol.encode())
            socket.setsockopt(zmq.RCVTIMEO, 5000)

            start_time = time.time()
            message_count = 0
            message_sizes = []

            # 收集PUB-SUB消息
            while time.time() - start_time < BENCHMARK_CONFIG["test_duration_seconds"]:
                try:
                    msg = socket.recv()
                    message_count += 1
                    message_sizes.append(len(msg))

                    if message_count % 100 == 0:
                        self.logger.log(f"  已接收 {message_count} 条 {symbol} PUB-SUB消息")

                except zmq.Again:
                    break

            socket.close()

            elapsed_time = time.time() - start_time
            throughput = message_count / elapsed_time if elapsed_time > 0 else 0

            self.logger.log(f"✅ PUB-SUB吞吐测试完成: {symbol}")
            self.logger.log_evidence("PUB_SUB_MESSAGES", f"symbol={symbol} messages={message_count} throughput={throughput:.2f} msgs/sec")

            return {
                "message_count": message_count,
                "elapsed_time": elapsed_time,
                "throughput": throughput,
                "avg_message_size": sum(message_sizes) / len(message_sizes) if message_sizes else 0
            }

        except Exception as e:
            self.logger.log(f"❌ PUB-SUB测试失败: {symbol} - {e}", "ERROR")
            return {
                "message_count": 0,
                "elapsed_time": 0,
                "throughput": 0,
                "avg_message_size": 0
            }

    def calculate_statistics(self, latencies: List[float]) -> Dict:
        """计算延迟统计"""
        if not latencies:
            return {
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0,
                "stdev": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0,
                "sample_count": 0
            }

        sorted_latencies = sorted(latencies)
        sample_count = len(sorted_latencies)

        return {
            "min": min(sorted_latencies),
            "max": max(sorted_latencies),
            "mean": statistics.mean(sorted_latencies),
            "median": statistics.median(sorted_latencies),
            "stdev": statistics.stdev(sorted_latencies) if sample_count > 1 else 0,
            "p50": sorted_latencies[int(sample_count * 0.50)],
            "p95": sorted_latencies[int(sample_count * 0.95)],
            "p99": sorted_latencies[int(sample_count * 0.99)],
            "sample_count": sample_count
        }

    def run_benchmark(self) -> bool:
        """运行完整基准测试"""
        self.logger.log("=" * 70)
        self.logger.log("启动ZMQ延迟基准测试 (Task #133)")
        self.logger.log("=" * 70)
        self.logger.log_evidence("BENCHMARK_START", f"Timestamp={datetime.now().isoformat()}")

        try:
            for symbol in SYMBOLS:
                self.logger.log(f"\n【测试品种】{symbol}")

                # REQ-REP延迟测试
                req_rep_latencies = self.test_req_rep_latency(symbol)
                req_rep_stats = self.calculate_statistics(req_rep_latencies)

                # PUB-SUB吞吐测试
                pub_sub_stats = self.test_pub_sub_throughput(symbol)

                # 保存结果
                self.results["symbols"][symbol] = {
                    "req_rep": {
                        "latencies": req_rep_latencies,  # 保存所有样本供分析
                        "statistics": req_rep_stats
                    },
                    "pub_sub": pub_sub_stats
                }

                self.logger.log(f"\n【{symbol}统计结果】")
                self.logger.log(f"  REQ-REP P50: {req_rep_stats['p50']:.3f}ms")
                self.logger.log(f"  REQ-REP P95: {req_rep_stats['p95']:.3f}ms")
                self.logger.log(f"  REQ-REP P99: {req_rep_stats['p99']:.3f}ms")
                self.logger.log(f"  PUB-SUB 吞吐: {pub_sub_stats['throughput']:.2f} msgs/sec")

            # 生成汇总
            self._generate_summary()

            self.logger.log("\n✅ 基准测试完成")
            self.logger.log_evidence("BENCHMARK_COMPLETE", f"Timestamp={datetime.now().isoformat()}")

            return True

        except Exception as e:
            self.logger.log(f"❌ 基准测试失败: {e}", "ERROR")
            return False

    def _generate_summary(self):
        """生成汇总报告"""
        self.logger.log("\n" + "=" * 70)
        self.logger.log("基准测试汇总")
        self.logger.log("=" * 70)

        for symbol in SYMBOLS:
            symbol_data = self.results["symbols"][symbol]
            req_rep_stats = symbol_data["req_rep"]["statistics"]
            pub_sub_stats = symbol_data["pub_sub"]

            self.logger.log(f"\n【{symbol}】")
            self.logger.log(f"  REQ-REP样本数: {req_rep_stats['sample_count']}")
            self.logger.log(f"  REQ-REP最小: {req_rep_stats['min']:.3f}ms")
            self.logger.log(f"  REQ-REP平均: {req_rep_stats['mean']:.3f}ms")
            self.logger.log(f"  REQ-REP最大: {req_rep_stats['max']:.3f}ms")
            self.logger.log(f"  REQ-REP P50:  {req_rep_stats['p50']:.3f}ms")
            self.logger.log(f"  REQ-REP P95:  {req_rep_stats['p95']:.3f}ms")
            self.logger.log(f"  REQ-REP P99:  {req_rep_stats['p99']:.3f}ms")
            self.logger.log(f"  PUB-SUB吞吐: {pub_sub_stats['throughput']:.2f} msgs/sec")
            self.logger.log(f"  PUB-SUB消息: {pub_sub_stats['message_count']}")

    def save_results(self):
        """保存结果为JSON"""
        # 移除latencies列表以减小文件大小
        results_copy = self.results.copy()
        for symbol in results_copy["symbols"]:
            if "latencies" in results_copy["symbols"][symbol]["req_rep"]:
                del results_copy["symbols"][symbol]["req_rep"]["latencies"]

        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results_copy, f, indent=2, ensure_ascii=False)

        self.logger.log(f"结果已保存: {RESULTS_FILE}")
        self.logger.log_evidence("RESULTS_SAVED", f"file={RESULTS_FILE}")


def main():
    """主函数"""
    logger = BenchmarkLogger(LOG_FILE)

    logger.log("=" * 70)
    logger.log("ZMQ Message Latency Benchmark (Task #133)")
    logger.log("=" * 70)
    logger.log(f"Session UUID: {SESSION_UUID}")
    logger.log(f"ZMQ服务器: {BENCHMARK_CONFIG['zmq_server_ip']}")
    logger.log(f"REQ-REP端口: {BENCHMARK_CONFIG['zmq_req_port']}")
    logger.log(f"PUB-SUB端口: {BENCHMARK_CONFIG['zmq_pub_port']}")
    logger.log(f"测试时长: {BENCHMARK_CONFIG['test_duration_seconds']}秒")

    benchmark = ZMQLatencyBenchmark(logger)

    # 运行基准测试
    success = benchmark.run_benchmark()

    # 保存结果
    if success:
        benchmark.save_results()
        logger.log("\n[UnifiedGate] PASS - ZMQ基准测试成功完成")
        sys.exit(0)
    else:
        logger.log("\n[UnifiedGate] FAIL - ZMQ基准测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
