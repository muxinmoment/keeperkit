from dataclasses import dataclass


@dataclass(frozen=True)
class QueryRewrite:
    original_question: str
    retrieval_question: str
    matched_terms: list[str]
    added_terms: list[str]


SLANG_EXPANSIONS: dict[str, list[str]] = {
    "车卡": ["创建调查员", "角色创建", "调查员创建", "属性", "技能", "职业", "背景"],
    "撕卡": ["调查员死亡", "死亡", "濒死", "疯狂", "失去调查员"],
    "kp": ["守秘人", "主持人", "主持游戏"],
    "守秘": ["守秘人", "主持游戏"],
    "sc": ["理智检定", "理智损失", "SAN"],
    "san": ["理智", "理智值", "理智检定", "SAN"],
    "大成功": ["极难成功", "大成功", "检定等级"],
    "大失败": ["大失败", "失败", "检定"],
    "mp": ["魔法值", "魔法值恢复", "施法消耗"],
    "db": ["伤害加值", "体格", "力量", "体型"],
    "体格": ["体格", "伤害加值", "力量", "体型"],
    "战技": ["战技", "战斗技艺", "近战", "反击", "闪避"],
}


def rewrite_rule_query(question: str) -> QueryRewrite:
    normalized_question = question.strip()
    lowered_question = normalized_question.lower()
    matched_terms: list[str] = []
    added_terms: list[str] = []

    for term, expansions in SLANG_EXPANSIONS.items():
        if term.lower() not in lowered_question:
            continue
        matched_terms.append(term)
        for expansion in expansions:
            if expansion not in added_terms and expansion.lower() not in lowered_question:
                added_terms.append(expansion)

    if not added_terms:
        return QueryRewrite(
            original_question=normalized_question,
            retrieval_question=normalized_question,
            matched_terms=[],
            added_terms=[],
        )

    retrieval_question = (
        f"{normalized_question}\n"
        f"检索补充词：{'、'.join(added_terms)}"
    )
    return QueryRewrite(
        original_question=normalized_question,
        retrieval_question=retrieval_question,
        matched_terms=matched_terms,
        added_terms=added_terms,
    )
