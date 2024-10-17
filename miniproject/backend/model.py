import PyPDF2
import pdfplumber
from transformers import pipeline
import random
import torch

# Function to extract text from PDF using PyPDF2
def extract_text_from_pdf(pdf_file):
    with open(pdf_file, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

# Function to extract text from PDF using pdfplumber
def extract_text_from_pdf_with_plumber(pdf_file):
    text = ''
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Summarization pipeline
summarizer = pipeline('summarization', model="facebook/bart-large-cnn")

# Function to summarize text
def summarize_text(text):
    max_chunk_size = 1024  # Max token length for the model
    text_chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]

    summary = ''
    for chunk in text_chunks:
        summarized_chunk = summarizer(chunk, max_length=150, min_length=30, do_sample=False)
        summary += summarized_chunk[0]['summary_text'] + " "
    return summary

# Question generation and answer pipeline setup
qg_pipeline = pipeline("text2text-generation", model="valhalla/t5-small-qg-hl")
qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")
fake_answer_pipeline = pipeline("text-generation", model="gpt2")

# Function to generate questions and answers
def generate_questions_and_answers(text, num_questions=10):
    max_length = 512  # Define the maximum length for your input text
    truncated_text = text[:max_length]  # Truncate to the maximum length

    questions = qg_pipeline(truncated_text)
    previous_questions = set()  # To ensure unique questions
    question_texts = [q['generated_text'] for q in questions]

    num_questions_to_print = min(num_questions, len(question_texts))
    print("Generated Questions with Answers and Options:")

    score = 0  # Initialize score

    for _ in range(num_questions_to_print):
        unique_question_found = False
        while not unique_question_found:
            question = random.choice(question_texts)

            if question not in previous_questions:
                previous_questions.add(question)
                print(f"\nQuestion: {question}")

                # Generate the correct answer
                answer = qa_pipeline({
                    'question': question,
                    'context': truncated_text
                })['answer']
                
                # Generate 3 fake answers
                fake_answers = set()
                while len(fake_answers) < 3:
                    fake_answer = fake_answer_pipeline(f"{question}?", max_length=20, num_return_sequences=1)[0]['generated_text']
                    fake_answer = fake_answer.replace(question, '').strip()
                    if fake_answer != answer:
                        fake_answers.add(fake_answer)

                # Print all answer options (1 correct and 3 fake)
                all_answers = [answer] + list(fake_answers)
                random.shuffle(all_answers)
                for i, option in enumerate(all_answers, 1):
                    print(f"Option {i}: {option}")

                # Ask user for their answer
                user_answer = input("Select the correct option number (1-4): ")
                
                # Check if the user's answer is correct
                if all_answers[int(user_answer) - 1] == answer:
                    print("Correct!")
                    score += 1
                else:
                    print(f"Incorrect. The correct answer is: {answer}")
                unique_question_found = True

    print(f"\nYour total score: {score}/{num_questions_to_print}")

# Main function to handle both PDF and prompt input
def process_input(pdf_file=None, prompt_text=None):
    if pdf_file:
        # Extract and summarize text from PDF
        pdf_text = extract_text_from_pdf_with_plumber(pdf_file)
        pdf_summary = summarize_text(pdf_text)
        print(f"Summary of PDF:\n{pdf_summary[:1000]}")
        generate_questions_and_answers(pdf_summary)
    
    if prompt_text:
        # Summarize and process the prompt directly
        prompt_summary = summarize_text(prompt_text)
        print(f"Summary of Prompt:\n{prompt_summary}")
        generate_questions_and_answers(prompt_summary)

# Example usage:
pdf_file = "/content/MachineTranslationwithAttention.pdf"
prompt_text = "Explain the importance of machine translation in language processing."

# Process both PDF and prompt
process_input(pdf_file=pdf_file, prompt_text=prompt_text)
