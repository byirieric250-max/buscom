'use client';
import { FormEvent, useState } from 'react';
import { Bot, Send, X } from 'lucide-react';
import './GuidanceBot.css';

const API_BASE=(process.env.NEXT_PUBLIC_API_BASE_URL||(process.env.NODE_ENV==='production'?'https://buscom-backend.onrender.com':'')).replace(/\/$/,'');
type Message={role:'bot'|'user';text:string};

export default function GuidanceBot(){
 const [open,setOpen]=useState(false);
 const [language,setLanguage]=useState('en');
 const [question,setQuestion]=useState('');
 const [busy,setBusy]=useState(false);
 const [messages,setMessages]=useState<Message[]>([{role:'bot',text:'How can I help you with business registration, VAT, payments, orders, or bookings?'}]);
 const ask=async(e:FormEvent)=>{e.preventDefault();const text=question.trim();if(text.length<3||busy)return;setMessages(m=>[...m,{role:'user',text}]);setQuestion('');setBusy(true);try{const response=await fetch(`${API_BASE}/api/ai-guidance/`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:text,language,context:'general'})});const data=await response.json();if(!response.ok)throw new Error(data.detail||'The guidance service is unavailable.');setMessages(m=>[...m,{role:'bot',text:data.answer}])}catch(error){setMessages(m=>[...m,{role:'bot',text:(error as Error).message}])}finally{setBusy(false)}};
 return <>
  {open&&<section className="guidance-panel" aria-label="Business guidance assistant"><header><div><Bot size={18}/><span><b>Regulation Guide</b><small>Simple business guidance</small></span></div><button onClick={()=>setOpen(false)} aria-label="Close guidance"><X size={17}/></button></header><label className="guidance-language">Language<select value={language} onChange={e=>setLanguage(e.target.value)}><option value="en">English</option><option value="rw">Kinyarwanda</option><option value="sw">Kiswahili</option><option value="fr">Français</option></select></label><div className="guidance-messages">{messages.map((message,index)=><p key={index} className={`guidance-message ${message.role}`}>{message.text}</p>)}</div><form onSubmit={ask}><input value={question} onChange={e=>setQuestion(e.target.value)} maxLength={500} placeholder="Ask about registration or VAT…" aria-label="Your guidance question"/><button disabled={busy||question.trim().length<3} aria-label="Send"><Send size={16}/></button></form><small className="guidance-disclaimer">Informational only; confirm legal decisions with the relevant authority.</small></section>}
  <button className="guidance-launcher" onClick={()=>setOpen(value=>!value)} aria-label="Open business guidance assistant"><Bot size={21}/><span>Ask guide</span></button>
 </>;
}
