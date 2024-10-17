from flask import Flask, request, jsonify
import pdfplumber
from transformers import pipeline
import pandas as pd
import neattext.functions as nxt
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize summarization pipeline
summarization_pipeline = pipeline("summarization", model="t5-base")

# Load ML models using joblib
model1 = joblib.load('./app0.pkl')  # Update with actual model path
model2 = joblib.load('./app1.pkl')  # Update with actual model path

# PDF summarization function
def extract_text_from_pdf(pdf_file):
    text = ''
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def summarize_text(text):
    max_length = summarization_pipeline.model.config.max_position_embeddings
    prompt = text[:max_length]  # Truncate if needed
    summary = summarization_pipeline(prompt, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
    return summary

# Preprocess Udemy dataset (course dataset)
def preprocess_udemy_dataset(file_path):
    df = pd.read_csv(file_path)
    df['clean_course_title'] = df['course_title'].apply(nxt.remove_stopwords).apply(nxt.remove_special_characters)
    return df

# Preprocess research articles dataset
def preprocess_article_dataset(file_path):
    dataset = pd.read_csv(file_path)
    columns_to_drop = ['Unnamed: 0', 'Id', 'citations']
    dataset.drop(columns=columns_to_drop, inplace=True)
    dataset['authors'] = dataset['authors'].apply(lambda x: re.sub(r"[\[\]\(\)]", "", x))
    dataset['title'] = dataset['title'].apply(nxt.remove_stopwords)
    return dataset

# Calculate cosine similarity for a given dataset
def calculate_cosine_similarity(dataset, summary):
    vectorizer = CountVectorizer().fit_transform(dataset['title'].tolist() + [summary])
    vectors = vectorizer.toarray()
    cosine_sim = cosine_similarity(vectors)
    similarities = cosine_sim[-1][:-1]  # Exclude summary itself
    return similarities

# Display recommendations
def display_recommendations(dataset, similarities, title_column):
    similar_items = dataset[similarities > 0]
    return similar_items[title_column].tolist()

# API endpoint to accept PDF or text prompt input
@app.route('/summarize', methods=['POST'])
def summarize_and_recommend():
    # File paths to datasets
    udemy_file = './uploads/udemy_courses.csv'  # Update this path
    article_file = './uploads/dataset.csv'      # Update this path
    
    # Check if a file or text prompt is submitted
    if 'file' in request.files:
        # If a file is provided, process as PDF
        pdf_file = request.files['file']
        text = extract_text_from_pdf(pdf_file)
        summary = summarize_text(text)
    elif 'prompt' in request.form:
        # If a text prompt is provided, process as text
        text_prompt = request.form['prompt']
        summary = summarize_text(text_prompt)
    else:
        return jsonify({'error': 'No valid input provided, please submit a PDF or a text prompt.'}), 400

    # Preprocess Udemy and Articles datasets
    udemy_df = preprocess_udemy_dataset(udemy_file)
    article_df = preprocess_article_dataset(article_file)

    # Calculate cosine similarities and get recommendations
    udemy_similarities = calculate_cosine_similarity(udemy_df, summary)
    related_courses = display_recommendations(udemy_df, udemy_similarities, 'course_title')

    article_similarities = calculate_cosine_similarity(article_df, summary)
    similar_articles = display_recommendations(article_df, article_similarities, 'title')

    # Return the summary and recommendations
    response = {
        'summary': summary,
        'related_courses': related_courses,
        'similar_articles': similar_articles
    }

    return jsonify(response)

# Prediction routes using loaded models
@app.route('/predict_model1', methods=['POST'])
def predict_model1():
    data = request.get_json()
    prediction = model1.predict([data['input']])
    return jsonify({'prediction': prediction.tolist()})

@app.route('/predict_model2', methods=['POST'])
def predict_model2():
    data = request.get_json()
    prediction = model2.predict([data['input']])
    return jsonify({'prediction': prediction.tolist()})

if __name__ == '__main__':
    app.run(debug=True)
