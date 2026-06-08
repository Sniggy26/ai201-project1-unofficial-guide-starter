import gradio as gr
from query import ask

def handle_query(question):
    """Handle a student question and return answer + sources."""
    if not question.strip():
        return "Please type a question first.", ""

    result = ask(question)
    answer = result["answer"]
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return answer, sources


# Build the Gradio UI
with gr.Blocks(title="GSU Unofficial Campus Survival Guide") as demo:

    gr.Markdown("""
    # 🐾 GSU Unofficial Campus Survival Guide
    Ask anything about MARTA passes, PAWS, financial aid, advising, housing, dining, safety, and more.
    Answers are grounded in real GSU student knowledge — no hallucinations.
    """)

    with gr.Row():
        with gr.Column(scale=3):
            question_input = gr.Textbox(
                label="Your Question",
                placeholder="e.g. How do I get a discounted MARTA pass?",
                lines=2
            )
        with gr.Column(scale=1):
            ask_btn = gr.Button("Ask 🔍", variant="primary", size="lg")

    with gr.Row():
        answer_output = gr.Textbox(
            label="Answer",
            lines=10,
            interactive=False
        )

    with gr.Row():
        sources_output = gr.Textbox(
            label="Retrieved from",
            lines=3,
            interactive=False
        )

    gr.Markdown("""
    ### Example questions to try:
    - How do I get a discounted MARTA pass as a GSU student?
    - What should I do if I have a hold on my PAWS account?
    - How do I accept my financial aid award at GSU?
    - Where do I go for academic advising as a new student?
    - What safety resources does GSU offer for students in downtown Atlanta?
    - What dining options are available on campus?
    - How do I find a roommate for off-campus housing?
    """)

    # Wire up button and Enter key
    ask_btn.click(
        fn=handle_query,
        inputs=question_input,
        outputs=[answer_output, sources_output]
    )
    question_input.submit(
        fn=handle_query,
        inputs=question_input,
        outputs=[answer_output, sources_output]
    )

if __name__ == "__main__":
    print("Starting GSU Unofficial Guide...")
    print("Open http://localhost:7860 in your browser")
    demo.launch()
