# Persona-Driven Document Intelligence Challenge

This project implements an intelligent document analysis system that processes a collection of PDF documents and extracts the most relevant sections tailored to a specific persona and their job-to-be-done (JTBD). The solution combines advanced PDF text extraction with state-of-the-art large language models—specifically Google’s Gemini AI—to semantically understand and rank document content according to user intent.

## Project Overview

- **PDF Section Extraction:** Using PyMuPDF, the system extracts logical sections from each PDF by detecting top-level headings (h1) based on font size. These sections preserve page information and content structure for focused analysis.

- **Persona and JTBD Integration:** The persona definition and the JTBD are combined into a semantic query context that guides the relevance scoring and summarization.

- **Gemini AI for Semantic Analysis:** Leveraging Google’s Gemini AI via the official Generative Language SDK, the system prompts the model with extracted sections and persona+JTBD context to perform relevance ranking, generate refined summaries, and output structured JSON tailored to the use case.

- **Efficient, Scalable, and Portable:** The entire solution is packaged to run efficiently with minimal dependencies, supports CPU-only processing for extraction, and utilizes cloud-based Gemini API for intelligent document understanding.

This approach enables customized, persona-driven insights across diverse document collections and domains, demonstrating a practical application of cutting-edge AI for enhanced document intelligence and automation.

