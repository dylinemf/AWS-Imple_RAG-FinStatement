import React, { useRef, useState } from 'react';
import styles from '../styles/ChatInterface.module.css';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { API_BASE_URL } from '../config';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  sources?: any[];
}

interface ChatInterfaceProps {
  disabled?: boolean;
}

export default function ChatInterface({ disabled=false }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const [sourcesOpen, setSourcesOpen] = useState<{[k:string]:boolean}>({});

  const handleSendMessage = async () => {
    if (!input.trim()) return;
    if (disabled) return;
    const userMessage: Message = { id: Date.now() + '_u', type: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          question: input, 
          chat_history: messages.filter(m => m.type === 'user').map(m => ({ role: m.type, content: m.content}))
        })
      });
      const data = await res.json();
      if (res.ok) {
        const msgId = Date.now() + '_a';
        const assistantMsg: Message = {
          id: msgId,
          type: 'assistant',
          content: data.answer || (data.detail ?? 'No answer returned.'),
          sources: data.sources || [],
        };
        setMessages(prev => [...prev, assistantMsg]);
        setSourcesOpen((s) => ({ ...s, [msgId]: false}));
      } else {
        setMessages(prev => [...prev, {
          id: Date.now()+'_e', type: 'assistant', content: data.detail || 'Chat error!', sources:[]
        }]);
      }
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now()+'_ex', type: 'assistant', content: 'Server error!', sources:[]
      }]);
    }
    setInput('');
    setIsLoading(false);
    inputRef.current?.focus();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading && !disabled) handleSendMessage();
  };

  return (
    <div className={styles.chatWrapper}>
      <div
        className={`${styles.chatBox} ${!disabled ? styles.chatBoxEnabled : ''}`}
      >
        {messages.length === 0 && <div style={{color:'#aaa'}}>No messages yet. Start asking in the column below!</div>}
        {messages.map((msg) => (
          <div key={msg.id} className={`${styles.msgRow} ${msg.type === 'user' ? styles.msgRowUser : styles.msgRowAssistant}`}>
            <div className={msg.type === 'user' ? styles.msgBubbleUser : styles.msgBubbleAssistant}>
              {msg.type === "assistant" ? (
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                  components={{
                    a: ({node, ...props}) => 
                      <a {...props} target="_blank" rel="noopener noreferrer">{props.children}</a>,
                    pre: ({node, ...props}) => <pre className={styles.markdownCodeblock} {...props} />,
                    code: ({node, ...props}) => <code className={styles.markdownInlineCode} {...props} />,
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              ) : (
                <span>{msg.content}</span>
              )}
              {msg.type==='assistant' && msg.sources && msg.sources.length > 0 && (
                <div style={{ marginTop: 10 }}>
                  <button
                    onClick={() => setSourcesOpen(o => ({...o, [msg.id]: !o[msg.id]}))}
                    className={styles.sourcesBtn}
                    aria-expanded={!!sourcesOpen[msg.id]}
                    title="See sources"
                  >
                    <span className={styles.sourcesExpandedIcon}
                          style={{
                            transform: sourcesOpen[msg.id] ? 'rotate(90deg)' : 'rotate(0deg)'
                          }}
                    >▶</span>
                    <span>Sources</span>
                  </button>
                  {sourcesOpen[msg.id] && (
                    <div className={styles.sourcesList}>
                      <ul style={{margin:0,paddingLeft:22, listStyle:'decimal'}}>
                        {msg.sources.map((s,i) => (
                          <li key={i} className={styles.sourceLi}>
                            <span className={styles.sourcePage}>Page {s.page}</span>
                            <span className={styles.sourceContent} title={s.content}>
                              {(s.content || '').slice(0, 50)}{(s.content || '').length > 50 ? '...' : ''}
                            </span>
                            {' '}
                            <span className={styles.sourceScore}>
                              (score: {s.score})
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && <div className={styles.typing}>Assistant is typing...</div>}
      </div>

      {/* Input area */}
      <div className={`${styles.inputRow} ${disabled ? styles.inputDisabled : ''}`}>
        <input
          type="text"
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyPress}
          disabled={disabled || isLoading}
          ref={inputRef}
          className={`${styles.chatTextInput} ${(disabled || isLoading) ? styles.chatTextInputDisabled : ''}`}
          placeholder={disabled
            ? "Chat is disabled, upload PDF first!"
            : "Type your question and press Enter..."
          }
        />
        <button
          onClick={handleSendMessage}
          disabled={!input.trim() || isLoading || disabled}
          className={styles.sendBtn}
        >Send</button>
      </div>
      {disabled && (
        <div className={styles.disabledNote}>
          <span>Upload PDF first to start Q&A ⬆️</span>
        </div>
      )}
    </div>
  );
}