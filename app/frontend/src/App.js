import { useState, useRef, useEffect } from 'react';
import { sendChatMessage, generateApplicationTemplate, generateMessage } from './services/api';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copySuccess, setCopySuccess] = useState('');
  const [showBusinessForm, setShowBusinessForm] = useState(false);
  const [businessDescription, setBusinessDescription] = useState('');
  const [currentSubsidyInfo, setCurrentSubsidyInfo] = useState(null);
  const [generatingTemplate, setGeneratingTemplate] = useState(false);
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
        query: data.query, // 検索クエリ
        applicationText: data.applicationText, // 申請書テキスト
        subsidyInfo: extractSubsidyInfo(data.response) // 補助金情報を抽出
      };

      setMessages(prevMessages => [...prevMessages, assistantMessage]);
      
      // 補助金情報が含まれている場合は保存
      if (assistantMessage.subsidyInfo) {
        setCurrentSubsidyInfo(assistantMessage.subsidyInfo);
      }
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

  // 補助金情報を応答から抽出する関数
  const extractSubsidyInfo = (content) => {
    if (!content) return null;
    
    // キーワードを拡張
    const subsidyKeywords = ['補助金', '奨励金', '助成金', '支援金', '支援事業', '給付金'];
    const periodKeywords = ['採択期間', '募集期間', '応募期間', '開始', '終了', '締切', '申請期限'];
    
    let hasSubsidyInfo = subsidyKeywords.some(keyword => content.includes(keyword));
    let hasPeriodInfo = periodKeywords.some(keyword => content.includes(keyword));
    
    if (hasSubsidyInfo) {  // 期間情報の有無に関わらず補助金情報を抽出
      // タイトル抽出を改善
      let titleMatch = content.match(/\*\*([^*:]+)\*\*/) || 
                      content.match(/「([^」]+)」/) ||
                      content.match(/『([^』]+)』/) ||
                      content.match(/(\d+\.\s*[^\n]+)/) ||
                      content.match(/(-\s*[^\n]+)/);
      
      const title = titleMatch ? titleMatch[1].trim() : "補助金情報";
      
      // 期間情報の抽出を改善
      const periodPattern = /(?:採択期間|募集期間|応募期間|申請期間|申請期限)[:：]?\s*([^(\r\n]+)/;
      const periodMatch = content.match(periodPattern);
      
      // 補助金額を抽出（パターンを追加）
      const amountPattern = /(?:最大補助金額|上限額|補助金額|補助金の上限|補助金上限|上限金額|給付額|支給額)[:：]?\s*([^(\r\n]+)/;
      const amountMatch = content.match(amountPattern) || 
                         content.match(/(?:最大|上限)(?:[\d,，.億万千百]+(?:円|万円|億円))/);
      
      // 対象者情報を抽出（パターンを追加）
      const empPattern = /(?:対象者|対象業種|対象企業|対象事業者|従業員の制約|従業員制約|従業員数|従業員|対象地域|対象)[:：]?\s*([^(\r\n]+)/;
      const empMatch = content.match(empPattern);
      
      // 開始日と終了日を抽出
      const startDatePattern = /(?:開始日|開始|募集開始)[:：]?\s*([^(\r\n]+)/;
      const startDateMatch = content.match(startDatePattern);
      
      const endDatePattern = /(?:終了日|締切日|締切|期限)[:：]?\s*([^(\r\n]+)/;
      const endDateMatch = content.match(endDatePattern);
      
      // 数値部分を抽出してsubsidy_max_limitを推定
      let subsidyMaxLimit = null;
      if (amountMatch) {
        const amountStr = amountMatch[1] || amountMatch[0];
        const numMatch = amountStr.match(/([\d,，]+)/);
        if (numMatch) {
          subsidyMaxLimit = parseInt(numMatch[1].replace(/[,，]/g, ''), 10);
          
          if (amountStr.includes('億円')) {
            subsidyMaxLimit *= 100000000;
          } else if (amountStr.includes('万円')) {
            subsidyMaxLimit *= 10000;
          }
        }
      }
      
      // より詳細な補助金情報オブジェクトを作成
      const subsidyInfo = {
        title: title,
        acceptance_start_datetime: startDateMatch ? startDateMatch[1] : null,
        acceptance_end_datetime: endDateMatch ? endDateMatch[1] : (periodMatch ? periodMatch[1] : null),
        target_area_search: empMatch ? empMatch[1] : "全国",
        subsidy_max_limit: subsidyMaxLimit,
        target_number_of_employees: empMatch ? empMatch[1] : null,
        summary: content.substring(0, 200),
        raw_content: content  // 生の応答内容も保存
      };
      
      return subsidyInfo;
    }
    
    return null;
  };

  // HTMLからスクリプトタグを除去するための関数
  const sanitizeHtml = (html) => {
    // 簡易的なサニタイズ（本番環境では専用ライブラリの使用を推奨）
    return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  };

  // クリップボードにコピーする関数
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        setCopySuccess('コピーしました！');
        setTimeout(() => setCopySuccess(''), 2000);
      })
      .catch(err => {
        console.error('コピーに失敗しました', err);
        setCopySuccess('コピーに失敗しました');
        setTimeout(() => setCopySuccess(''), 2000);
      });
  };

  // ビジネス説明フォームを表示
  const handleCreateApplication = () => {
    setShowBusinessForm(true);
  };

  // ビジネス説明フォームをキャンセル
  const handleCancelBusinessForm = () => {
    setShowBusinessForm(false);
    setBusinessDescription('');
  };

  // AI拡張テンプレートを生成
  const handleGenerateAITemplate = async () => {
    if (!currentSubsidyInfo) return;
    
    setGeneratingTemplate(true);
    
    try {
      // API呼び出し
      const result = await generateApplicationTemplate(
        currentSubsidyInfo, 
        businessDescription.trim() || null
      );
      
      // 結果をメッセージに追加
      const templateMessage = {
        role: 'assistant',
        content: '補助金申請書テンプレートを生成しました：',
        applicationText: result.template,
        aiEnhanced: result.aiEnhanced
      };
      
      setMessages([...messages, templateMessage]);
      
      // フォームをリセット
      setShowBusinessForm(false);
      setBusinessDescription('');
    } catch (error) {
      console.error('テンプレート生成エラー:', error);
      const errorMessage = {
        role: 'system',
        content: 'テンプレート生成中にエラーが発生しました。しばらく経ってからもう一度お試しください。'
      };
      setMessages([...messages, errorMessage]);
    } finally {
      setGeneratingTemplate(false);
    }
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
        
        // 抽出した表形式のHTML部分がある場合のみ置換える
        if (hasMatches) {
          // 補助金情報を含む部分を特定
          const startPattern = content.match(/(?:\d+\.\s+\*\*|-\s+\*\*|\*\*)/);
          const listStart = startPattern ? startPattern.index : 0;
          
          // 補助金リストの部分をテーブルに置換
          const beforeList = content.substring(0, listStart).trim();
          
          // 説明文があれば、それを保持
          const description = content.substring(listStart).trim();
          
          // AI拡張テンプレート作成ボタンを追加
          const actionButton = `
            <div class="action-button-container">
              <button 
                class="create-application-button" 
                onclick="document.getElementById('createTemplateBtn').click()"
              >
                AI申請書テンプレート作成
              </button>
            </div>
          `;
          
          return [beforeList, tableHtml, actionButton, description].filter(Boolean).join('');
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
              
              {/* 申請書テキスト表示セクション */}
              {message.applicationText && (
                <div className="application-form-container">
                  <div className="application-form-header">
                    <h3>
                      補助金申請書テンプレート
                      {message.aiEnhanced && <span className="ai-enhanced-tag">AI拡張</span>}
                    </h3>
                    <button 
                      className="copy-button"
                      onClick={() => copyToClipboard(message.applicationText)}
                    >
                      {copySuccess || 'コピー'}
                    </button>
                  </div>
                  <pre className="application-form-text">{message.applicationText}</pre>
                </div>
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
        
        {/* 補助金申請書作成フォーム */}
        {showBusinessForm && (
          <div className="business-form-overlay">
            <div className="business-form-container">
              <h3>AI拡張テンプレート作成</h3>
              <p>より具体的な申請書テンプレートを生成するために、事業内容や企業情報を入力してください：</p>
              
              <textarea
                className="business-description-input"
                value={businessDescription}
                onChange={(e) => setBusinessDescription(e.target.value)}
                placeholder="例: IT企業として、クラウドサービスの開発・運用を行っています。従業員10名、年商5000万円。今回、AI機能を追加したサービス展開を計画しています。"
                rows={5}
              />
              
              <div className="business-form-actions">
                <button 
                  className="cancel-button" 
                  onClick={handleCancelBusinessForm}
                  disabled={generatingTemplate}
                >
                  キャンセル
                </button>
                <button 
                  className="submit-button" 
                  onClick={handleGenerateAITemplate}
                  disabled={generatingTemplate}
                >
                  {generatingTemplate ? '生成中...' : 'テンプレート生成'}
                </button>
              </div>
            </div>
          </div>
        )}
        
        <form className="message-form" onSubmit={handleSendMessage}>
          {/* 補助金申請文章生成ボタン */}
          <div className="subsidy-button-container">
            <button 
              className="generate-subsidy-button" 
              onClick={handleCreateApplication}
              disabled={!currentSubsidyInfo || loading || generatingTemplate}
              type="button"
            >
              補助金申請文章を生成する
            </button>
          </div>

          <div className="input-container">
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
          </div>
        </form>
        
        {/* 隠れたボタン - JavaScriptからのクリックイベント用 */}
        <button 
          id="createTemplateBtn" 
          style={{ display: 'none' }} 
          onClick={handleCreateApplication}
        />
      </div>
    </div>
  );
}

export default App;
