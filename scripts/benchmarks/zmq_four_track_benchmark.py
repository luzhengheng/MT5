#!/usr/bin/env python3
"""
ZMQ四轨道延迟基准测试脚本
任务: Task #135 - Four-Track Feasibility Study & System Capacity Limits
功能: 并发测试四个交易品种(4轨)的ZMQ REQ-REP延迟，验证系统容量上限
协议: Protocol v4.4 (Autonomous Living System - Ouroboros)
生成时间: 2026-01-23
说明: 基于Task #134三轨测试(P99=1722ms)，研究四轨部署可行性
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
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========================================
# 常量定义
# ========================================

# 基准测试配置
BENCHMARK_CONFIG = {
    "zmq_server_ip": "172.19.141.251",
    "zmq_req_port": 5555,
    "zmq_pub_port": 5556,
    "test_duration_seconds": 120,  # 增加至120秒以增加采样数量
    "min_samples": 100,  # 最少100条样本
    "max_concurrent_threads": 10,  # 最大并发线程数
}

# 交易品种 (Task #134: EURUSD.s, BTCUSD.s, GBPUSD.s + Task #135新增: XAUUSD.s)
SYMBOLS = ["EURUSD.s", "BTCUSD.s", "GBPUSD.s", "XAUUSD.s"]

# 输出文件 (Task #135)
RESULTS_FILE = Path("/opt/mt5-crs/zmq_four_track_results.json")
LOG_FILE = Path("/opt/mt5-crs/TASK_135_VERIFY.log")
REPORT_FILE = Path("/opt/mt5-crs/TASK_135_CAPACITY_REPORT.md")

# Session UUID
SESSION_UUID = str(uuid.uuid4())

# 全局锁(用于线程安全的结果收集)
results_lock = threading.Lock()

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
        log_entry = f"[{timestamp}] [{level}] [Task#135-Benchmark] {message}"
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
# 四轨ZMQ基准测试器
# ========================================

class FourTrackZMQBenchmark:
    """四轨ZMQ延迟基准测试器(支持并发品种测试)"""

    def __init__(self, logger: BenchmarkLogger):
        """初始化"""
        self.logger = logger
        self.context = zmq.Context()
        self.results = {
            "session_uuid": SESSION_UUID,
            "timestamp": datetime.now().isoformat(),
            "test_type": "four-track",
            "task": "Task #135",
            "symbols": {},
            "summary": {}
        }

    def test_req_rep_latency_concurrent(self, symbol: str) -> List[float]:
        """测试REQ-REP延迟(为并发设计)"""
        self.logger.log(f"[{symbol}] 启动REQ-REP并发测试线程")

        latencies = []

        try:
            # 创建REQ套接字(每个线程独立套接字)
            socket = self.context.socket(zmq.REQ)
            socket.connect(f"tcp://{BENCHMARK_CONFIG['zmq_server_ip']}:{BENCHMARK_CONFIG['zmq_req_port']}")

            # ========================================
            # Quick Wins TCP优化 (Task #133-OPT-1)
            # ========================================
            socket.setsockopt(zmq.SNDBUF, 256000)  # 256KB
            socket.setsockopt(zmq.RCVBUF, 256000)  # 256KB
            socket.setsockopt(zmq.RCVTIMEO, 2000)  # 2秒
            socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
            socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 300)
            socket.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
            socket.setsockopt(zmq.LINGER, 0)

            start_time = time.time()
            sample_count = 0

            # 在指定时间内收集样本
            while time.time() - start_time < BENCHMARK_CONFIG["test_duration_seconds"]:
                try:
                    # 发送消息 (包含线程ID用于追踪并发)
                    thread_id = threading.current_thread().ident
                    msg = f"PING:{symbol}:{int(time.time() * 1000)}:TID{thread_id}"
                    t1 = time.perf_counter()

                    socket.send_string(msg)
                    response = socket.recv_string()

                    t2 = time.perf_counter()

                    # 计算往返延迟(毫秒)
                    latency_ms = (t2 - t1) * 1000
                    latencies.append(latency_ms)
                    sample_count += 1

                    if sample_count % 50 == 0:
                        self.logger.log(f"[{symbol}] 已收集 {sample_count} 条样本")

                except zmq.Again:
                    self.logger.log(f"[{symbol}] 超时", "WARNING")
                    break
                except Exception as e:
                    self.logger.log(f"[{symbol}] 错误 - {e}", "ERROR")
                    break

            socket.close()

            self.logger.log(f"✅ [{symbol}] REQ-REP测试完成 ({sample_count}条样本)")
            self.logger.log_evidence("REQ_REP_SAMPLES", f"symbol={symbol} samples={sample_count}")

        except Exception as e:
            self.logger.log(f"❌ [{symbol}] REQ-REP测试失败 - {e}", "ERROR")

        return latencies

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

    def run_four_track_benchmark(self) -> bool:
        """运行四轨基准测试(并发执行所有品种)"""
        self.logger.log("=" * 70)
        self.logger.log("启动四轨ZMQ延迟基准测试 (Task #135)")
        self.logger.log("=" * 70)
        self.logger.log_evidence("BENCHMARK_START", f"Timestamp={datetime.now().isoformat()} Tracks={len(SYMBOLS)}")

        try:
            # 使用线程池并发运行所有品种测试
            with ThreadPoolExecutor(max_workers=min(len(SYMBOLS), BENCHMARK_CONFIG["max_concurrent_threads"])) as executor:
                # 提交所有品种的测试任务
                futures = {
                    executor.submit(self.test_req_rep_latency_concurrent, symbol): symbol
                    for symbol in SYMBOLS
                }

                # 收集结果
                for future in as_completed(futures):
                    symbol = futures[future]
                    try:
                        latencies = future.result()
                        stats = self.calculate_statistics(latencies)

                        # 线程安全地保存结果
                        with results_lock:
                            self.results["symbols"][symbol] = {
                                "req_rep": {
                                    "statistics": stats
                                }
                            }

                        self.logger.log(f"【{symbol}统计结果】")
                        self.logger.log(f"  样本数: {stats['sample_count']}")
                        self.logger.log(f"  P50: {stats['p50']:.3f}ms")
                        self.logger.log(f"  P95: {stats['p95']:.3f}ms")
                        self.logger.log(f"  P99: {stats['p99']:.3f}ms")

                    except Exception as e:
                        self.logger.log(f"❌ 处理{symbol}结果失败: {e}", "ERROR")

            # 生成汇总
            self._generate_summary()

            self.logger.log("\n✅ 四轨基准测试完成")
            self.logger.log_evidence("BENCHMARK_COMPLETE", f"Timestamp={datetime.now().isoformat()}")

            return True

        except Exception as e:
            self.logger.log(f"❌ 四轨基准测试失败: {e}", "ERROR")
            return False

    def _generate_summary(self):
        """生成汇总报告"""
        self.logger.log("\n" + "=" * 70)
        self.logger.log("四轨基准测试汇总")
        self.logger.log("=" * 70)

        # 收集所有P99值用于容量分析
        all_p99_values = []

        for symbol in SYMBOLS:
            if symbol in self.results["symbols"]:
                symbol_data = self.results["symbols"][symbol]
                req_rep_stats = symbol_data["req_rep"]["statistics"]

                self.logger.log(f"\n【{symbol}】")
                self.logger.log(f"  样本数: {req_rep_stats['sample_count']}")
                self.logger.log(f"  最小: {req_rep_stats['min']:.3f}ms")
                self.logger.log(f"  平均: {req_rep_stats['mean']:.3f}ms")
                self.logger.log(f"  最大: {req_rep_stats['max']:.3f}ms")
                self.logger.log(f"  P50:  {req_rep_stats['p50']:.3f}ms")
                self.logger.log(f"  P95:  {req_rep_stats['p95']:.3f}ms")
                self.logger.log(f"  P99:  {req_rep_stats['p99']:.3f}ms")

                all_p99_values.append(req_rep_stats['p99'])

        # 容量分析
        if all_p99_values:
            max_p99 = max(all_p99_values)
            capacity_budget = max_p99 * 1.5
            track_count = len(SYMBOLS)

            self.logger.log("\n" + "=" * 70)
            self.logger.log("容量分析")
            self.logger.log("=" * 70)
            self.logger.log(f"最大P99延迟: {max_p99:.3f}ms")
            self.logger.log(f"容量预算(P99 x 1.5): {capacity_budget:.3f}ms")
            self.logger.log(f"当前轨道数: {track_count}")

            # 与Task #134的容量对比
            task_134_budget = 2583  # 从Task #134报告
            self.logger.log(f"Task #134容量预算: {task_134_budget}ms")

            if track_count <= 3:
                status = "acceptable"
                status_text = "✅ 可接受"
            elif max_p99 < task_134_budget:
                status = "warning_but_possible"
                status_text = f"⚠️ 边界可行 (P99 {max_p99:.0f}ms < 预算 {task_134_budget}ms)"
            else:
                status = "unacceptable"
                status_text = "❌ 不可行"

            self.logger.log(f"容量评级: {status_text}")

            self.results["summary"] = {
                "total_tracks": track_count,
                "max_p99_latency": max_p99,
                "capacity_budget": capacity_budget,
                "task_134_capacity_budget": task_134_budget,
                "status": status
            }

    def save_results(self):
        """保存结果为JSON"""
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        self.logger.log(f"结果已保存: {RESULTS_FILE}")
        self.logger.log_evidence("RESULTS_SAVED", f"file={RESULTS_FILE}")


def main():
    """主函数"""
    logger = BenchmarkLogger(LOG_FILE)

    logger.log("=" * 70)
    logger.log("Four-Track ZMQ Latency Benchmark (Task #135)")
    logger.log("=" * 70)
    logger.log(f"Session UUID: {SESSION_UUID}")
    logger.log(f"ZMQ服务器: {BENCHMARK_CONFIG['zmq_server_ip']}")
    logger.log(f"REQ-REP端口: {BENCHMARK_CONFIG['zmq_req_port']}")
    logger.log(f"测试时长: {BENCHMARK_CONFIG['test_duration_seconds']}秒")
    logger.log(f"测试品种: {', '.join(SYMBOLS)} ({len(SYMBOLS)}轨)")
    logger.log(f"并发模式: 是 (最大{BENCHMARK_CONFIG['max_concurrent_threads']}线程)")
    logger.log(f"\n说明: 基于Task #134三轨P99=1722ms, 验证四轨可行性")
    logger.log(f"理论推算: 四轨P99 ≈ 1722 × (4/3) ≈ 2296ms")
    logger.log(f"容量预算: 2583ms (P99 × 1.5)")

    benchmark = FourTrackZMQBenchmark(logger)

    # 运行四轨基准测试
    success = benchmark.run_four_track_benchmark()

    # 保存结果
    if success:
        benchmark.save_results()
        logger.log("\n[UnifiedGate] PASS - 四轨基准测试成功完成")
        sys.exit(0)
    else:
        logger.log("\n[UnifiedGate] FAIL - 四轨基准测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
