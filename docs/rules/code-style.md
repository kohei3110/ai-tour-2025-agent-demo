# コーディング規約

## 1. 一般原則

### 1.1 コードの明瞭性
- シンプルで読みやすいコードを優先する
- 過度な最適化よりも可読性を重視する
- 自己文書化コードを目指し、適切な変数名・関数名を選定する

### 1.2 一貫性
- プロジェクト全体で統一されたスタイルを維持する
- 既存のコードパターンに従う
- 個人の好みよりもチームの規約を優先する

### 1.3 DRY原則 (Don't Repeat Yourself)
- コードの重複を避け、共通処理は抽象化する
- 類似コードは共通の抽象化を検討する
- ただし、過度な抽象化による複雑化も避ける

## 2. Python コーディングスタイル

### 2.1 PEP 8準拠
- [PEP 8](https://www.python.org/dev/peps/pep-0008/) スタイルガイドに従う
- インデントは4スペースを使用
- 行の長さは最大100文字に制限

### 2.2 命名規則
- クラス名: UpperCamelCase (例: `AudioProcessor`)
- 関数/メソッド名: snake_case (例: `convert_audio_format`)
- 変数名: snake_case (例: `audio_file`)
- 定数名: UPPER_SNAKE_CASE (例: `MAX_FILE_SIZE`)
- プライベート変数/メソッド: 先頭にアンダースコア (例: `_internal_method`)

### 2.3 インポート
- インポートは適切にグループ化し、以下の順序で記述する:
1. 標準ライブラリ
2. サードパーティライブラリ
3. ローカルアプリケーション/ライブラリ
- 各グループ内はアルファベット順にソート
- ワイルドカードインポート (`from x import *`) は避ける

```python
# 正しいインポート例
import os
import sys
from typing import Dict, List

import numpy as np
import pandas as pd
from fastapi import FastAPI

from app.features.audio_conversion import AudioConverter
from app.shared.utils import format_timestamp
```

### 2.4 ドキュメンテーション
- すべての公開API、クラス、関数にはdocstringを記述する
- Google スタイルのdocstringを使用
- 複雑なロジックには適切なインラインコメントを付与

```python
def convert_audio(input_file: str, output_format: str = "mp3") -> str:
    """音声ファイルを指定されたフォーマットに変換する.
    
    Args:
        input_file: 入力ファイルのパス
        output_format: 出力形式 (デフォルト: "mp3")
        
    Returns:
        変換後のファイルパス
        
    Raises:
        FileNotFoundError: 入力ファイルが存在しない場合
        ConversionError: 変換処理に失敗した場合
    """
    # 実装...
```

### 2.5 型ヒント
- すべての関数とメソッドには型ヒントを使用する
- 複雑な型は `typing` モジュールを活用する
- 型ヒントはドキュメントとして役立つだけでなく、静的解析ツールにも活用される

## 3. プロジェクト固有のルール

### 3.1 エラー処理
- 例外は具体的な型を使用し、汎用的な `Exception` は避ける
- カスタム例外は `app/shared/exceptions` に定義
- すべての例外は適切にログに記録する

### 3.2 ログ記録
- システムの動作状況を把握できるよう、適切なログレベルを使用
- ログメッセージは情報を明確に伝える内容にする
- 個人情報や機密情報のログ出力は避ける

```python
# 正しいログ記録例
logger.info(f"File processing started: {file_id}")
logger.error(f"Conversion failed for file {file_id}: {str(error)}")
```

### 3.3 テスト
- すべての機能にはユニットテストを書く
- モックを適切に使用して外部依存を分離する
- 重要なユースケースには結合テストとE2Eテストを用意

### 3.4 非同期処理
- I/O待ち時間が長い処理は非同期（async/await）を使用
- ブロッキング処理はバックグラウンドタスクとして実行
- 適切なタイムアウト処理を実装

### 3.5 JavaScript コーディングスタイル

#### 3.5.1 基本ルール
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) に準拠する
- セミコロンは必須
- インデントは2スペースを使用
- 行の長さは最大100文字に制限

#### 3.5.2 命名規則
- 変数・関数名: camelCase (例: `getUserData`)
- クラス・コンポーネント: PascalCase (例: `UserProfile`)
- 定数: UPPER_SNAKE_CASE (例: `MAX_RETRY_COUNT`)
- プライベート変数/メソッド: 先頭にアンダースコア (例: `_privateMethod`)

