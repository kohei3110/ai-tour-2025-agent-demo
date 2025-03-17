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

  // 補助金情報のリストをテーブル形式に変換する関数
  const formatSubsidyInfoToTable = (content) => {
    if (!content) return '';

    // 数値＋ドット＋スペースのパターンとタイトルを含む行を検出する正規表現
    const numberListPattern = /(\d+)\.\s+\*\*([^*]+)\*\*/g;
    
    if (content.match(numberListPattern)) {
      // 補助金の情報が含まれているかを確認するキーワード
      const subsidyKeywords = ['補助金', '奨励金', '助成金', '支援金', '支援事業'];
      const periodKeywords = ['募集期間', '応募期間']; 
      let hasSubsidyInfo = subsidyKeywords.some(keyword => content.includes(keyword));
      let hasPeriodInfo = periodKeywords.some(keyword => content.includes(keyword));
      
      if (hasSubsidyInfo && hasPeriodInfo) {
        // 表のヘッダー部分を作成
        let tableHtml = `
          <div class="subsidy-table-container">
            <table class="subsidy-table">
              <thead>
                <tr>
                  <th>補助金名</th>
                  <th>応募期間</th>
                  <th>上限額</th>
                  <th>対象者/人数</th>
                </tr>
              </thead>
              <tbody>
        `;
        
        // 改良された補助金情報を抽出するパターン
        const subsidyBlocks = content.split(/(?=\d+\.\s+\*\*)/);
        let hasMatches = false;
        
        for (const block of subsidyBlocks) {
          if (!block.trim()) continue;
          
          // 補助金名を抽出
          const titleMatch = block.match(/\d+\.\s+\*\*([^*]+)\*\*/);
          if (!titleMatch) continue;
          
          const title = titleMatch[1].trim();
          
          // 募集期間を抽出
          const periodMatch = block.match(/(?:募集期間|応募期間)[:：]\s*([^(\n]+)/);
          const period = periodMatch ? periodMatch[1].trim() : "";
          
          // 最大補助金額を抽出
          const amountMatch = block.match(/(?:最大補助金額|上限額|補助金最大額)[:：]\s*([^(\n]+)/);
          const amount = amountMatch ? amountMatch[1].trim() : "";
          
          // 対象人数/従業員制約を抽出
          const empMatch = block.match(/(?:対象人数|従業員の制約|従業員制約)[:：]\s*([^(\n]+)/);
          const employeeLimit = empMatch ? empMatch[1].trim() : "";
          
          if (title) {
            hasMatches = true;
            tableHtml += `
              <tr>
                <td>${title}</td>
                <td>${period}</td>
                <td>${amount}</td>
                <td>${employeeLimit}</td>
              </tr>
            `;
          }
        }
        
        tableHtml += `
              </tbody>
            </table>
          </div>
        `;
        
        // 抽出した表形式のHTML部分がある場合のみ置き換える
        if (hasMatches) {
          // 元の補助金リストを見つけて置き換える正規表現パターン
          const listPattern = /(\d+\.\s+\*\*[^*]+\*\*[\s\S]*?)(?=(\d+\.\s+\*\*)|$)/g;
          const listStart = content.search(listPattern);
          const listEnd = content.lastIndexOf("これらの補助金は");
          
          if (listStart >= 0) {
            // 補助金リストの部分をテーブルに置換
            const beforeList = content.substring(0, listStart);
            const afterList = listEnd >= 0 ? content.substring(listEnd) : "";
            
            return beforeList + tableHtml + "\n\n" + afterList;
          }
        }
      }
    }
    
    return content;
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
                    __html: sanitizeHtml(formatSubsidyInfoToTable(message.content)) 
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
