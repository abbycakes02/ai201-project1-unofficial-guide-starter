"""
app.py — Milestone 5: Gradio query interface for The Unofficial Guide.

A minimal web UI: type a question about UC Berkeley dining, get a grounded answer
plus the list of source documents it was drawn from. The "Retrieved from" box shows
attribution built programmatically from chunk metadata (see query.py).

Run:
    python app.py
then open http://localhost:7860
"""

from __future__ import annotations

import gradio as gr

from query import ask

EXAMPLES = [
    "What unique food items can you get at Crossroads?",
    "How many flex dollars does the Gold meal plan include?",
    "Why do students say Clark Kerr is inconvenient despite the food?",
    "Do students agree on whether Cafe 3 is a good dining hall?",
    "What's the best dining hall at UC Berkeley?",
]


def handle_query(question: str):
    """Run one query through the RAG pipeline and format outputs for the UI."""
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", ""

    result = ask(question)
    answer = result["answer"]
    if result["sources"]:
        sources = "\n".join(f"• {s}" for s in result["sources"])
    else:
        sources = "(no sources retrieved)"
    return answer, sources


with gr.Blocks(title="The Unofficial Guide — UC Berkeley Dining") as demo:
    gr.Markdown(
        "# 🍽️ The Unofficial Guide — UC Berkeley Dining\n"
        "Ask about the dining halls (Crossroads, Cafe 3, Clark Kerr, Foothill), "
        "meal plans, and campus food. Answers are grounded in real student reviews "
        "and guides — if the documents don't cover it, the guide will say so."
    )
    inp = gr.Textbox(label="Your question", placeholder="e.g. What's the best dining hall?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from", lines=4)

    gr.Examples(examples=EXAMPLES, inputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