#### 3.5.3 モジュール化
- ESモジュール構文を使用する (`import`/`export`)
- 名前付きエクスポートを優先し、デフォルトエクスポートは適切な場合のみ使用

```javascript
// 好ましいモジュールパターン
export function calculateTotal(items) {
  // 実装...
}

export const TAX_RATE = 0.1;

// コンポーネントなどの場合はデフォルトエクスポートも可
export default class UserProfile extends Component {
  // 実装...
}
```

#### 3.5.4 React コンポーネント
- 関数コンポーネントを優先し、必要な場合のみクラスコンポーネントを使用
- Hooksを適切に活用する（不要な再レンダリングを避ける）
- コンポーネントは単一責任の原則に従う
- PropTypesまたはTypeScriptによる型定義を必須とする

```javascript
// 好ましいReactコンポーネントパターン
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const UserCard = ({ username, email, onProfileClick }) => {
  const [isActive, setIsActive] = useState(false);
  
  useEffect(() => {
    // 副作用の実装...
    return () => {
      // クリーンアップ...
    };
  }, []);
  
  return (
    <div className="user-card" onClick={() => onProfileClick(username)}>
      <h3>{username}</h3>
      <p>{email}</p>
    </div>
  );
};

UserCard.propTypes = {
  username: PropTypes.string.isRequired,
  email: PropTypes.string.isRequired,
  onProfileClick: PropTypes.func.isRequired,
};

export default UserCard;
```

#### 3.5.5 エラー処理
- Promiseの拒否は常にcatchブロックで処理する
- try/catchブロックを使用して例外を適切に処理する
- ユーザーに分かりやすいエラーメッセージを表示する

```javascript
// エラー処理の例
async function fetchUserData(userId) {
  try {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  } catch (error) {
    if (error.response && error.response.status === 404) {
      throw new NotFoundError('ユーザーが見つかりません');
    }
    logger.error(`ユーザーデータ取得エラー: ${error.message}`);
    throw new ApiError('ユーザー情報の取得に失敗しました');
  }
}
```

#### 3.5.6 テスト
- Jestを使用してユニットテストを書く
- React Testing Libraryでコンポーネントテストを実施
- スナップショットテストは必要に応じて使用する
- モックを適切に使用して外部依存を分離する

```javascript
// テストの例
describe('UserCard', () => {
  it('正しくユーザー情報をレンダリングする', () => {
    const handleClick = jest.fn();
    const { getByText } = render(
      <UserCard 
        username="testuser" 
        email="test@example.com" 
        onProfileClick={handleClick} 
      />
    );
    
    expect(getByText('testuser')).toBeInTheDocument();
    expect(getByText('test@example.com')).toBeInTheDocument();
  });
  
  it('クリック時にコールバックが呼ばれる', () => {
    const handleClick = jest.fn();
    const { container } = render(
      <UserCard 
        username="testuser" 
        email="test@example.com" 
        onProfileClick={handleClick} 
      />
    );
    
    fireEvent.click(container.firstChild);
    expect(handleClick).toHaveBeenCalledWith('testuser');
  });
});
```

## 4. コード品質ツール

以下のツールを用いて継続的にコード品質を確保する:

- **Black**: コードフォーマッタ
- **isort**: インポート順序の最適化
- **Flake8**: スタイルガイドの遵守チェック
- **mypy**: 静的型チェック
- **Pylint**: コード品質分析
- **Bandit**: セキュリティの脆弱性スキャン

## 5. コードレビュー基準

コードレビューでは以下の点に注目する:

- 機能要件の充足
- コーディング規約の遵守
- アーキテクチャ設計原則の遵守
- テストの充実度
- エラー処理の適切さ
- パフォーマンスへの配慮
- セキュリティ上の懸念

## 6. バージョン管理

- コミットメッセージは明確で説明的に記述
- [Conventional Commits](https://www.conventionalcommits.org/) の形式に従う
- 機能単位でブランチを分け、完了後にプルリクエストを作成

```
feat: 音声ファイル変換機能の追加
fix: 大容量ファイル処理時のメモリリーク修正
docs: APIドキュメントの更新
test: 音声認識サービスのテストケース追加
```