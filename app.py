import streamlit as st
from agent.loop import run

st.set_page_config(page_title="AI Research Agent", page_icon="🔎", layout="centered")

st.title("🔎 AI 研究助手")
st.caption("輸入一個研究主題，自動多輪聯網搜尋並產出帶來源引用的結構化報告。")

topic = st.text_input(
    "研究主題",
    placeholder="例如：What is Model Context Protocol in AI?",
)

if st.button("開始研究", type="primary", disabled=not topic.strip()):
    with st.spinner("正在規劃查詢、聯網搜尋與整理報告（約 30–60 秒）..."):
        report = run(topic.strip())

    # 狀態提示
    if report.status == "failed":
        st.error("本次研究執行失敗，請檢查 API Key 或網路連線後重試。")
    elif report.status == "degraded":
        st.warning("搜尋結果有限，報告內容可能不完整（已觸發降級模式）。")
    else:
        st.success(f"研究完成！共蒐集 {len(report.references)} 個參考來源。")

    # 一、背景
    st.header("背景")
    st.write(report.background or "無相關背景資訊。")

    # 二、關鍵發現
    st.header("關鍵發現")
    if report.findings:
        for i, item in enumerate(report.findings, 1):
            claim = item.get("claim", "")
            source = item.get("source", "")
            if source:
                st.markdown(f"{i}. {claim} （[來源]({source})）")
            else:
                st.markdown(f"{i}. {claim}")
    else:
        st.write("暫無可引用之關鍵發現。")

    # 三、分歧點
    st.header("分歧點")
    if report.disagreements:
        for d in report.disagreements:
            st.markdown(f"- {d}")
    else:
        st.write("目前資料中未發現明顯分歧。")

    # 四、參考連結
    st.header("參考連結")
    if report.references:
        for url in report.references:
            st.markdown(f"- [{url}]({url})")
    else:
        st.write("無參考連結。")

    # 折疊展示 ReAct 執行軌跡
    with st.expander("查看 Agent 思考與搜尋軌跡"):
        for step in report.steps:
            st.markdown(
                f"**Round {step.round} · `{step.action}`** （耗時 `{step.duration_ms} ms`）"
            )
            st.json({"input": step.input, "output": step.output})