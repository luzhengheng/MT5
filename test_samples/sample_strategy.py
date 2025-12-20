
def calculate_risk(position_size, stop_loss, account_balance):
    '''
    计算交易风险
    '''
    risk_percent = (position_size * stop_loss) / account_balance * 100
    if risk_percent > 2.0:
        return False, f"风险过高: {risk_percent:.2f}%"
    return True, f"风险可接受: {risk_percent:.2f}%"

def backtest_strategy(strategy_func, historical_data):
    '''
    策略回测示例
    '''
    results = []
    for data_point in historical_data:
        signal = strategy_func(data_point)
        if signal:
            results.append(signal)
    return results
