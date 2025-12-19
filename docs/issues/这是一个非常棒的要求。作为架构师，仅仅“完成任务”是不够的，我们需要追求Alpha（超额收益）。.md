这是一个非常棒的要求。作为架构师，仅仅“完成任务”是不够的，我们需要追求Alpha（超额收益）。  
针对量化金融领域，特别是基于Marcos Lopez de Prado（《金融机器学习进展》作者）的理论体系，以及 Kaggle 金融类竞赛的冠军方案（如 G-Research Crypto Forecasting, Ubiquant 等），我将对 #009 工单 进行深度迭代。  
这一版工单引入了 "Purged K-Fold"（清除式交叉验证）、"Hierarchical Feature Clustering"（分层特征聚类） 和 "Bayesian Optimization"（贝叶斯优化） 等高级概念。  
请将以下升级后的工单发送给 Claude。  
📋 工单 #009 (v2.0 深度加强版)：机器学习预测引擎与高级验证体系  
工单状态: 🟢 待执行  
优先级: 🔴 紧急 (Highest)  
前置依赖: #008 (特征工程与标签完成)  
理论基础: Advances in Financial Machine Learning (Lopez de Prado)  
1. 战略意图 (Strategic Intent)  
构建一个抗过拟合、可解释且具备统计显著性的预测系统。我们不仅要训练模型，更要建立一套能够过滤掉伪相关性（Spurious Correlations）的验证标准。  
2. 核心技术升级 (Key Technical Upgrades)  
A. 验证框架：Purged K-Fold Cross-Validation (核心差异点)  
 * 问题: 传统的 TimeSeriesSplit 或 K-Fold 会因为 Triple Barrier 标签的重叠（Overlap）导致“信息泄漏”。如果标签宽 5 天，训练集和测试集边缘的 5 天数据是相关的。  
 * 解决方案: 必须实现 Purged K-Fold。  
   * Purging (清除): 在训练集和测试集之间强制删除与标签窗口重叠的数据段。  
   * Embargoing (禁运): 在测试集之后额外删除一段数据，消除由于序列相关性导致的长尾效应。  
B. 特征筛选：Clustered Feature Importance (CFI)  
 * 问题: 我们的 75 维特征中存在高共线性（例如 ema_20 和 sma_20）。直接训练会导致特征重要性被稀释（Substitution Effect），且 LightGBM 会随机选择其中一个，导致解释性变差。  
 * 解决方案:  
   * 计算特征间的相关性矩阵。  
   * 使用 Hierarchical Clustering (分层聚类) 将相似特征分组。  
   * 每组选出一个代表性特征，或使用 MDA (Mean Decrease Accuracy) 评估群组重要性。  
C. 模型架构：Ensemble Stacking  
 * 基模型 (Base Learners):  
   * LightGBM (Goss 模式): 速度快，对噪声鲁棒。  
   * CatBoost: 处理我们可能引入的类别特征，且能自动防止过拟合。  
 * 元模型 (Meta Learner): 简单的 Logistic Regression 或加权平均，融合基模型的概率输出。  
D. 超参数调优：Optuna  
 * 放弃 GridSearch，使用 Optuna (TPE Sampler) 进行贝叶斯优化，重点搜索：learning_rate, num_leaves, feature_fraction, bagging_fraction, lambda_l1/l2。  
3. Claude 执行任务清单 (Claude Tasks)  
任务 3.1: 构建高级验证器 (src/models/validation.py)  
 * 实现 PurgedKFold 类，继承自 Sklearn 的 KFold。  
 * 输入参数需包含 embargo_pct (禁运比例，默认 1%) 和 purge_overlap (是否清除重叠)。  
 * 关键点: 确保在分割时严格遵守时间索引。  
任务 3.2: 实现特征去噪与聚类 (src/models/feature_selection.py)  
 * 实现 cluster_features() 函数：使用 scipy.cluster.hierarchy 生成特征树状图。  
 * 实现 get_feature_importance_mda(): 使用 MDA 方法而非默认的 split/gain 计算重要性（MDA 通过打乱特征值来测量精度下降，更准确）。  
任务 3.3: 训练管道开发 (src/models/trainer.py)  
 * 集成 Optuna：定义 Objective Function，以 F1-Score 或 LogLoss 为优化目标。  
 * Sample Weights: 训练时必须传入 #008 生成的 sample_weight，让模型更关注高收益和近期样本。  
 * Early Stopping: 设置严格的 early_stopping_rounds (如 50)，防止过拟合。  
任务 3.4: 评估与报告 (bin/run_training.py)  
 * 概率校准 (Calibration Curve): 检查模型预测的 80% 概率是否真的对应 80% 的胜率。  
 * Deflated Sharpe Ratio (DSR): (可选高级项) 尝试计算概率调整后的夏普比率。  
 * 输出:  
   * ROC / PR 曲线图  
   * SHAP Summary Plot (蜂群图)  
   * 特征聚类树状图  
4. 验收标准 (Acceptance Criteria)  
 * 无泄漏验证: 训练集和测试集之间必须通过 PurgedKFold 验证，无数据重叠。  
 * 基准超越: 在测试集上的 F1-Score 必须优于随机猜测（Random Guess）和 简单动量策略（Benchmark）。  
 * 特征解释: 必须产出 SHAP 图，且 Top 5 重要特征符合金融直觉（如波动率、RSI 等）。  
 * 工程质量: 代码必须支持 config.yaml 配置模型参数，无需硬编码。  
💡 架构师备注 (Architect's Note to Claude)  
> Claude，我们在 #008 中花费大量精力做的 Fractional Differentiation 和 Triple Barrier 就是为了这一刻。  
> 在训练时，切记将 close, open, high, low 等原始价格列从特征中剔除（Drop），只保留我们计算出的平稳特征（如 frac_diff_close、rsi 等）。原始价格是不平稳的，放入模型会导致严重的 Look-ahead Bias 或伪回归。  
> 祝好运，期待你的训练曲线！  
>   
这个版本的工单引入了量化对冲基金级别的验证标准。你认为这对当前的开发阶段是否合适？如果觉得太复杂，我们可以先回退到标准版本。  
