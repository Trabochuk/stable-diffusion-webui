import gradio as gr
from modules import scripts, shared, ui_common, postprocessing, call_queue, ui_toprow
import modules.infotext_utils as parameters_copypaste
from modules.ui_components import ResizeHandleRow


def hook_scale_update(inputs):
    import re
    pattern = r'(\d)[xX]|[xX](\d)'

    resize = upscaler = None
    for script in inputs:
        if script.label == "Resize":
            resize = script
        elif script.label == "Upscaler 1":
            upscaler = script
        elif resize and upscaler:
            break

    def update_scale(upscaler: str, slider: float):
        match = re.search(pattern, upscaler)

        if match:
            if match.group(1):
                return gr.update(value=int(match.group(1)))

            else:
                return gr.update(value=int(match.group(2)))

        else:
            return gr.update(value=slider)

    if resize and upscaler:
        upscaler.input(update_scale, inputs=[upscaler, resize], outputs=[resize])


def create_ui():
    dummy_component = gr.Label(visible=False)
    tab_index = gr.Number(value=0, visible=False)

    with ResizeHandleRow(equal_height=False, variant='compact'):
        with gr.Column(variant='compact'):
            with gr.Tabs(elem_id="mode_extras"):
                with gr.TabItem('Single Image', id="single_image", elem_id="extras_single_tab") as tab_single:
                    extras_image = gr.Image(label="Source", source="upload", interactive=True, type="pil", elem_id="extras_image")

                with gr.TabItem('Batch Process', id="batch_process", elem_id="extras_batch_process_tab") as tab_batch:
                    image_batch = gr.Files(label="Batch Process", interactive=True, elem_id="extras_image_batch")

                with gr.TabItem('Batch from Directory', id="batch_from_directory", elem_id="extras_batch_directory_tab") as tab_batch_dir:
                    extras_batch_input_dir = gr.Textbox(label="Input directory", **shared.hide_dirs, placeholder="A directory on the same machine where the server is running.", elem_id="extras_batch_input_dir")
                    extras_batch_output_dir = gr.Textbox(label="Output directory", **shared.hide_dirs, placeholder="Leave blank to save images to the default path.", elem_id="extras_batch_output_dir")
                    show_extras_results = gr.Checkbox(label='Show result images', value=True, elem_id="extras_show_extras_results")

            script_inputs = scripts.scripts_postproc.setup_ui()
            hook_scale_update(script_inputs)

        with gr.Column():
            toprow = ui_toprow.Toprow(is_compact=True, is_img2img=False, id_part="extras")
            toprow.create_inline_toprow_image()
            submit = toprow.submit

            output_panel = ui_common.create_output_panel("extras", shared.opts.outdir_extras_samples)

    tab_single.select(fn=lambda: 0, inputs=[], outputs=[tab_index])
    tab_batch.select(fn=lambda: 1, inputs=[], outputs=[tab_index])
    tab_batch_dir.select(fn=lambda: 2, inputs=[], outputs=[tab_index])

    submit.click(
        fn=call_queue.wrap_gradio_gpu_call(postprocessing.run_postprocessing_webui, extra_outputs=[None, '']),
        _js="submit_extras",
        inputs=[
            dummy_component,
            tab_index,
            extras_image,
            image_batch,
            extras_batch_input_dir,
            extras_batch_output_dir,
            show_extras_results,
            *script_inputs
        ],
        outputs=[
            output_panel.gallery,
            output_panel.generation_info,
            output_panel.html_log,
        ],
        show_progress=False,
    )

    parameters_copypaste.add_paste_fields("extras", extras_image, None)

    extras_image.change(
        fn=scripts.scripts_postproc.image_changed,
        inputs=[], outputs=[]
    )
