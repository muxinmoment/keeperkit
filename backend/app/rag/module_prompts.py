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


def build_full_module_prep_prompt(module_title: str, documents: list[str]) -> str:
    joined_documents = "\n\n===== 文档分隔 =====\n\n".join(documents)
    return f"""{SYSTEM_PROMPT}

你现在不是在回答单个问题，而是在帮助新人守秘人完整备团。
请直接阅读下面的模组全文资料，输出一份结构化备团整理。

要求：
1. 不要改写剧情，不要新增世界线，只做分析和整理。
2. 明确区分“原文可确认的信息”和“AI 建议”。
3. 尽量提取场景、时间线、NPC、线索、地点、触发条件、潜在断点。
4. 如果资料里没有明确内容，写“未在资料中确认”，不要编。
5. 输出结构请稳定，方便后续转成界面数据。

模组名称：
{module_title}

模组全文资料：
{joined_documents}

请按下面结构输出：

# 备团总览

# 跑团前必须知道

# 时间线

# 场景清单

# NPC 清单

# 关键线索

# 地点与手牌

# 可能卡住的地方

# 跑团前检查清单
"""


def build_revise_prep_section_prompt(
    module_title: str,
    section_title: str,
    section_content: str,
    instruction: str,
) -> str:
    return f"""{SYSTEM_PROMPT}

你正在协助守秘人修改一份备团草稿的单个章节。
这是一段持续编辑中的备团稿，不要重新生成整份文档，只修改当前章节。

要求：
1. 严格保留当前章节主题，不要扩展到其他章节。
2. 根据守秘人的修改要求调整内容。
3. 如果守秘人要求补充细节，可以补充“AI 建议”，但必须明确标注。
4. 不要输出标题，不要输出解释过程，只输出修改后的章节正文。

模组名称：
{module_title}

章节标题：
{section_title}

当前章节正文：
{section_content}

守秘人的修改要求：
{instruction}

请输出修改后的章节正文。
"""
