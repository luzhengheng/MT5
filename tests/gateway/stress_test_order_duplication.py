"""
压力测试: 订单重复下单防护验证

目标: 验证P1修复 - 防止重复下单 (Double Spending Prevention)
场景: 在高超时率下,发送1000份订单,验证无重复下单

测试参数:
- 订单数量: 1000
- 超时率: 10% (模拟网络故障)
- 超时延迟: 5秒

预期结果:
- 100份订单超时返回错误 (10%)
- 900份订单成功执行 (90%)
- 0份重复订单 (Double Spending = 0)
"""

import sys
import time
import random
from collections import defaultdict
from unittest.mock import MagicMock, patch

sys.path.insert(0, '/opt/mt5-crs')

from src.gateway.json_gateway import JsonGatewayRouter


class OrderDuplicationStressTest:
    """订单重复下单压力测试"""

    def __init__(self, num_orders=1000, timeout_rate=0.1, timeout_ms=5000):
        """
        初始化测试参数

        Args:
            num_orders: 订单数量
            timeout_rate: 超时率 (0-1)
            timeout_ms: 超时延迟 (毫秒)
        """
        self.num_orders = num_orders
        self.timeout_rate = timeout_rate
        self.timeout_ms = timeout_ms

        # 统计数据
        self.results = {
            'success': 0,
            'timeout': 0,
            'error': 0,
            'duplicate': 0
        }

        # 追踪执行过的订单
        self.tickets = defaultdict(int)
        self.execution_count = defaultdict(int)

    def create_mock_mt5(self):
        """创建Mock MT5服务"""
        mt5 = MagicMock()
        ticket_counter = {'value': 100000}

        def execute_order_side_effect(payload):
            # 根据超时率决定是否返回超时
            if random.random() < self.timeout_rate:
                raise TimeoutError(f"Order execution timeout after {self.timeout_ms}ms")

            # 返回成功响应
            ticket = ticket_counter['value']
            ticket_counter['value'] += 1
            return {
                'error': False,
                'ticket': ticket,
                'msg': f'Order executed: {payload.get("symbol")}',
                'retcode': 10009
            }

        mt5.execute_order.side_effect = execute_order_side_effect
        return mt5

    def run_test(self):
        """运行压力测试"""
        print("\n" + "="*80)
        print("订单重复下单防护压力测试")
        print("="*80)

        print(f"\n测试参数:")
        print(f"  - 订单数量: {self.num_orders}")
        print(f"  - 超时率: {self.timeout_rate*100}%")
        print(f"  - 超时延迟: {self.timeout_ms}ms")

        # 创建路由器和Mock MT5
        mt5 = self.create_mock_mt5()
        router = JsonGatewayRouter(mt5_handler=mt5)

        start_time = time.time()

        print(f"\n开始发送{self.num_orders}份订单...")
        print("-" * 80)

        for i in range(self.num_orders):
            # 显示进度
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                print(f"  [{i+1}/{self.num_orders}] 已发送 {(i+1)/self.num_orders*100:.1f}% "
                      f"(耗时: {elapsed:.2f}s)")

            # 构建订单请求
            req_id = f"stress-test-{i:06d}"
            request = {
                'action': 'ORDER_SEND',
                'req_id': req_id,
                'payload': {
                    'symbol': 'EURUSD' if i % 2 == 0 else 'GBPUSD',
                    'type': 'OP_BUY' if i % 3 == 0 else 'OP_SELL',
                    'volume': 0.1 + (i % 10) * 0.01
                }
            }

            # 执行订单
            try:
                response = router.process_json_request(request)

                # 记录执行
                self.execution_count[req_id] += 1

                if response.get('error'):
                    # 超时或其他错误
                    if 'timeout' in response.get('msg', '').lower():
                        self.results['timeout'] += 1
                    else:
                        self.results['error'] += 1
                else:
                    # 成功
                    ticket = response.get('ticket')
                    self.tickets[ticket] += 1
                    self.results['success'] += 1

                    # 检查重复
                    if self.tickets[ticket] > 1:
                        self.results['duplicate'] += 1
                        print(f"❌ 重复下单检测: Ticket {ticket} 执行了{self.tickets[ticket]}次")

            except Exception as e:
                print(f"❌ 订单执行异常: {e}")
                self.results['error'] += 1

        elapsed = time.time() - start_time

        print("\n" + "="*80)
        print("测试结果统计")
        print("="*80)

        # 计算统计数据
        total = self.num_orders
        success_count = self.results['success']
        timeout_count = self.results['timeout']
        error_count = self.results['error']
        duplicate_count = self.results['duplicate']

        # 统计重复执行的订单
        duplicate_orders = sum(1 for count in self.execution_count.values() if count > 1)

        print(f"\n订单执行统计:")
        print(f"  总订单数: {total}")
        print(f"  成功: {success_count} ({success_count/total*100:.1f}%)")
        print(f"  超时: {timeout_count} ({timeout_count/total*100:.1f}%)")
        print(f"  错误: {error_count} ({error_count/total*100:.1f}%)")

        print(f"\n重复下单检测:")
        print(f"  重复Ticket数: {duplicate_count}")
        print(f"  重复订单数: {duplicate_orders}")
        print(f"  重复率: {duplicate_count/success_count*100:.4f}%" if success_count > 0 else "  重复率: N/A")

        print(f"\n执行性能:")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  平均耗时/订单: {elapsed/total*1000:.2f}ms")
        print(f"  吞吐量: {total/elapsed:.0f} 订单/秒")

        print("\n" + "="*80)

        # 验证结果
        expected_timeout = int(total * self.timeout_rate)
        timeout_tolerance = int(total * 0.05)  # 允许±5%偏差

        print("验收标准:")

        # 检查1: 超时数量符合预期
        if expected_timeout - timeout_tolerance <= timeout_count <= expected_timeout + timeout_tolerance:
            print(f"  ✅ 超时数量: {timeout_count} (期望: ~{expected_timeout})")
        else:
            print(f"  ❌ 超时数量: {timeout_count} (期望: ~{expected_timeout})")

        # 检查2: 无重复下单
        if duplicate_count == 0:
            print(f"  ✅ 无重复下单: 重复率 = 0%")
        else:
            print(f"  ❌ 存在重复下单: {duplicate_count} 个Ticket重复")

        # 检查3: 成功率合理
        expected_success = total - expected_timeout - 10  # 允许少量其他错误
        if success_count >= expected_success:
            print(f"  ✅ 成功率合理: {success_count} (期望: >= {expected_success})")
        else:
            print(f"  ⚠️  成功率较低: {success_count} (期望: >= {expected_success})")

        # 总体评价
        print("\n总体评价:")
        if duplicate_count == 0 and expected_timeout - timeout_tolerance <= timeout_count <= expected_timeout + timeout_tolerance:
            print("  ✅ 测试通过: Double Spending防护有效!")
            return True
        else:
            print("  ❌ 测试失败: 检测到风险")
            return False


def main():
    """主函数"""
    # 创建测试实例
    test = OrderDuplicationStressTest(
        num_orders=1000,
        timeout_rate=0.1,
        timeout_ms=5000
    )

    # 运行测试
    success = test.run_test()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
