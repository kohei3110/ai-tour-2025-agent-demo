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

    // 補助金情報を含むか確認するキーワード
    const subsidyKeywords = ['補助金', '奨励金', '助成金', '支援金', '支援事業'];
    const periodKeywords = ['採択期間', '募集期間', '応募期間', '開始', '終了', '締切']; 
    let hasSubsidyInfo = subsidyKeywords.some(keyword => content.includes(keyword));
    let hasPeriodInfo = periodKeywords.some(keyword => content.includes(keyword));
    
    if (hasSubsidyInfo && hasPeriodInfo) {
      // 1. 数値+ドット+スペース+タイトル のパターン
      const numberListPattern = /(\d+)\.\s+\*\*([^*]+)\*\*/g;
      
      // 2. - **タイトル** のパターン
      const bulletPointPattern = /-\s+\*\*([^*]+)\*\*/g;
      
      // 3. **タイトル** のパターン
      const boldTitlePattern = /\*\*([^*:]+)\*\*/g;

      // パターンのいずれかにマッチするか確認
      let hasListFormat = content.match(numberListPattern) || 
                         content.match(bulletPointPattern) ||
                         content.match(boldTitlePattern);

      // 追加: タイトル行のみで格納されている場合にも対応
      const singleTitlePattern = /^\s*\*\*([^*]+)\*\*/;
      if (!hasListFormat && singleTitlePattern.test(content)) {
        hasListFormat = true;
      }
                         
      if (hasListFormat) {
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
        
        // 補助金情報を抽出するためのブロック分割パターン
        let blocks = [];
        
        // パターン1: 番号リスト (1. **タイトル**)
        if (content.match(numberListPattern)) {
          blocks = content.split(/(?=\d+\.\s+\*\*)/);
        } 
        // パターン2: 箇条書きリスト (- **タイトル**)
        else if (content.match(bulletPointPattern)) {
          blocks = content.split(/(?=-\s+\*\*)/);
        }
        // パターン3: 最初の補助金情報が番号なしのタイトルだけの場合
        else if (content.match(/^\s*\*\*([^*]+)\*\*/)) {
          // 先頭の補助金情報とそれ以降の複数補助金情報を分離
          const mainBlock = content.match(/^\s*\*\*([^*]+)\*\*.*?(?=\d+\.\s+\*\*|$)/s);
          if (mainBlock) {
            // 最初の補助金情報をブロックに追加
            blocks.push(mainBlock[0]);
            
            // 残りの補助金情報を番号付きリストとして処理
            const remainingContent = content.substring(mainBlock[0].length);
            if (remainingContent.trim()) {
              const remainingBlocks = remainingContent.split(/(?=\d+\.\s+\*\*)/);
              blocks = [...blocks, ...remainingBlocks];
            }
          } else {
            blocks = [content]; // 単一ブロックとして処理
          }
        }
        // パターン4: タイトルリスト (**タイトル**:) または単一の補助金情報
        else {
          blocks = [content]; // 単一ブロックとして処理
        }
        
        let hasMatches = false;
        
        for (let block of blocks) {
          if (!block.trim()) continue;
          
          // タイトル抽出 - 複数のパターンに対応
          let titleMatch = block.match(/\d+\.\s+\*\*([^*:]+)\*\*/) || // 番号リスト
                          block.match(/-\s+\*\*([^*:]+)\*\*/) ||     // 箇条書きリスト
                          block.match(/\*\*([^*:]+)\*\*/);           // 一般的な太字タイトル
          
          // タイトル行がない場合はスキップ
          if (!titleMatch) continue;
          
          const title = titleMatch[1].trim();
          
          // 期間情報を抽出 - 様々なパターンに対応
          const periodPatterns = [
            /(?:採択期間|募集期間|応募期間|申請期間)[:：]?\s*([^(\r\n]+)/,
            /-\s+\*\*(?:採択期間|募集期間|応募期間|申請期間)\*\*[:：]?\s*([^(\r\n]+)/,
            /-\s+(?:募集開始日|応募期間|開始日)[:：]?\s*([^(\r\n]+)/,
            /開始日[:：]?\s*([^(\r\n]+)/,
            /開始[:：]?\s*([^(\r\n]+)/
          ];
          
          let period = "";
          for (const pattern of periodPatterns) {
            const match = block.match(pattern);
            if (match) {
              period = match[1].trim();
              break;
            }
          }
          
          // 終了日が別に記載されている場合は追加
          const endDatePatterns = [
            /(?:募集締切日|終了日)[:：]?\s*([^(\r\n]+)/,
            /-\s+(?:募集締切日|終了日)[:：]?\s*([^(\r\n]+)/,
            /終了[:：]?\s*([^(\r\n]+)/
          ];
          
          let endDate = "";
          for (const pattern of endDatePatterns) {
            const match = block.match(pattern);
            if (match) {
              endDate = match[1].trim();
              break;
            }
          }
          
          if (endDate && period) {
            period += " 〜 " + endDate;
          } else if (endDate && !period) {
            period = endDate;
          }
          
          // 補助金額を抽出 - パターンを拡張
          const amountPatterns = [
            // 既存のパターン
            /(?:最大補助金額|上限額|補助金額|補助金の上限|補助金上限|補助金最大額)[:：]?\s*([^(\r\n]+)/,
            /-\s+\*\*(?:最大補助金額|上限額|補助金額|補助金の上限)\*\*[:：]?\s*([^(\r\n]+)/,
            /-\s+(?:最大補助金額|上限額|補助金額|補助金の上限|補助金上限)[:：]?\s*([^(\r\n]+)/,
            
            // 追加パターン：さまざまな表現に対応
            /(?:補助上限|上限金額|補助限度額|限度額|助成金額|支援金額|助成上限|支給上限|給付額)[:：]?\s*([^(\r\n]+)/,
            /-\s+\*\*(?:補助上限|上限金額|補助限度額|限度額|助成金額|支援金額|助成上限|支給上限|給付額)\*\*[:：]?\s*([^(\r\n]+)/,
            /-\s+(?:補助上限|上限金額|補助限度額|限度額|助成金額|支援金額|助成上限|支給上限|給付額)[:：]?\s*([^(\r\n]+)/,
            
            // 金額だけの表現に対応
            /最大(?:[\d,，.億万千百]+(?:円|万円|億円))/i,
            /上限(?:[\d,，.億万千百]+(?:円|万円|億円))/i,
            
            // コロンなしの場合にも対応
            /(?:補助金額|上限額|補助上限|最大金額)は?[\s　]*([^(\r\n]+)/,
            /(?:補助金|助成金|支援金|給付金).{1,10}上限[\s　]*([^(\r\n]+)/,
            
            // **〜円** のようなパターン
            /\*\*([\d,，.億万千百]+(?:円|万円|億円))\*\*/
          ];
          
          // 対象者情報を抽出 - パターンを拡張
          const empPatterns = [
            /(?:対象者|対象業種|対象人数|従業員の制約|従業員制約|従業員数|従業員|対象地域|対象)[:：]?\s*([^(\r\n]+)/,
            /-\s+\*\*(?:対象者|対象業種|対象人数|従業員の制約|対象従業員数)\*\*[:：]?\s*([^(\r\n]+)/,
            /-\s+(?:対象者|対象業種|対象人数|従業員の制約|対象従業員数|対象地域)[:：]?\s*([^(\r\n]+)/
          ];
          
          let employeeLimit = "";
          for (const pattern of empPatterns) {
            const match = block.match(pattern);
            if (match) {
              employeeLimit = match[1].trim();
              break;
            }
          }
          
          // 補助金額を抽出
          let amount = "";
          for (const pattern of amountPatterns) {
            const match = block.match(pattern);
            if (match) {
              // 最大/上限 〜円のパターンの場合は少し処理が異なる
              if (pattern.toString().includes('最大(?:') || pattern.toString().includes('上限(?:')) {
                amount = match[0].trim();
              } else {
                amount = match[1].trim();
              }
              break;
            }
          }
          
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
          // 補助金情報を含む部分を特定
          const startPattern = content.match(/(?:\d+\.\s+\*\*|-\s+\*\*|\*\*)/);
          const listStart = startPattern ? startPattern.index : 0;
          
          // 補助金リスト終了位置を判定する表現を改良
          const listEndMatch = content.match(/(?:これらの補助金|以上の情報|以上が|これらの支援金|これらの事業|これらの回答)/i);
          const listEnd = listEndMatch ? listEndMatch.index : content.length;
          
          if (listStart >= 0) {
            // 補助金リストの部分をテーブルに置換
            const beforeList = content.substring(0, listStart).trim();
            const afterList = listEnd < content.length ? content.substring(listEnd).trim() : "";
            
            return [beforeList, tableHtml, afterList].filter(Boolean).join('\n');
          }
          
          // 全体がタイトルと説明のみの場合
          if (blocks.length === 1) {
            return [tableHtml, content.trim()].filter(Boolean).join('\n');
          }
          
          // それ以外の場合はテーブルだけを返す
          return tableHtml;
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
