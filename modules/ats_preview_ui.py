"""
ATS rewrite preview UI.

This module keeps the ATS rewrite workflow safe:
1) generate a preview,
2) compare current vs proposed text,
3) accept only after review.
"""

from __future__ import annotations

from typing import Callable, Dict

import streamlit as st


def _as_int(value, default=None):
    try:
        return int(value)
    except Exception:
        return default


def render_ats_rewrite_preview_panel(render_suggestion: Callable[[str, str], None]) -> None:
    """Render preview-first ATS rewrite workflow."""
    st.markdown("---")
    st.markdown("### 🧠 One-Click ATS Rewrite")
    st.caption("Preview-first mode: generate a rewritten draft, compare it with the current resume, then accept or discard.")

    col_btn, col_note = st.columns([1, 2])
    with col_btn:
        generate_preview = st.button(
            "🧠 Generate Rewrite Preview",
            key="ats_generate_rewrite_preview_btn",
            type="primary",
            use_container_width=True,
        )
    with col_note:
        st.info("Resume Builder is not changed until the preview is accepted.")

    if generate_preview:
        try:
            with st.spinner("Generating ATS rewrite preview..."):
                from modules.ats_rewriter import rewrite_resume_from_ats
                from modules.resume_builder import get_resume_data
                from modules.export_utils import resume_data_to_text

                current_resume = get_resume_data()
                current_text = resume_data_to_text(current_resume)
                result = rewrite_resume_from_ats(
                    resume_data=current_resume,
                    parsed_resume=st.session_state.get("parsed_resume"),
                    ats_score=st.session_state.get("ats_score"),
                    jd_match=st.session_state.get("jd_match"),
                )
                result["original_text"] = current_text
                st.session_state.ats_rewrite_preview_result = result
            st.success("✅ Preview generated. Review it before accepting.")
        except Exception as exc:
            st.error(f"Could not generate rewrite preview: {exc}")

    preview = st.session_state.get("ats_rewrite_preview_result")
    if preview:
        _render_preview(preview, render_suggestion)

    accepted = st.session_state.get("ats_rewritten_result")
    if accepted:
        st.markdown("#### ✅ Last accepted rewrite")
        for action in accepted.get("actions", [])[:6]:
            render_suggestion(action, "success")
        _render_latex_download(accepted)


def _render_preview(result: Dict, render_suggestion: Callable[[str, str], None]) -> None:
    st.markdown("#### 👁️ Compare Before Accepting")

    old_score = result.get("old_score", "-")
    new_score = result.get("new_score", "-")
    old_i = _as_int(old_score)
    new_i = _as_int(new_score)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Current ATS Score", old_score)
    with c2:
        st.metric("Preview ATS Score", new_score)
    with c3:
        st.metric("Projected Change", f"{new_i - old_i:+d}" if old_i is not None and new_i is not None else "-")

    left, right = st.columns(2)
    with left:
        st.text_area(
            "Current version",
            value=str(result.get("original_text", "")),
            height=420,
            key="ats_preview_current_text",
            disabled=True,
        )
    with right:
        st.text_area(
            "Preview version",
            value=str(result.get("updated_text", "")),
            height=420,
            key="ats_preview_updated_text",
            disabled=True,
        )

    if result.get("actions"):
        st.markdown("##### Planned improvements")
        for action in result.get("actions", [])[:8]:
            render_suggestion(action, "success")

    if result.get("remaining_issues"):
        with st.expander("Remaining checks before final use", expanded=False):
            for issue in result.get("remaining_issues", [])[:10]:
                render_suggestion(issue, "warning")
            st.warning("Check every placeholder, metric, date, and claim before using the resume.")

    st.download_button(
        "⬇️ Download Preview TXT",
        data=str(result.get("updated_text", "")).encode("utf-8"),
        file_name="ats_rewrite_preview.txt",
        mime="text/plain",
        key="download_ats_preview_txt",
        use_container_width=True,
    )

    a, b = st.columns(2)
    with a:
        if st.button("✅ Accept & Update Resume Builder", key="accept_ats_preview", type="primary", use_container_width=True):
            _accept_preview(result)
    with b:
        if st.button("🗑️ Discard Preview", key="discard_ats_preview", use_container_width=True):
            st.session_state.pop("ats_rewrite_preview_result", None)
            st.info("Preview discarded. Resume Builder was not changed.")
            st.rerun()


def _accept_preview(result: Dict) -> None:
    try:
        from modules.resume_builder import set_resume_data

        set_resume_data(result["resume_data"])
        st.session_state.parsed_resume = result["parsed_resume"]
        st.session_state.ats_score = result["updated_score"]
        st.session_state.ats_rewritten_result = result
        st.session_state.pop("ats_rewrite_preview_result", None)
        st.success("✅ Accepted. Resume Builder and ATS score are updated.")
        st.rerun()
    except Exception as exc:
        st.error(f"Could not accept preview: {exc}")


def _render_latex_download(result: Dict) -> None:
    try:
        from modules.latex_exporter import export_latex_resume, get_latex_filename

        latex_bytes = export_latex_resume(result["resume_data"])
        filename = get_latex_filename(result["resume_data"])
        st.download_button(
            label="⬇️ Download ATS-Optimized LaTeX CV (.tex)",
            data=latex_bytes,
            file_name=filename,
            mime="application/x-tex",
            key="download_ats_rewritten_latex",
            use_container_width=True,
        )
    except Exception as exc:
        st.error(f"Could not prepare LaTeX download: {exc}")
