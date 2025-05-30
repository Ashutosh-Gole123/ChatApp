import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { BrowserRouter as Router} from 'react-router-dom';
import { AuthProvider } from './component/context/AuthContext'; 
import { ChatContextProvider } from './component/context/ChatContext.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ChatContextProvider>
    <AuthProvider>
    <Router>
    <App />
    </Router>
  </AuthProvider>
  </ChatContextProvider>
  </React.StrictMode>,



)
