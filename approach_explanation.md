# Persona-Driven Document Intelligence with Gemini AI

This project automatically extracts the most relevant sections from PDF documents using h1 (largest font) headings, ranks them according to a provided persona and task (JTBD), and summarizes them with the help of Google's Gemini AI via the official Generative AI SDK.

---

## Project Structure

project-root/
├── documents_1/
│ ├── PDFs/
│ │ ├── your-document-1.pdf
│ │ ├── your-document-2.pdf
│ ├── inputs.json
│ ├── output.json
├── documents_2/
│ ...
├── documents_3/
│ ...
├── main.py
├── requirements.txt
├── Dockerfile
├── README.md
└── .env # (Optional for local dev, holds GOOGLE_API_KEY)


---

## Inputs & Outputs

- **inputs.json:** Specifies which PDFs to analyze, and includes the persona and job-to-be-done (JTBD).
- **PDFs folder:** All PDFs listed in `inputs.json` must be present here.
- **output.json:** Script will write extracted sections and their summaries (from Gemini) in the target structure here.

---

## How It Works: Approach

1. **Section Extraction with PyMuPDF**:  
   For each PDF, PyMuPDF reads each page and detects h1 (top-level) headings by identifying text blocks with the largest font size. Each heading and its associated text become a "section."

2. **Prompt Building for Gemini**:  
   The script builds a prompt that includes:
   - The persona (role) and the user's target job-to-be-done (JTBD)
   - The document name
   - All detected sections (h1 + text)

3. **Relevance & Summarization via Gemini**:  
   Gemini AI receives the prompt and returns a JSON array of the most relevant sections, ranked and summarized, per your requested schema.

4. **Final Output**:  
   For each `documents_X` collection, the script writes a single `output.json` summarizing the most relevant section per document, up to a max of 5 (configurable), with concise summaries and ranking.

---

## Requirements

- Python 3.9 or newer (Docker handles this)
- Google Cloud API key with access to Gemini (store as env GOOGLE_API_KEY)
- Supported Google Generative AI model (e.g., `gemini-2.0-flash`)

---

## Quick Start

### 1. Build Docker Image

First, ensure your `.env` file (if present) contains your API key:

GOOGLE_API_KEY=your_api_key_here

text

Then build the Docker image:

docker build -t persona-doc-intel .

text

### 2. Run the Container

You can run the analysis for any inputs folder by mounting the project and specifying input/output, for example:

docker run --rm
-v $(pwd):/workspace
-e GOOGLE_API_KEY="$GOOGLE_API_KEY"
persona-doc-intel
--input_folder documents_1 --output_file documents_1/output.json

text

- Replace `documents_1` as needed for each test collection.
- The script will read PDFs and `inputs.json` from that folder, write output to `output.json`.

---

## Troubleshooting

- Ensure your `inputs.json` filenames **exactly** match PDFs placed in the `PDFs/` subfolder.
- Make sure your Google API key (`GOOGLE_API_KEY`) is valid and enabled for Gemini models.
- If Gemini's output isn't perfectly formatted JSON, the script will attempt to extract and parse JSON content from its responses.
- For debugging, the script prints raw Gemini responses.

---

## Security

- **API Key Security:** Do not commit your `.env` or API key to version control. Use environment variables or Docker secrets in production.

---

## Example Command

To process the second collection:

docker run --rm
-v $(pwd):/workspace
-e GOOGLE_API_KEY="$GOOGLE_API_KEY"
persona-doc-intel
--input_folder documents_2 --output_file documents_2/output.json

text

---

## Dependencies

List in `requirements.txt`:

PyMuPDF
sentence-transformers
numpy
google-ai-generativelanguage
python-dotenv

text

---

## Customizing

- Adjust `TOP_N_RESULTS` in `main.py` to change how many sections appear per output.
- Refine section extraction by editing `extract_sections_from_pdf`.
- Prompt engineering: Tune the system prompt in `build_prompt` for Gemini.

---