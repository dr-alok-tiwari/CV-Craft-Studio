# CV-Craft-Studio - Modules Package

from __future__ import annotations


def _install_ats_draft_panel() -> None:
    """Route the ATS action panel to a review-first draft workflow."""
    try:
        from . import ui_components as _ui

        def _review_first_panel():
            try:
                import streamlit as st
                from modules.ats_preview_ui import render_ats_rewrite_preview_panel

                if not _ui._is_ats_page() or not st.session_state.get("ats_score"):
                    return
                render_ats_rewrite_preview_panel(_ui.render_suggestion)
            except Exception as exc:
                _ui.st.error(f"Could not load ATS draft preview: {exc}")

        _ui.render_ats_rewrite_panel = _review_first_panel
    except Exception:
        pass


_install_ats_draft_panel()
