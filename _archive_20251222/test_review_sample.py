# 这是一个测试的改进代码
def calculate_signal_strength(price_data, window_size=14):
    """
    计算信号强度的改进版本
    - 支持动态窗口
    - 添加异常处理
    - 优化内存使用
    """
    if not price_data or len(price_data) < window_size:
        return None
    
    # 计算移动平均线
    ma = sum(price_data[-window_size:]) / window_size
    
    # 计算标准差
    variance = sum((x - ma) ** 2 for x in price_data[-window_size:]) / window_size
    std_dev = variance ** 0.5
    
    # 计算信号强度
    current_price = price_data[-1]
    signal_strength = (current_price - ma) / std_dev if std_dev > 0 else 0
    
    return signal_strength

# 测试数据
test_prices = [100, 101, 102, 101, 103, 104, 103, 105, 106, 105, 107, 108, 109, 110]
result = calculate_signal_strength(test_prices)
print(f"信号强度: {result}")
