# RAG Step 06：固定评测问题集脚本

## 本步目标

增加一套可重复运行的规则问答检索评测问题，用来在后续更换 reranker、调整 chunk 或改前端展示前做回归对比。

本步默认只评测检索和 rerank 结果，不调用 LLM，也不需要读取真实 API key。

## 修改内容

新增固定问题集：

```text
backend/data/eval/rules_eval_questions.json
```

新增评测脚本：

```text
backend/scripts/evaluate_rules.py
```

问题集目前包含 15 个 CoC 7 版常用规则问题，覆盖：

```text
奖励骰/惩罚骰
孤注一掷
成功等级
大失败
战斗顺序
闪避/反击
火器故障
伤害加值
理智检定
临时疯狂
追逐 MOV
魔法值恢复
神话典籍
法术成本
怪物护甲/伤害
```

## 运行方式

推荐使用当前 Chroma + BGE 配置：

```powershell
cd keeperkit\backend
$env:KEEPERKIT_DISABLE_DOTENV = "1"
$env:INDEX_DIR = ".\data\index\coc7_bge_chroma"
$env:EMBEDDING_PROVIDER = "sentence_transformers"
$env:EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
$env:VECTOR_STORE_PROVIDER = "chroma"
$env:CHROMA_COLLECTION = "keeperkit_coc7"
python scripts\evaluate_rules.py --top-k 8 --rerank-top-k 3
```

这里显式设置 `KEEPERKIT_DISABLE_DOTENV=1`，表示本次脚本只使用临时环境变量和默认值，不读取 `backend/.env`。

输出 JSON 报告：

```powershell
python scripts\evaluate_rules.py --top-k 8 --rerank-top-k 3 --output data\eval\latest_report.json
```

## 判定方式

每个问题包含 `expected_terms`。脚本会在召回候选和最终 rerank 结果中查找这些关键词：

```text
PASS：最终 rerank 结果命中
CANDIDATE_ONLY：原始召回命中，但 rerank 后丢失
MISS：原始召回和 rerank 都未命中
```

这不是最终答案质量评测，而是一个轻量的检索回归检查。后续接入 BGE reranker 后，可以用同一组问题对比 `PASS / CANDIDATE_ONLY / MISS` 的变化。

## 下一步

接入 BGE reranker：

```text
Chroma Top 20
  -> BAAI/bge-reranker-v2-m3 Top 5
  -> DeepSeek Answer
```
