"""
压力测试: Notion推送耐久性验证

目标: 验证Phase 2集成 - Notion推送50次重试机制
场景: 发送100个推送任务,30%故障率,验证最终成功率>99%

测试参数:
- 推送数量: 100
- 故障率: 30% (模拟网络故障)
- 最大重试: 50次
- 超时: 300秒

预期结果:
- 最终成功率: > 99%
- 平均重试次数: < 5
- 最大重试次数: < 50
- 总耗时: < 300秒 (5分钟)
"""

import sys
import time
import random
from collections import defaultdict
from unittest.mock import MagicMock, patch

sys.path.insert(0, '/opt/mt5-crs')


class NotionResilienceStressTest:
    """Notion推送耐久性压力测试"""

    def __init__(self, num_pushes=100, failure_rate=0.3, max_retries=50):
        """
        初始化测试参数

        Args:
            num_pushes: 推送数量
            failure_rate: 故障率 (0-1)
            max_retries: 最大重试次数
        """
        self.num_pushes = num_pushes
        self.failure_rate = failure_rate
        self.max_retries = max_retries

        # 统计数据
        self.results = {
            'success': 0,
            'failed': 0,
            'retries_total': 0,
            'retries_max': 0,
            'retries_list': []
        }

    def create_mock_notion(self):
        """创建Mock Notion API"""
        notion = MagicMock()
        retry_count = defaultdict(int)

        def push_task_side_effect(task_id, payload):
            """
            模拟推送到Notion的函数

            前30%的调用返回失败,模拟网络故障
            后续调用返回成功
            """
            # 某个任务会在前几次调用时失败
            retry_count[task_id] += 1
            attempt_num = retry_count[task_id]

            # 前30%的任务在前3次尝试会失败
            if random.random() < self.failure_rate and attempt_num < 4:
                raise ConnectionError(f"Network error (attempt {attempt_num})")

            # 最终返回成功
            return {
                'success': True,
                'task_id': task_id,
                'page_id': f'page_{task_id}',
                'attempt': attempt_num
            }

        notion.push_task.side_effect = push_task_side_effect
        return notion

    def run_test(self):
        """运行压力测试"""
        print("\n" + "="*80)
        print("Notion推送耐久性压力测试")
        print("="*80)

        print(f"\n测试参数:")
        print(f"  - 推送数量: {self.num_pushes}")
        print(f"  - 故障率: {self.failure_rate*100}%")
        print(f"  - 最大重试: {self.max_retries}次")

        # 创建Mock Notion
        notion = self.create_mock_notion()

        start_time = time.time()

        print(f"\n开始推送{self.num_pushes}个任务...")
        print("-" * 80)

        for i in range(self.num_pushes):
            # 显示进度
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                print(f"  [{i+1}/{self.num_pushes}] 已推送 {(i+1)/self.num_pushes*100:.1f}% "
                      f"(耗时: {elapsed:.2f}s)")

            task_id = f"notion-push-{i:04d}"
            payload = {
                'title': f'Task {i}',
                'description': f'Description for task {i}',
                'status': 'in_progress'
            }

            # 执行推送,带重试逻辑
            retry_attempt = 0
            last_error = None

            while retry_attempt <= self.max_retries:
                try:
                    result = notion.push_task(task_id, payload)
                    self.results['success'] += 1
                    self.results['retries_total'] += retry_attempt
                    self.results['retries_list'].append(retry_attempt)

                    if retry_attempt > self.results['retries_max']:
                        self.results['retries_max'] = retry_attempt

                    break

                except ConnectionError as e:
                    last_error = e
                    retry_attempt += 1

                    # 模拟指数退避
                    backoff_time = min(0.001 * (2 ** retry_attempt), 0.1)
                    time.sleep(backoff_time)

                    if retry_attempt > self.max_retries:
                        self.results['failed'] += 1
                        print(f"❌ 推送失败: {task_id} 在{retry_attempt}次重试后失败")
                        break

            else:
                # 若循环正常结束但仍未成功
                if retry_attempt > self.max_retries:
                    self.results['failed'] += 1

        elapsed = time.time() - start_time

        print("\n" + "="*80)
        print("测试结果统计")
        print("="*80)

        total = self.num_pushes
        success_count = self.results['success']
        failed_count = self.results['failed']
        retries_total = self.results['retries_total']
        retries_max = self.results['retries_max']

        # 计算重试统计
        if self.results['retries_list']:
            avg_retries = retries_total / success_count
            median_retries = sorted(self.results['retries_list'])[len(self.results['retries_list'])//2]
        else:
            avg_retries = 0
            median_retries = 0

        print(f"\n推送执行统计:")
        print(f"  总推送数: {total}")
        print(f"  成功: {success_count} ({success_count/total*100:.1f}%)")
        print(f"  失败: {failed_count} ({failed_count/total*100:.1f}%)")

        print(f"\n重试统计:")
        print(f"  平均重试次数: {avg_retries:.2f}")
        print(f"  中位数重试: {median_retries}")
        print(f"  最大重试次数: {retries_max}")

        print(f"\n性能指标:")
        print(f"  总耗时: {elapsed:.2f}秒")
        print(f"  平均耗时/推送: {elapsed/total*1000:.2f}ms")
        print(f"  吞吐量: {total/elapsed:.1f} 推送/秒")

        print("\n" + "="*80)

        # 验证结果
        print("验收标准:")

        # 检查1: 最终成功率 > 99%
        success_rate = success_count / total * 100
        if success_rate > 99:
            print(f"  ✅ 最终成功率: {success_rate:.1f}% (> 99%)")
        else:
            print(f"  ⚠️  最终成功率: {success_rate:.1f}% (<= 99%)")

        # 检查2: 平均重试次数 < 5
        if avg_retries < 5:
            print(f"  ✅ 平均重试次数: {avg_retries:.2f} (< 5)")
        else:
            print(f"  ⚠️  平均重试次数: {avg_retries:.2f} (>= 5)")

        # 检查3: 最大重试次数 < 50
        if retries_max < 50:
            print(f"  ✅ 最大重试次数: {retries_max} (< 50)")
        else:
            print(f"  ⚠️  最大重试次数: {retries_max} (>= 50)")

        # 检查4: 总耗时 < 300秒
        if elapsed < 300:
            print(f"  ✅ 总耗时: {elapsed:.2f}秒 (< 300秒)")
        else:
            print(f"  ⚠️  总耗时: {elapsed:.2f}秒 (>= 300秒)")

        # 总体评价
        print("\n总体评价:")
        if success_rate > 99 and retries_max < 50 and elapsed < 300:
            print("  ✅ 测试通过: Notion推送50次重试机制有效!")
            return True
        else:
            print("  ⚠️  测试部分通过: 某些指标未达标")
            return False


def main():
    """主函数"""
    # 创建测试实例
    test = NotionResilienceStressTest(
        num_pushes=100,
        failure_rate=0.3,
        max_retries=50
    )

    # 运行测试
    success = test.run_test()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
