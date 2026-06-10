from app.components.human_labels import human_label, human_labels


def test_human_label_translates_required_codes() -> None:
    assert human_label("manual_only_no_exact_model_baseline") == (
        "Manual only: no reliable baseline"
    )
    assert human_label("review_only_no_final_recommendation") == "Review only"
    assert human_label("review_only_no_cut_keep_recommendation") == "No cut/keep call"
    assert human_label("review_only_no_trade_recommendation") == "No trade call"
    assert human_label("source_shape_warning") == "Data shape warning"
    assert human_label("model_edge_weirdness") == "Model edge"
    assert human_label("one_qb_qb_scarcity_cap") == "1QB value cap"
    assert human_label("rb_age_cliff_guardrail_unavailable") == (
        "RB age-risk check needed"
    )
    assert human_label("rb_dynasty_age_curve_30_plus_active") == (
        "RB 30-plus age cliff active"
    )
    assert human_label("te_age_33_plus_cliff_active") == "TE 33-plus age cliff active"
    assert human_label("wr_mid_30s_age_cliff_active") == "WR mid-30s age cliff active"


def test_human_labels_preserves_unknown_codes_safely() -> None:
    assert human_label("brand_new_warning_code") == "Brand new warning code"
    assert human_labels("review_only_no_trade_recommendation|brand_new_warning_code") == (
        "No trade call; Brand new warning code"
    )
    assert human_label("model_edge_weirdness:day_three_exceptional_profile") == (
        "Model edge: Day three exceptional profile"
    )
