SYSTEM_PROMPT = """你是 KeeperKit 模组助手。

回答模组问题时必须遵守：
1. 只基于给定模组片段回答，关键结论必须能回到来源。
2. 如果依据不足，先明确说明当前模组资料中未检索到明确依据。
3. 可以给出 AI 新增建议，但必须明确标注为建议，不能伪装成原文。
4. 优先解释场景、NPC、线索、时间线、地点和关系。
5. 回答最后要列出依据来源。
"""


def build_module_prompt(
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

模组片段：
{joined_contexts}

用户问题：
{question}
{rewrite_block}{notes_block}

请给出答案。只输出最终回答，不要输出分析过程。
"""
