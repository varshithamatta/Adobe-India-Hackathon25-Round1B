import fitz  # PyMuPDF
import json
import os
import sys
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime

# Gemini API import (official Google Generative AI Python SDK)
import google.generativeai as genai

# ---------------- CONFIG ----------------
EMBEDDING_MODEL = "gemini-2.0-flash"  # Updated Gemini model name for Gemini 2.0 API
TOP_N_RESULTS = 5  # Number of top relevant sections overall to return

# ---------------- PDF Section Extraction ----------------

def extract_sections_from_pdf(pdf_path):
    """
    Extract sections from a PDF by treating largest font text on each page as an h1 heading (section title),
    and the rest of the page text under that heading as the section text.
    """
    doc = fitz.open(pdf_path)
    sections = []

    for page_num in range(doc.page_count):
        page = doc[page_num]

        blocks = page.get_text("dict")["blocks"]
        if not blocks:
            continue

        max_fontsize = 0
        block_font_info = []

        # Gather max font size per block and combined text
        for block in blocks:
            if block["type"] != 0:  # 0 = text blocks
                continue
            max_block_fontsize = 0
            block_text_pieces = []
            for line in block["lines"]:
                for span in line["spans"]:
                    font_size = span["size"]
                    text = span["text"].strip()
                    if font_size > max_block_fontsize:
                        max_block_fontsize = font_size
                    if text:
                        block_text_pieces.append(text)
            block_text = " ".join(block_text_pieces).strip()
            block_font_info.append((max_block_fontsize, block_text))
            if max_block_fontsize > max_fontsize:
                max_fontsize = max_block_fontsize

        # Identify all blocks with max font size as potential h1 headings
        section_titles = [text for fontsize, text in block_font_info if abs(fontsize - max_fontsize) < 0.01 and text]

        if not section_titles:
            # No heading found, fallback: use "Page N"
            full_text = page.get_text("text").strip()
            sections.append({
                "document": os.path.basename(pdf_path),
                "page_number": page_num + 1,
                "section_title": f"Page {page_num + 1}",
                "section_text": full_text
            })
            continue

        # Use first h1 as section title
        h1_title = section_titles[0]
        full_text = page.get_text("text").strip()
        
        # Remove heading text if at start
        if full_text.startswith(h1_title):
            section_text = full_text[len(h1_title):].strip()
        else:
            section_text = full_text

        sections.append({
            "document": os.path.basename(pdf_path),
            "page_number": page_num + 1,
            "section_title": h1_title,
            "section_text": section_text
        })

    return sections

# ---------------- Gemini API Invocation ----------------

def init_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: Set environment variable GOOGLE_API_KEY with your Gemini API Key")
        sys.exit(1)
    genai.configure(api_key=api_key)
    return genai

def build_prompt(persona, jtbd, sections, document_name):
    prompt = f"""
You are an intelligent document analyst.  
Persona: {persona}  
Task: {jtbd}  
Document: {document_name}  

Extract and rank the most relevant sections related to the task, providing for each:  
- section_title (h1 heading)  
- page_number  
- a concise summary focused on the persona's job-to-be-done.  

Return a JSON array where each entry is an object with keys:  
"section_title", "page_number", and "summary".  

Here are the sections:  

"""

    # Append sections with headings and texts (limit size)
    for sec in sections:
        prompt += f"\nSection Title: {sec['section_title']} (Page {sec['page_number']})\n"
        sec_text = sec['section_text']
        if len(sec_text) > 1200:
            sec_text = sec_text[:1200] + "..."
        prompt += sec_text + "\n"

    prompt += "\nPlease respond with the JSON array only."

    return prompt

def query_gemini(client, prompt, model_name=EMBEDDING_MODEL):
    try:
        model = client.GenerativeModel(model_name)
        response = model.generate_content(prompt, generation_config={
            "temperature": 0,
            "max_output_tokens": 1500
        })
        text_output = response.text.strip()

        # Attempt to parse JSON from output
        try:
            json_output = json.loads(text_output)
            return json_output
        except json.JSONDecodeError:
            print("Warning: Could not parse Gemini response as JSON. Returning raw text.")
            return text_output
    except Exception as e:
        print(f"Gemini API call failed with error: {e}")
        return None

# ---------------- MAIN PROCESS ----------------

