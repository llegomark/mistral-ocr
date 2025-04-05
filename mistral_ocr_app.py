import gradio as gr
import os
import base64
import requests
from pathlib import Path
import traceback
from mistralai import Mistral, models
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    raise ValueError(
        "MISTRAL_API_KEY environment variable is not set. Please add it to your .env file.")

# Initialize Mistral client
client = Mistral(api_key=api_key)

# Constants
MAX_FILE_SIZE_MB = 50

# Helper Functions


def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    """Replaces image placeholders in Markdown with base64 data URIs."""
    for img_name, base64_str in images_dict.items():
        # Ensure the base64 string is formatted correctly for Markdown image data URI
        if not base64_str.startswith('data:image'):
            # Attempt to infer mime type - default to png if unknown
            mime_type = "image/png"  # Default assumption
            if img_name.lower().endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            elif img_name.lower().endswith(".gif"):
                mime_type = "image/gif"
            # Add more types if necessary
            base64_str = f"data:{mime_type};base64,{base64_str}"

        markdown_str = markdown_str.replace(
            f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})")
    return markdown_str


def get_combined_markdown(ocr_response) -> tuple:
    """Combines Markdown from OCR pages/response, embedding images."""
    markdowns = []
    raw_markdowns = []
    # Check if ocr_response has pages (for multi-page docs like PDF)
    if hasattr(ocr_response, 'pages') and ocr_response.pages:
        for page in ocr_response.pages:
            image_data = {}
            if hasattr(page, 'images') and page.images:
                for img in page.images:
                    # Assumes this is already base64 encoded by Mistral
                    image_data[img.id] = img.image_base64
            markdowns.append(replace_images_in_markdown(
                page.markdown, image_data))
            raw_markdowns.append(page.markdown)
    # Check if ocr_response has markdown directly (single images)
    elif hasattr(ocr_response, 'markdown'):
        image_data = {}
        if hasattr(ocr_response, 'images') and ocr_response.images:
            for img in ocr_response.images:
                image_data[img.id] = img.image_base64
        markdowns.append(replace_images_in_markdown(
            ocr_response.markdown, image_data))
        raw_markdowns.append(ocr_response.markdown)
    else:
        # Handle unexpected response structure
        print("Warning: Unexpected OCR response structure:", ocr_response)
        return "## Error: Could not parse OCR response.", ""

    return "\n\n".join(markdowns), "\n\n".join(raw_markdowns)


def get_content_type(url):
    """Fetch the content type of the URL."""
    try:
        response = requests.head(
            url, allow_redirects=True, timeout=10, stream=True)
        response.raise_for_status()
        return response.headers.get('Content-Type')
    except requests.exceptions.RequestException as e:
        return f"Error fetching content type: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


def check_file_size(file_path):
    """Check if file size is within limits."""
    try:
        file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        return file_size_mb <= MAX_FILE_SIZE_MB, file_size_mb
    except FileNotFoundError:
        return False, "File not found"
    except Exception as e:
        return False, f"Error checking file size: {e}"

# OCR Functions


def perform_ocr_file(file, ocr_method="Mistral OCR"):
    """Performs OCR on an uploaded file using the selected method."""
    if not file:
        return "## Error: No file uploaded.", "No file uploaded."

    temp_path = file
    original_filename = getattr(file, 'name', str(temp_path))
    file_path_obj = Path(original_filename)
    original_file_suffix = file_path_obj.suffix.lower()

    if ocr_method == "Mistral OCR":
        try:
            size_ok, file_size_mb = check_file_size(temp_path)
            if not size_ok:
                if isinstance(file_size_mb, str):
                    return f"## Error checking file size: {file_size_mb}", ""
                else:
                    return f"## Error: File too large ({file_size_mb:.1f}MB). Max is {MAX_FILE_SIZE_MB}MB.", ""

            uploaded_pdf = None
            if original_file_suffix == '.pdf':
                # Process PDF
                try:
                    with open(temp_path, "rb") as f:
                        uploaded_pdf = client.files.upload(
                            file={"file_name": original_filename, "content": f},
                            purpose="ocr"
                        )
                    signed_url = client.files.get_signed_url(
                        file_id=uploaded_pdf.id)
                    ocr_response = client.ocr.process(
                        model="mistral-ocr-latest",
                        document={"type": "document_url",
                                  "document_url": signed_url.url},
                        include_image_base64=True
                    )
                    client.files.delete(file_id=uploaded_pdf.id)

                except models.SDKError as e:
                    if uploaded_pdf:
                        try:
                            client.files.delete(file_id=uploaded_pdf.id)
                        except Exception as cleanup_e:
                            print(
                                f"Warning: Failed cleanup {uploaded_pdf.id}: {cleanup_e}")
                    return f"## Mistral API Error: {str(e)}", ""

            elif original_file_suffix in ['.png', '.jpg', '.jpeg']:
                # Process image
                try:
                    with open(temp_path, "rb") as image_file:
                        base64_image = base64.b64encode(
                            image_file.read()).decode('utf-8')

                    mime_type = "image/png"
                    if original_file_suffix in ['.jpg', '.jpeg']:
                        mime_type = "image/jpeg"

                    ocr_response = client.ocr.process(
                        model="mistral-ocr-latest",
                        document={
                            "type": "image_url", "image_url": f"data:{mime_type};base64,{base64_image}"},
                        include_image_base64=True
                    )
                except models.SDKError as e:
                    return f"## Mistral API Error: {str(e)}", ""
            else:
                return f"## Error: Unsupported file format ({original_file_suffix}). Please upload PDF, PNG, JPG, JPEG.", ""

            combined_markdown, raw_markdown = get_combined_markdown(
                ocr_response)
            return combined_markdown, raw_markdown

        except FileNotFoundError:
            return f"## Error: Temporary file not found: {temp_path}. Gradio issue?", ""
        except Exception as e:
            print(f"Unexpected error in perform_ocr_file: {e}")
            return f"## Error: An unexpected error occurred.\n\n{traceback.format_exc()}", ""

    return "## Method not supported.", "Method not supported."


