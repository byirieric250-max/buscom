import { StrictMode } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import Marketplace from './Marketplace';
import './style.css';
ReactDOM.createRoot(document.getElementById('root')!).render(<StrictMode><BrowserRouter><Marketplace /></BrowserRouter></StrictMode>);