def main(input_folder, output_path):
    input_json_path = os.path.join(input_folder, "inputs.json")
    pdf_folder = os.path.join(input_folder, "PDFs")

    if not os.path.isfile(input_json_path):
        print(f"Error: Cannot find inputs.json in {input_folder}")
        sys.exit(1)
    if not os.path.isdir(pdf_folder):
        print(f"Error: PDFs folder not found at expected location: {pdf_folder}")
        sys.exit(1)

    with open(input_json_path, "r", encoding="utf-8") as f:
        input_data = json.load(f)

    persona = input_data.get("persona", {}).get("role", "Unknown Persona")
    jtbd = input_data.get("job_to_be_done", {}).get("task", "Unknown Task")

    documents_meta = input_data.get("documents", [])
    if not documents_meta:
        print("Error: No documents listed in inputs.json")
        sys.exit(1)

    client = init_gemini_client()

    all_sections = []  # Collect all sections from all PDFs first
    all_subsection_analysis = []

    for doc_meta in documents_meta:
        filename = doc_meta.get("filename")
        if not filename:
            continue
        pdf_path = os.path.join(pdf_folder, filename)
        if not os.path.isfile(pdf_path):
            print(f"Warning: PDF file not found: {filename} — skipping")
            continue

        print(f"Processing {filename}...")

        sections = extract_sections_from_pdf(pdf_path)
        if not sections:
            print(f"No sections extracted from {filename}")
            continue

        prompt = build_prompt(persona, jtbd, sections, filename)
        gemini_response = query_gemini(client, prompt)

        if not gemini_response:
            print(f"No valid response for {filename}, skipping...")
            continue


        # If response is string, try to parse as JSON, or extract JSON array using regex
        if isinstance(gemini_response, str):
            import re
            try:
                parsed = json.loads(gemini_response)
                gemini_response = parsed
            except Exception:
                # Try to extract JSON array from text
                match = re.search(r'(\[.*?\])', gemini_response, re.DOTALL)
                if match:
                    try:
                        gemini_response = json.loads(match.group(1))
                    except Exception:
                        print(f"Gemini response for {filename} could not be parsed after regex extraction:\n{gemini_response}")
                        continue
                else:
                    print(f"Gemini response for {filename} was not JSON and no array found:\n{gemini_response}")
                    continue

        # Only process if there are relevant sections
        if isinstance(gemini_response, list) and len(gemini_response) > 0:
            for item in gemini_response:
                section_title = item.get("section_title", "")
                page_number = item.get("page_number", -1)
                summary = item.get("summary", "")
                all_sections.append({
                    "document": filename,
                    "section_title": section_title,
                    "page_number": page_number,
                    "summary": summary
                })
        else:
            print(f"No relevant sections found for {filename}, skipping in output.")

    # Select the top N unique sections across all PDFs (no duplicate section_title+document+page_number)
    unique_keys = set()
    # 1. Select the most relevant section from each PDF (first occurrence per document)
    doc_first_section = {}
    for section in all_sections:
        doc = section["document"]
        if doc not in doc_first_section:
            doc_first_section[doc] = section

    # 2. Start with these, in the order of input_documents
    extracted_sections = []
    subsection_analysis = []
    used_keys = set()
    for doc in [doc["filename"] for doc in documents_meta]:
        if doc in doc_first_section:
            section = doc_first_section[doc]
            key = (section["document"], section["section_title"], section["page_number"])
            if key not in used_keys:
                used_keys.add(key)
                extracted_sections.append(section)
    # 3. If less than TOP_N_RESULTS, fill with next most relevant unique sections
    for section in all_sections:
        key = (section["document"], section["section_title"], section["page_number"])
        if key not in used_keys and len(extracted_sections) < TOP_N_RESULTS:
            used_keys.add(key)
            extracted_sections.append(section)
    # 4. Assign importance_rank and build subsection_analysis
    final_extracted = []
    final_subsection = []
    for idx, section in enumerate(extracted_sections[:TOP_N_RESULTS], start=1):
        final_extracted.append({
            "document": section["document"],
            "section_title": section["section_title"],
            "importance_rank": idx,
            "page_number": section["page_number"]
        })
        final_subsection.append({
            "document": section["document"],
            "refined_text": section["summary"],
            "page_number": section["page_number"]
        })

    metadata = {
        "input_documents": [doc["filename"] for doc in documents_meta],
        "persona": persona,
        "job_to_be_done": jtbd,
        "processing_timestamp": datetime.now().isoformat()
    }

    output_json = {
        "metadata": metadata,
        "extracted_sections": final_extracted,
        "subsection_analysis": final_subsection,
    }

    print("Writing the following output to file:")
    print(json.dumps(output_json, indent=2))
    with open(output_path, "w", encoding="utf-8") as fout:
        json.dump(output_json, fout, indent=4)

    print(f"Output saved to {output_path}")

# ---------------- ENTRY POINT ----------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gemini-based Document Intelligence Challenge")
    parser.add_argument("--input_folder", type=str, required=True,
                        help="Folder containing inputs.json and PDFs/")
    parser.add_argument("--output_file", type=str, default="output.json",
                        help="Path to save final output JSON")
    args = parser.parse_args()

    main(args.input_folder, args.output_file)
