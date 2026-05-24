SYSTEM_PROMPT = """你是 KeeperKit Rules，一个 TRPG 规则书问答助手。

回答规则问题时必须遵守：
1. 规则、数值、流程和例外情况必须严格基于给定规则片段。
2. 如果规则片段没有足够依据，先明确说明“当前规则资料中未检索到明确依据”，再给出不冒充规则原文的通用建议或提问引导。
3. 可以解释中文 TRPG/CoC 常见黑话，但必须说明这是术语解释，不是规则书原文。
4. 涉及检定、伤害、轮次、奖励骰、惩罚骰时，用简洁步骤说明。
5. 回答最后必须列出“依据来源”；如果某部分不是规则书依据，请标明“通用建议，无规则书依据”。
6. 不要编造具体规则数值、表格、法术效果或怪物数据。
"""


def build_rule_prompt(
    question: str,
    contexts: list[str],
    retrieval_question: str | None = None,
    query_notes: list[str] | None = None,
) -> str:
    joined_contexts = "\n\n---\n\n".join(contexts)
    notes = "\n".join(f"- {note}" for note in query_notes or [])
    rewrite_block = ""
    if retrieval_question and retrieval_question != question:
        rewrite_block = f"""
检索改写：
{retrieval_question}
"""
    notes_block = ""
    if notes:
        notes_block = f"""
查询提示：
{notes}
"""
    return f"""{SYSTEM_PROMPT}

规则片段：
{joined_contexts}

用户问题：
{question}
{rewrite_block}{notes_block}

请给出答案。只输出最终回答，不要输出分析过程。
"""
