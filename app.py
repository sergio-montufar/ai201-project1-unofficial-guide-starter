"""
Gradio interface for The Unofficial Guide (Project 1) — Milestone 5.

Stage 5 of the pipeline diagram: a thin UI over query.ask(), showing the
grounded answer plus the sources it was retrieved from.

Run:
    python app.py        # then open the local URL it prints
"""

import gradio as gr

from query import ask


def handle_query(question):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"]) or "(no sources)"
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide — UConn CS") as demo:
    gr.Markdown(
        "# The Unofficial Guide — UConn CS Professors\n"
        "Ask about a UConn computer science professor or course. Answers are "
        "grounded only in collected student reviews (RateMyProfessors, "
        "Coursicle, Reddit)."
    )
    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. How is Derek Aguiar's grading in algorithms?",
    )
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])

    gr.Examples(
        examples=[
            "How is Derek Aguiar's grading in his algorithms class?",
            "Who teaches CSE 2050 Data Structures and what is she like?",
            "Is there a curve in CSE 4300 Operating Systems with Khan?",
        ],
        inputs=inp,
    )


if __name__ == "__main__":
    demo.launch()