def perform_ocr_url(url, ocr_method="Mistral OCR"):
    """Performs OCR on a URL using the selected method."""
    if not url or not url.strip():
        return "## Error: No URL provided.", ""

    if ocr_method == "Mistral OCR":
        try:
            if not url.lower().startswith(('http://', 'https://')):
                return "## Error: Invalid URL scheme. Use http:// or https://.", ""

            content_type_result = get_content_type(url)

            if isinstance(content_type_result, str) and content_type_result.startswith("Error"):
                return f"## Error: Could not fetch URL details. {content_type_result}", ""
            elif not isinstance(content_type_result, str):
                return "## Error: Could not determine content type for URL.", ""

            content_type = content_type_result.lower().split(';')[0].strip()

            if content_type == 'application/pdf':
                try:
                    ocr_response = client.ocr.process(
                        model="mistral-ocr-latest",
                        document={"type": "document_url", "document_url": url},
                        include_image_base64=True
                    )
                except models.SDKError as e:
                    return f"## Mistral API Error (PDF URL): {str(e)}", ""

            elif content_type in ['image/png', 'image/jpeg', 'image/jpg']:
                try:
                    ocr_response = client.ocr.process(
                        model="mistral-ocr-latest",
                        document={"type": "image_url", "image_url": url},
                        include_image_base64=True
                    )
                except models.SDKError as e:
                    return f"## Mistral API Error (Image URL): {str(e)}", ""
            else:
                error_msg = f"Unsupported type at URL: '{content_type}'. Use PDF, PNG, JPG, JPEG."
                return f"## Error: {error_msg}", ""

            combined_markdown, raw_markdown = get_combined_markdown(
                ocr_response)
            return combined_markdown, raw_markdown

        except Exception as e:
            print(f"Unexpected error in perform_ocr_url: {e}")
            return f"## Error: An unexpected error occurred.\n\n{traceback.format_exc()}", ""

    return "## Method not supported.", "Method not supported."


# Gradio Interface
with gr.Blocks(css="""
    .gradio-container { font-family: 'Helvetica', 'Arial', sans-serif !important; }
    h1, h2, h3 { font-family: 'Helvetica', 'Arial', sans-serif !important; }
""") as demo:
    gr.Markdown("# Mistral OCR")
    gr.Markdown(
        "Upload a PDF/Image or provide a URL for OCR using Mistral.\n\nBlog post [here](https://mistral.ai/news/mistral-ocr).")

    with gr.Tab("Upload File"):
        file_input = gr.File(
            label=f"Upload PDF or Image (Max {MAX_FILE_SIZE_MB}MB)", type="filepath")
        ocr_method_file = gr.Dropdown(
            choices=["Mistral OCR"], label="Select OCR Method", value="Mistral OCR")
        file_output = gr.Markdown(label="Rendered Markdown")
        file_raw_output = gr.Textbox(label="Raw Markdown", lines=10)
        file_button = gr.Button("Process Uploaded File")

        file_button.click(
            fn=perform_ocr_file,
            inputs=[file_input, ocr_method_file],
            outputs=[file_output, file_raw_output]
        )

    with gr.Tab("Enter URL"):
        url_input = gr.Textbox(label="Enter URL to PDF or Image",
                               placeholder="e.g., https://arxiv.org/pdf/1706.03762")
        ocr_method_url = gr.Dropdown(
            choices=["Mistral OCR"], label="Select OCR Method", value="Mistral OCR")
        url_output = gr.Markdown(label="Rendered Markdown")
        url_raw_output = gr.Textbox(label="Raw Markdown", lines=10)
        url_button = gr.Button("Process URL")

        gr.Examples(
            examples=[
                ["https://arxiv.org/pdf/1706.03762", "Mistral OCR"],
            ],
            inputs=[url_input, ocr_method_url],
            outputs=[url_output, url_raw_output],
            fn=perform_ocr_url
        )

        url_button.click(
            fn=perform_ocr_url,
            inputs=[url_input, ocr_method_url],
            outputs=[url_output, url_raw_output]
        )

# Launch the application
demo.launch(max_threads=1)
