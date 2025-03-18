# テスト駆動開発 (TDD) ガイドライン

## 1. TDDの基本サイクル

AIエージェント開発プロジェクトでは、以下のTDDサイクルを採用します：

### Red-Green-Refactor サイクル

1. **Red**: 失敗するテストを書く
- 実装したい機能を明確にする
- テストは実装前に記述し、必ず失敗することを確認する
- テストは機能要件を明確に表現したものであること

2. **Green**: 最小限のコードで成功させる
- テストが通るための最小限（必要十分）のコードを実装する
- この段階ではパフォーマンスやエレガントさより機能の正しさを優先する

3. **Refactor**: リファクタリングする
- コードの品質を高めるための改善を行う
- テストは引き続き成功する状態を維持する
- コードの重複を排除し、可読性を向上させる

## 2. テストの種類と役割

### 2.1 ユニットテスト

- 対象: 関数、メソッド、小さなクラス
- 目的: コードの最小単位の正確性を検証
- 特徴: 高速に実行可能、外部依存をモック化
- ツール: pytest
- 場所: 各機能モジュール内の `tests` ディレクトリ

```python
# 例: 音声変換サービスのユニットテスト
def test_convert_mp4_to_mp3():
    converter = AudioConverter()
    result = converter.convert("test.mp4", "mp3")
    
    assert result.format == "mp3"
    assert result.success is True
    assert os.path.exists(result.output_path)
```

### 2.2 統合テスト

- 対象: 複数のコンポーネントの相互作用
- 目的: コンポーネント間の連携が正しく機能することを確認
- 特徴: やや実行に時間がかかる、一部の外部依存を実際に使用
- 場所: `tests/integration` ディレクトリ

```python
# 例: ファイル処理と音声変換の統合テスト
def test_file_upload_and_conversion_flow():
    # テスト用ファイルをアップロード
    file_service = FileProcessingService()
    file_id = file_service.upload(test_mp4_file)
    
    # 音声変換を実行
    converter_service = AudioConversionService()
    result = converter_service.process_file(file_id)
    
    # 検証
    assert result.status == "completed"
    assert storage_service.exists(f"{file_id}/converted.mp3")
```

### 2.3 エンドツーエンド (E2E) テスト

- 対象: システム全体の機能
- 目的: ユーザーの視点からのシナリオ検証
- 特徴: 実行に時間がかかる、実際のサービスと連携
- 場所: `tests/e2e` ディレクトリ

```python
# 例: 音声ファイルアップロードから分析結果通知までのE2Eテスト
def test_full_analysis_workflow():
    # APIクライアントをセットアップ
    client = TestClient(app)
    
    # ファイルアップロード
    with open("test_samples/conversation.mp4", "rb") as f:
        response = client.post("/api/files/upload", files={"file": f})
    
    job_id = response.json()["job_id"]
    
    # 処理完了を待機（ポーリングまたはWebhook）
    result = wait_for_completion(job_id, timeout=120)
    
    # 結果の検証
    assert result["status"] == "completed"
    assert "excel_url" in result
    assert result["notification_sent"] is True
```

## 3. テストカバレッジ方針

- **目標カバレッジ**: コードベース全体で80%以上
- **重要コンポーネント**: 核となるビジネスロジックは90%以上
- **測定**: pytestとCoverageを使用
- **レポート**: CI/CDパイプラインで自動生成

## 4. モックとスタブの使用ガイドライン

### 4.1 モックを使用するケース

- 外部サービス（Azure Speech、Azure OpenAI等）の呼び出し
- データベース操作
- ファイルシステムアクセス
- 時間依存の処理

### 4.2 モック実装例

```python
# Azureサービスをモック化する例
@pytest.fixture
def mock_speech_service(monkeypatch):
    def mock_transcribe(*args, **kwargs):
        return {
            "text": "こんにちは、具合はどうですか？",
            "speaker": "veterinarian",
            "confidence": 0.95
        }
    
    monkeypatch.setattr("app.infrastructure.azure_speech.SpeechService.transcribe", 
                    mock_transcribe)
```

### 4.3 テストダブル選択指針

- **Stub**: 単純な戻り値が必要な場合
- **Mock**: 呼び出し回数や引数の検証が必要な場合
- **Fake**: 軽量な代替実装が必要な場合（インメモリDBなど）
- **Spy**: 実際の処理を行いつつ呼び出し情報も記録する場合

