import streamlit as st
from agent.loop import run

st.set_page_config(page_title="AI Research Agent", page_icon="🔎", layout="centered")

TEXTS = {
    "en": {
        "title": "🔎 AI Research Agent",
        "subtitle": "Enter a research topic to run multi-round web searches and generate a structured report with citations.",
        "input_label": "Research Topic",
        "input_placeholder": "e.g., SQLite vs PostgreSQL for small web apps",
        "run_btn": "Start Research",
        "empty_warn": "Please enter a research topic first.",
        "spinner": "Searching the web and synthesizing report (max 3 rounds)...",
        "status_ok": "Status: Completed (ok)",
        "status_degraded": "Status: Degraded — limited search results or fallback formatting triggered.",
        "status_failed": "Status: Failed — an internal error occurred.",
        "sec_bg": "1. Background",
        "sec_findings": "2. Key Findings",
        "sec_disagreements": "3. Disagreements & Trade-offs",
        "sec_refs": "4. References",
        "source_label": "Source",
        "no_data": "No data available.",
        "trace_title": "Execution Trace (ReAct Steps)",
        "step_fmt": "Round {round} · {action} ({ms} ms)",
    },
    "zh": {
        "title": "🔎 AI 研究助手",
        "subtitle": "输入一个研究主题，自动执行多轮联网搜索并生成带来源引用的结构化报告。",
        "input_label": "研究主题",
        "input_placeholder": "例如：SQLite vs PostgreSQL 在小型 Web 应用中的对比",
        "run_btn": "开始研究",
        "empty_warn": "请先输入一个研究主题。",
        "spinner": "正在联网搜索并生成报告（最多 3 轮）...",
        "status_ok": "状态：完成 (ok)",
        "status_degraded": "状态：降级 (degraded) — 搜索结果不足或触发了兜底解析。",
        "status_failed": "状态：失败 (failed) — 运行过程中发生内部异常。",
        "sec_bg": "1. 背景",
        "sec_findings": "2. 关键发现",
        "sec_disagreements": "3. 分歧点",
        "sec_refs": "4. 参考链接",
        "source_label": "来源",
        "no_data": "暂无内容。",
        "trace_title": "执行轨迹（ReAct 步骤）",
        "step_fmt": "第 {round} 轮 · {action}（耗时 {ms} ms）",
    },
}

# 顶部语言切换（默认英文，方便简历展示）
col_title, col_lang = st.columns([4, 1])
with col_lang:
    lang_choice = st.segmented_control(
        "Language",
        options=["EN", "中文"],
        default="EN",
        label_visibility="collapsed",
    )
lang = "zh" if lang_choice == "中文" else "en"
t = TEXTS[lang]

with col_title:
    st.title(t["title"])
st.caption(t["subtitle"])

topic = st.text_input(t["input_label"], placeholder=t["input_placeholder"])

if st.button(t["run_btn"], type="primary"):
    if not topic.strip():
        st.warning(t["empty_warn"])
    else:
        with st.spinner(t["spinner"]):
            report = run(topic.strip())

        if report.status == "ok":
            st.success(t["status_ok"])
        elif report.status == "degraded":
            st.warning(t["status_degraded"])
        else:
            st.error(t["status_failed"])

        st.subheader(t["sec_bg"])
        st.write(report.background or t["no_data"])

        st.subheader(t["sec_findings"])
        if report.findings:
            for item in report.findings:
                claim = item.get("claim", "")
                source = item.get("source", "")
                if source:
                    st.markdown(f"- {claim} ([{t['source_label']}]({source}))")
                else:
                    st.markdown(f"- {claim}")
        else:
            st.write(t["no_data"])

        st.subheader(t["sec_disagreements"])
        if report.disagreements:
            for d in report.disagreements:
                st.markdown(f"- {d}")
        else:
            st.write(t["no_data"])

        st.subheader(t["sec_refs"])
        if report.references:
            for url in report.references:
                st.markdown(f"- [{url}]({url})")
        else:
            st.write(t["no_data"])

        with st.expander(t["trace_title"]):
            for s in report.steps:
                st.markdown(
                    f"**{t['step_fmt'].format(round=s.round, action=s.action, ms=s.duration_ms)}**"
                )
                st.json({"input": s.input, "output": s.output})
