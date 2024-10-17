// src/App.js
import React from 'react';
import UploadForm from './Components/UploadFrom';
import GlobalStyles from './GlobalStyle';

const App = () => {
    return (
        <>
            <GlobalStyles />
            <div className="app-container">
                <h1>PDF Text Processor</h1>
                <UploadForm />
            </div>
        </>
    );
};

export default App;
