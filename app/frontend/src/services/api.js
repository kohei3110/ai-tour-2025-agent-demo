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
      query: data.query
    };
  } catch (error) {
    console.error('API request failed:', error);
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