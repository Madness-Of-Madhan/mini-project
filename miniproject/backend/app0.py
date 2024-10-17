from flask import Flask, request, jsonify
import pdfplumber
from transformers import pipeline
import random
import tempfile
import os
import logging
from flask_cors import CORS

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize the Flask app
app = Flask(__name__)
CORS(app)
# app = Flask(__name__)

# Summarization, question generation, and answer pipelines
logging.info("Loading summarization model...")
summarizer = pipeline("summarization", model="t5-base")
logging.info("Summarization model loaded.")

logging.info("Loading question generation model...")
qg_pipeline = pipeline("text2text-generation", model="t5-small")
logging.info("Question generation model loaded.")

logging.info("Loading question answering model...")
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")
logging.info("Question answering model loaded.")

logging.info("Loading fake answer generation model...")
fake_answer_pipeline = pipeline("text-generation", model="gpt2")
logging.info("Fake answer generation model loaded.")

# Function to extract text from PDF using pdfplumber
def extract_text_from_pdf_with_plumber(pdf_file):
    text = ''
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:  # Only append non-empty text
                text += page_text
    return text

# Function to summarize text
def summarize_text(text):
    max_chunk_size = 1024  # Max token length for the model
    text_chunks = [text[i:i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    summary = ''
    for chunk in text_chunks:
        summarized_chunk = summarizer(chunk, max_length=150, min_length=30, do_sample=False)
        summary += summarized_chunk[0]['summary_text'] + " "
    return summary.strip()

# Function to generate unique questions and their answers
def generate_questions_and_answers(text, num_questions=5):
    max_length = 512  # Define the maximum length for your input text
    truncated_text = text[:max_length]  # Truncate to the maximum length

    questions = qg_pipeline(truncated_text)
    previous_questions = set()  # To ensure unique questions

    qa_results = []
    for question in questions:
        q_text = question['generated_text']
        if q_text not in previous_questions:
            previous_questions.add(q_text)
            answer = qa_pipeline({'question': q_text, 'context': truncated_text})['answer']
            fake_answers = generate_fake_answers(q_text, answer)
            qa_results.append({
                'question': q_text,
                'options': fake_answers,
                'correct_answer': answer
            })

            if len(qa_results) >= num_questions:
                break

    return qa_results

# Function to generate fake answers for the questions
def generate_fake_answers(question, correct_answer):
    fake_answers = set()
    while len(fake_answers) < 3:
        fake_answer = fake_answer_pipeline(f"{question}?", max_length=20, num_return_sequences=1)[0]['generated_text']
        fake_answer = fake_answer.replace(question, '').strip()
        if fake_answer != correct_answer and fake_answer:  # Ensure uniqueness and non-empty
            fake_answers.add(fake_answer)
    all_answers = [correct_answer] + list(fake_answers)
    random.shuffle(all_answers)
    return all_answers

# Route for processing PDF or text prompt
@app.route('/process', methods=['POST'])
def process_input():
    pdf_file = request.files.get('pdf_file')
    prompt_text = request.form.get('prompt_text')

    if pdf_file:
        # Save the PDF temporarily and extract text
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            pdf_file.save(temp_file.name)
            pdf_path = temp_file.name

        try:
            pdf_text = extract_text_from_pdf_with_plumber(pdf_path)
        finally:
            os.remove(pdf_path)  # Clean up after processing

        if not pdf_text:
            return jsonify({'error': 'No text found in the PDF.'}), 400

        # Summarize and generate questions from the PDF
        pdf_summary = summarize_text(pdf_text)
        if not pdf_summary:
            return jsonify({'error': 'No summary could be generated.'}), 400
        
        questions_answers = generate_questions_and_answers(pdf_summary)
        return jsonify({
            'summary': pdf_summary,
            'questions_answers': questions_answers
        })

    elif prompt_text:
        # Summarize and generate questions from the prompt text
        prompt_summary = summarize_text(prompt_text)
        if not prompt_summary:
            return jsonify({'error': 'No summary could be generated from the prompt.'}), 400
        
        questions_answers = generate_questions_and_answers(prompt_summary)
        return jsonify({
            'summary': prompt_summary,
            'questions_answers': questions_answers
        })

    else:
        return jsonify({'error': 'No valid input provided (PDF or prompt text).'}), 400

if __name__ == '__main__':
    app.run(debug=True)