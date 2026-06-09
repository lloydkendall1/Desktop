import os

import gradio as gr
from dotenv import load_dotenv

from api_client import (
    get_backend_status,
    get_live_frame,
    get_live_status,
)

load_dotenv()

STUDENT_NAME = os.getenv("STUDENT_NAME", "Lloyd")
API_BASE_URL = os.getenv("SLOUCH_API_BASE_URL", "http://127.0.0.1:8000")
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "127.0.0.1")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "7860"))

theme = gr.themes.Soft(primary_hue="blue", secondary_hue="gray")


def refresh_live():
    """Poll the backend for the latest frames + verdicts (called on a timer)."""
    status = get_live_status()
    verdicts = status.get("verdicts", {})

    if verdicts:
        lines = [
            f"**{cam}**: {v['label']} ({v['confidence'] * 100:.0f}%)"
            for cam, v in verdicts.items()
        ]
        text = "  \n".join(lines)
    else:
        text = "_Waiting for the backend worker to produce frames..._"

    return get_live_frame("front"), get_live_frame("side"), text


with gr.Blocks(title=f"The Slouch Punisher - {STUDENT_NAME}", theme=theme) as demo:
    gr.Markdown("# The Slouch Punisher")
    gr.Markdown(f"Student: **{STUDENT_NAME}**  |  Backend: `{API_BASE_URL}`")

    status_box = gr.Textbox(label="Backend status", interactive=False)
    gr.Button("Check backend connection").click(
        fn=get_backend_status, inputs=None, outputs=status_box
    )

    # --- Tab 1: Setup / onboarding ---
    with gr.Tab("Setup"):
        gr.Markdown("## Getting started")
        with gr.Tab("Step 1"):
            gr.Markdown("Place **camera 1** on your monitor or laptop, facing you head-on.")
        with gr.Tab("Step 2"):
            gr.Markdown("Place **camera 2** to your left, about 1 m away at roughly 45 degrees.")
        with gr.Tab("Step 3"):
            gr.Markdown("Adjust both cameras until your whole upper body is visible in each feed.")
        with gr.Tab("Step 4"):
            gr.Markdown("Make sure the cameras are stable and will not move during use.")
        with gr.Tab("Step 5"):
            gr.Markdown("Sit up straight, then go to the **Live** tab and press **Calibrate**.")

    # --- Tab 2: Live feed (polls the backend worker) ---
    with gr.Tab("Live"):
        gr.Markdown("## Live feed")
        with gr.Row():
            front_img = gr.Image(label="Front camera", type="pil")
            side_img = gr.Image(label="Side camera", type="pil")
        verdict_md = gr.Markdown("_Waiting for the backend worker..._")

        # Fires ~4x/sec and pulls the latest frames + verdicts from the backend.
        live_timer = gr.Timer(0.25)
        live_timer.tick(
            fn=refresh_live,
            inputs=None,
            outputs=[front_img, side_img, verdict_md],
        )

    # --- Tab 3: Stats (wired up in step 5) ---
    with gr.Tab("Stats"):
        gr.Markdown("## Your posture over time")
        gr.Markdown("_Placeholder - charts from the database get wired up in step 5._")

    # --- Tab 4: Settings (wired up in step 5) ---
    with gr.Tab("Settings"):
        gr.Markdown("## Settings")
        gr.Markdown("_Placeholder - these controls get wired up in step 5._")
        gr.Slider(0, 100, value=50, step=1, label="Strictness")


if __name__ == "__main__":
    demo.launch(server_name=FRONTEND_HOST, server_port=FRONTEND_PORT)
