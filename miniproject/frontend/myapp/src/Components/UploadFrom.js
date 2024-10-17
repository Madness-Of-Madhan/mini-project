// src/components/UploadForm.js
import React, { useState } from 'react';
import axios from 'axios';
import styled from 'styled-components';

const FormContainer = styled.div`
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    max-width: 600px;
    margin: 20px auto;
    border: 2px solid #ccc;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
`;

const InputField = styled.input`
    width: 100%;
    padding: 10px;
    margin: 10px 0;
    border: 1px solid #ccc;
    border-radius: 5px;
    font-size: 16px;
`;

const Button = styled.button`
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    background-color: #28a745;
    color: white;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.3s;

    &:hover {
        background-color: #218838;
    }
`;

const ResultContainer = styled.div`
    margin-top: 20px;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 10px;
    background-color: #f9f9f9;
`;

const ErrorContainer = styled.div`
    margin-top: 10px;
    color: red;
`;

const UploadForm = () => {
    const [pdfFile, setPdfFile] = useState(null);
    const [promptText, setPromptText] = useState('');
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleFileChange = (event) => {
        setPdfFile(event.target.files[0]);
    };

    const handlePromptChange = (event) => {
        setPromptText(event.target.value);
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError(null); // Clear previous errors
        const formData = new FormData();
        
        // Check if both inputs are empty
        if (!pdfFile && !promptText) {
            setError('Please upload a PDF or enter a prompt text.');
            return;
        }

        if (pdfFile) {
            formData.append('pdf_file', pdfFile);
        }
        if (promptText) {
            formData.append('prompt_text', promptText);
        }

        try {
            const response = await axios.post('http://127.0.0.1:5000/process', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setResult(response.data);
        } catch (error) {
            console.error('Error processing input:', error);
            setError('Failed to process the input. Please try again.');
        }
    };

    return (
        <FormContainer>
            <h2>Upload PDF or Enter Prompt</h2>
            <form onSubmit={handleSubmit}>
                <InputField 
                    type="file" 
                    accept="application/pdf" 
                    onChange={handleFileChange} 
                />
                <InputField
                    type="text"
                    placeholder="Enter prompt text"
                    value={promptText}
                    onChange={handlePromptChange}
                />
                <Button type="submit">Process</Button>
            </form>

            {error && <ErrorContainer>{error}</ErrorContainer>}

            {result && (
                <ResultContainer>
                    <h3>Summary</h3>
                    <p>{result.summary}</p>
                    <h3>Questions and Answers:</h3>
                    {result.questions_answers && result.questions_answers.length > 0 ? (
                        result.questions_answers.map((qa, index) => (
                            <div key={index}>
                                <strong>Q: {qa.question}</strong>
                                <ul>
                                    {qa.options.map((option, i) => (
                                        <li key={i}>{option}</li>
                                    ))}
                                </ul>
                            </div>
                        ))
                    ) : (
                        <p>No questions generated.</p>
                    )}
                </ResultContainer>
            )}
        </FormContainer>
    );
};

export default UploadForm;