## 5. テストデータ管理

- テストデータは `tests/fixtures` ディレクトリに格納
- 大容量ファイルはGitに含めず、CIパイプラインで取得
- 機密データはテスト用に匿名化したものを使用
- フィクスチャとファクトリパターンを活用

```python
@pytest.fixture
def sample_conversation_data():
    return {
        "metadata": {
            "farm_id": "farm_123",
            "date": "2023-05-15",
            "duration": 630  # 10分30秒
        },
        "transcript": [
            {"time": 0, "speaker": "veterinarian", "text": "今日はどのような症状がありますか？"},
            {"time": 5, "speaker": "farmer", "text": "牛の食欲が昨日から落ちているんです"}
            # ...
        ]
    }
```

## 6. テスト自動化

### 6.1 ローカル開発環境

- コミット前に自動実行するプリコミットフック
- 変更されたコードに関連するテストのみ実行する機能

### 6.2 CI/CD パイプライン

- プルリクエスト時に全テストを自動実行
- テストカバレッジレポートの自動生成
- 失敗テストの通知とレポート

### 6.3 実行コマンド

```bash
# ユニットテストのみ実行
pytest app/

# 統合テストを実行
pytest tests/integration/

# E2Eテストを実行
pytest tests/e2e/

# カバレッジレポート付きで全テスト実行
pytest --cov=app --cov-report=html
```

## 7. TDDのベストプラクティス

### 7.1 テストファーストの原則

- 必ず実装前にテストを記述する
- テストが意味のある失敗を示すことを確認してから実装に進む

### 7.2 FIRST原則

- **Fast**: テストは高速に実行できること
- **Independent**: テスト間に依存関係がないこと
- **Repeatable**: 何度実行しても同じ結果が得られること
- **Self-validating**: テストは自己検証可能であること
- **Timely**: テストは実装前に書くこと

### 7.3 テストの表現力

- テスト名は検証内容を明確に表現する
- Given-When-Then パターンで条件、操作、期待結果を明確に
- ヘルパー関数を使って複雑なセットアップを抽象化

```python
def test_when_large_file_uploaded_then_chunked_processing_used():
    # Given: 大容量ファイルの準備
    large_file = create_test_file(size_mb=500)
    
    # When: ファイル処理サービスに渡す
    processor = FileProcessingService()
    result = processor.process(large_file)
    
    # Then: チャンク処理が適用されていることを確認
    assert result.processing_strategy == "chunked"
    assert len(result.chunks) > 1
```

## 8. 特定のテスト戦略

### 8.1 非同期コードのテスト

```python
@pytest.mark.asyncio
async def test_async_file_processing():
    processor = AsyncFileProcessor()
    result = await processor.process_file("test.mp4")
    assert result.status == "completed"
```

### 8.2 例外とエラー処理のテスト

```python
def test_invalid_file_format_raises_exception():
    converter = AudioConverter()
    
    with pytest.raises(InvalidFormatError) as exc_info:
        converter.convert("test.txt", "mp3")
    
    assert "Unsupported format" in str(exc_info.value)
```

### 8.3 分岐条件のテスト

各条件分岐を網羅するテストを作成し、すべてのパスが少なくとも1回は実行されるようにする。

### 8.4 Reactコンポーネントのテスト

#### 8.4.1 コンポーネントのユニットテスト

React Testing LibraryとJestを使用したコンポーネントのテスト例：

```jsx
// UserProfile.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import UserProfile from './UserProfile';

describe('UserProfile', () => {
  // レンダリングテスト
  test('ユーザー情報が正しく表示される', () => {
    const user = { name: '山田太郎', email: 'taro@example.com' };
    render(<UserProfile user={user} />);
    
    expect(screen.getByText('山田太郎')).toBeInTheDocument();
    expect(screen.getByText('taro@example.com')).toBeInTheDocument();
  });
  
  // イベントハンドリングのテスト
  test('編集ボタンをクリックするとフォームが表示される', () => {
    const user = { name: '山田太郎', email: 'taro@example.com' };
    render(<UserProfile user={user} />);
    
    // 初期状態ではフォームは表示されていない
    expect(screen.queryByLabelText('名前')).not.toBeInTheDocument();
    
    // 編集ボタンをクリック
    fireEvent.click(screen.getByText('編集'));
    
    // フォームが表示される
    expect(screen.getByLabelText('名前')).toBeInTheDocument();
    expect(screen.getByLabelText('メールアドレス')).toBeInTheDocument();
  });
  
  // フォーム送信のテスト
  test('フォーム送信時にonSubmitが呼ばれる', () => {
    const mockSubmit = jest.fn();
    const user = { name: '山田太郎', email: 'taro@example.com' };
    render(<UserProfile user={user} onSubmit={mockSubmit} />);
    
    // 編集モードに切り替え
    fireEvent.click(screen.getByText('編集'));
    
    // フォームの値を変更
    fireEvent.change(screen.getByLabelText('名前'), {
      target: { value: '山田花子' }
    });
    
    // フォームを送信
    fireEvent.click(screen.getByText('保存'));
    
    // onSubmitが呼ばれたことを確認
    expect(mockSubmit).toHaveBeenCalledWith({
      name: '山田花子',
      email: 'taro@example.com'
    });
  });
});
```

