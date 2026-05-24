from app.rag.query_rewriter import rewrite_rule_query
from app.services.rule_qa_service import build_query_notes


def test_rewrite_rule_query_expands_character_creation_slang() -> None:
    rewrite = rewrite_rule_query("新手怎么车卡？")

    assert rewrite.original_question == "新手怎么车卡？"
    assert "车卡" in rewrite.matched_terms
    assert "创建调查员" in rewrite.added_terms
    assert "角色创建" in rewrite.added_terms
    assert "检索补充词" in rewrite.retrieval_question


def test_rewrite_rule_query_keeps_plain_question_unchanged() -> None:
    rewrite = rewrite_rule_query("奖励骰和惩罚骰怎么计算？")

    assert rewrite.retrieval_question == "奖励骰和惩罚骰怎么计算？"
    assert rewrite.matched_terms == []
    assert rewrite.added_terms == []


def test_build_query_notes_describes_slang_expansion() -> None:
    notes = build_query_notes(["车卡"], ["创建调查员", "角色创建"])

    assert notes == [
        "用户问题包含常见 TRPG 黑话：车卡；检索时已补充规则书常用说法：创建调查员、角色创建。"
    ]
