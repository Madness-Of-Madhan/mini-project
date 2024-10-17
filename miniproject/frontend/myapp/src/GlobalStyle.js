// src/GlobalStyles.js
import { createGlobalStyle } from 'styled-components';

const GlobalStyles = createGlobalStyle`
    body {
        font-family: 'Arial', sans-serif;
        margin: 0;
        padding: 0;
        background-color: #f4f4f4;
        color: #333;
    }

    .app-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px;
    }
`;

export default GlobalStyles;
