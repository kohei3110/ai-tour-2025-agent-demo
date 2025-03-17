import { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from './services/api';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messageEndRef = useRef(null);

  // 自動スクロール機能
  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // メッセージ送信処理
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (input.trim() === '') return;
    
    // ユーザーのメッセージをチャットに追加
    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      // APIサービスを使用してメッセージを送信
      const data = await sendChatMessage(input);
      
      // アシスタントの返信をチャットに追加（引用ソースとクエリも含める）
      const assistantMessage = { 
        role: 'assistant', 
        content: data.response,
        sources: data.sources, // 引用ソース
        query: data.query // 検索クエリ
      };
      setMessages(prevMessages => [...prevMessages, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      // エラーメッセージをチャットに表示
      const errorMessage = { 
        role: 'system', 
        content: 'エラーが発生しました。しばらく経ってからもう一度お試しください。' 
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // HTMLからスクリプトタグを除去するための関数
  const sanitizeHtml = (html) => {
    // 簡易的なサニタイズ（本番環境では専用ライブラリの使用を推奨）
    return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  };

  return (
    <div className="App">
      <div className="chat-container">
        <h1>AIエージェントアシスタント</h1>
        
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <p>こんにちは！どのようなご質問がありますか？</p>
            </div>
          )}
          {messages.map((message, index) => (
            <div 
              key={index} 
              className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
            >
              {message.role === 'user' ? (
                <div className="message-content">{message.content}</div>
              ) : (
                <div 
                  className="message-content"
                  dangerouslySetInnerHTML={{ 
                    __html: sanitizeHtml(message.content) 
                  }}
                />
              )}
              
              <div className="message-references">
                {/* 引用ソースがある場合に表示 */}
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <p className="sources-title">引用ソース:</p>
                    <ul className="sources-list">
                      {message.sources.map((source, sourceIndex) => (
                        <li key={sourceIndex}>
                          <a href={source} target="_blank" rel="noopener noreferrer">
                            {source}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* 検索クエリがある場合に表示 */}
                {message.query && (
                  <div className="search-query">
                    <a 
                      href={`https://www.bing.com/search?q=${encodeURIComponent(message.query)}`}
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="bing-search-link"
                    >
                      Bingで「{message.query}」を検索
                    </a>
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message assistant-message">
              <div className="message-content loading">
                <span>思考中</span>
                <span className="dot">.</span>
                <span className="dot">.</span>
                <span className="dot">.</span>
              </div>
            </div>
          )}
          <div ref={messageEndRef} />
        </div>
        
        <form className="message-form" onSubmit={handleSendMessage}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="メッセージを入力してください..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || input.trim() === ''}>
            送信
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
