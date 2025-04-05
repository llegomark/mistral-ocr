# Mistral OCR Application

A Gradio-based web interface for document OCR and understanding using Mistral AI's state-of-the-art OCR capabilities.

## Overview

This application provides a powerful interface to Mistral's Optical Character Recognition technology. It allows you to extract text and images from PDFs and images with unprecedented accuracy while maintaining document structure.

## Features

- **Advanced Document Processing**: Extract text while maintaining document structure and hierarchy
- **Image Extraction**: Preserves and extracts embedded images from documents
- **Multiple Input Methods**: Process files via upload or URL
- **Multilingual Support**: Process documents in multiple languages with high accuracy
- **Formatted Output**: Results in clean, well-formatted markdown

## Key Capabilities

- Extracts text content while maintaining document structure and hierarchy
- Preserves formatting like headers, paragraphs, lists and tables
- Returns results in markdown format for easy parsing and rendering
- Handles complex layouts including multi-column text and mixed content
- Processes documents at scale with high accuracy
- Supports multiple document formats including PDF, images, and uploaded documents

## Installation

### Prerequisites

- Python 3.12+
- A Mistral AI API key ([Get one here](https://console.mistral.ai/api-keys))

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/llegomark/mistral-ocr.git
   cd mistral-ocr
   ```

2. Install dependencies:
   ```bash
   pip install gradio requests mistralai python-dotenv
   ```

3. Create a `.env` file in the project directory:
   ```
   MISTRAL_API_KEY=your_api_key_here
   ```

## Usage

1. Run the application:
   ```bash
   python mistral_ocr_app.py
   ```

2. Open your browser and navigate to `http://127.0.0.1:7860`

3. Use the application through one of two tabs:
   - **Upload File**: Upload PDFs or images for OCR processing
   - **Enter URL**: Provide a URL to a PDF or image for OCR processing

## Technical Performance

Mistral OCR outperforms other leading OCR solutions in rigorous benchmarks:

| Model | Overall | Math | Multilingual | Scanned | Tables |
|-------|---------|------|--------------|---------|--------|
| Google Document AI | 83.42 | 80.29 | 86.42 | 92.77 | 78.16 |
| Azure OCR | 89.52 | 85.72 | 87.52 | 94.65 | 89.52 |
| Gemini-1.5-Flash-002 | 90.23 | 89.11 | 86.76 | 94.87 | 90.48 |
| Gemini-1.5-Pro-002 | 89.92 | 88.48 | 86.33 | 96.15 | 89.71 |
| Gemini-2.0-Flash-001 | 88.69 | 84.18 | 85.80 | 95.11 | 91.46 |
| GPT-4o-2024-11-20 | 89.77 | 87.55 | 86.00 | 94.58 | 91.70 |
| Mistral OCR 2503 | 94.89 | 94.29 | 89.55 | 98.96 | 96.12 |

## Example Usage

### Processing a PDF:
1. Upload a PDF file using the "Upload File" tab
2. Click "Process Uploaded File"
3. View the extracted text and images in the output

## Use Cases

This application can be used for various document processing tasks:

- **Digitizing Scientific Research**: Convert papers and journals into AI-ready formats
- **Historical Document Preservation**: Digitize and make accessible historical documents
- **Customer Service Enhancement**: Transform documentation into indexed knowledge
- **Educational Content**: Convert lecture notes, presentations into searchable formats
- **Legal Document Processing**: Extract information from regulatory filings and legal documents

## Resources

- [Mistral OCR Documentation](https://docs.mistral.ai/capabilities/document/)
- [Mistral OCR Blog Post](https://mistral.ai/news/mistral-ocr)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.