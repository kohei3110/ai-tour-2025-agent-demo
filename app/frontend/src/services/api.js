// API通信を管理するサービス

// バックエンドのベースURL
const API_BASE_URL = process.env.NODE_ENV === 'production' ? '/api' : (process.env.REACT_APP_API_URL || 'http://localhost:8000/api');

/**
 * チャットAPIにメッセージを送信する
 * @param {string} message - ユーザーのメッセージ
 * @returns {Promise} - レスポンスとソース引用を含むオブジェクトのPromise
 */
export const sendChatMessage = async (message) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    // バックエンドからの応答形式："response"にアシスタントメッセージ、"sources"に引用URL、"query"に検索クエリが含まれる
    return {
      response: data.response,
      sources: data.sources,
      query: data.query,
      applicationText: data.application_text // 新しく追加された申請書テキスト
    };
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

/**
 * 補助金申請書テンプレートをAIで生成する
 * @param {Object} subsidyInfo - 補助金情報の辞書
 * @param {string} businessDescription - ビジネスの簡単な説明（任意）
 * @returns {Promise} - 生成された申請書テンプレートを含むオブジェクトのPromise
 */
export const generateApplicationTemplate = async (subsidyInfo, businessDescription = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/application/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        subsidy_info: subsidyInfo,
        business_description: businessDescription
      }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const data = await response.json();
    return {
      template: data.template,
      aiEnhanced: data.ai_enhanced
    };
  } catch (error) {
    console.error('Application template generation failed:', error);
    throw error;
  }
};

/**
 * 会話の履歴を取得する（実装予定）
 * @returns {Promise} - レスポンスのPromise
 */
export const getConversationHistory = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

/**
 * AIにプロンプトを送信してメッセージを生成する
 * @param {string} prompt - AIに送信するプロンプト
 * @returns {Promise} - 生成されたメッセージのPromise
 */
export const generateMessage = async (prompt) => {
  try {
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    const data = await response.json();
    return {
      generatedText: data.generated_text,
      success: data.success
    };
  } catch (error) {
    console.error('Message generation failed:', error);
    throw error;
  }
};