#### 8.4.2 カスタムフックのテスト

```jsx
// useCounter.test.js
import { renderHook, act } from '@testing-library/react-hooks';
import useCounter from './useCounter';

describe('useCounter', () => {
  test('初期値が正しく設定される', () => {
    const { result } = renderHook(() => useCounter(10));
    expect(result.current.count).toBe(10);
  });
  
  test('incrementで値が増加する', () => {
    const { result } = renderHook(() => useCounter(0));
    
    act(() => {
      result.current.increment();
    });
    
    expect(result.current.count).toBe(1);
  });
  
  test('decrementで値が減少する', () => {
    const { result } = renderHook(() => useCounter(5));
    
    act(() => {
      result.current.decrement();
    });
    
    expect(result.current.count).toBe(4);
  });
});
```

#### 8.4.3 Redux連携のテスト

```jsx
// UserList.test.js
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureMockStore from 'redux-mock-store';
import UserList from './UserList';

const mockStore = configureMockStore();

describe('UserList', () => {
  test('ユーザーリストが表示される', () => {
    const users = [
      { id: 1, name: '山田太郎' },
      { id: 2, name: '鈴木花子' }
    ];
    
    const store = mockStore({
      users: { data: users, loading: false, error: null }
    });
    
    render(
      <Provider store={store}>
        <UserList />
      </Provider>
    );
    
    expect(screen.getByText('山田太郎')).toBeInTheDocument();
    expect(screen.getByText('鈴木花子')).toBeInTheDocument();
  });
  
  test('ローディング中はローディングインジケータが表示される', () => {
    const store = mockStore({
      users: { data: [], loading: true, error: null }
    });
    
    render(
      <Provider store={store}>
        <UserList />
      </Provider>
    );
    
    expect(screen.getByText('読み込み中...')).toBeInTheDocument();
  });
});
```

#### 8.4.4 APIリクエストのモック

```jsx
// UserDetails.test.js
import { render, screen, waitFor } from '@testing-library/react';
import axios from 'axios';
import UserDetails from './UserDetails';

// axiosをモック化
jest.mock('axios');

describe('UserDetails', () => {
  test('APIから取得したユーザーの詳細情報が表示される', async () => {
    // モックレスポンスの設定
    axios.get.mockResolvedValue({
      data: {
        id: 1,
        name: '山田太郎',
        email: 'taro@example.com',
        phone: '03-1234-5678'
      }
    });
    
    render(<UserDetails userId={1} />);
    
    // 初期状態では読み込み中
    expect(screen.getByText('読み込み中...')).toBeInTheDocument();
    
    // データ読み込み完了を待機
    await waitFor(() => {
      expect(screen.getByText('山田太郎')).toBeInTheDocument();
    });
    
    // 詳細情報が表示されていることを確認
    expect(screen.getByText('taro@example.com')).toBeInTheDocument();
    expect(screen.getByText('03-1234-5678')).toBeInTheDocument();
    
    // APIが正しいパラメータで呼び出されたことを確認
    expect(axios.get).toHaveBeenCalledWith('/api/users/1');
  });
});
```

## 9. コードレビューとテスト

コードレビューでは以下の点を重点的に確認します：

1. テストが機能要件を適切にカバーしているか
2. テスト自体の品質は適切か
3. エッジケースや例外パターンがテストされているか
4. テストの可読性と保守性は確保されているか

## 10. 継続的改善

- テスト戦略を定期的に見直し、改善する
- 重要な障害発生時には、該当するケースのテストを追加
- チーム内でテスト技術の共有と学習を促進