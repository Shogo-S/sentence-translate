import streamlit as st
import os
import re
import json
from openai import OpenAI
from dotenv import load_dotenv

# .envファイルをロード
load_dotenv()

# OpenAIのAPIキーを環境変数から取得
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
    st.error("OpenAIのAPIキーが設定されていません。環境変数 'OPENAI_API_KEY' を設定してください。")
    st.stop()

# OpenAIクライアントの初期化
client = OpenAI(api_key=api_key)

# アプリのタイトル
st.title("英語文章の日本語翻訳アプリ")

# 英語文章の入力
english_text = st.text_area("英語の文章をここに貼り付けてください:", height=300)

def split_sentences(text):
    # テキストの前処理
    # 改行を空白に置換
    text = text.replace('\n', ' ')
    # 複数の空白を1つの空白に置換
    text = re.sub(r'\s+', ' ', text)
    
    # 文末のパターンを定義
    # ピリオド、感嘆符、疑問符の後に空白または文字列の終わりが来る場合をマッチ
    # ただし、Mr., Dr., etc. などの略語は除外
    exceptions = r'(?<!Mr)(?<!Mrs)(?<!Dr)(?<!Prof)(?<!Sr)(?<!Jr)(?<!vs)(?<!etc)'
    pattern = f'{exceptions}[.!?](?=\\s+[A-Z]|$)'
    
    # 文を分割
    sentences = re.split(pattern, text)
    
    # 分割後の文章を整形
    cleaned_sentences = []
    for sentence in sentences:
        # 文章の前後の空白を削除
        sentence = sentence.strip()
        if sentence:  # 空の文字列は除外
            # 文末の句読点を追加（最後の文字が .!? でない場合）
            if not sentence[-1] in '.!?':
                sentence += '.'
            cleaned_sentences.append(sentence)
    
    return cleaned_sentences

# 送信ボタン
if st.button("翻訳して表示"):
    if not english_text.strip():
        st.warning("翻訳する英語の文章を入力してください。")
    else:
        with st.spinner('翻訳中...'):
            try:
                # 改良した文章分割を使用
                sentences = split_sentences(english_text)

                # 翻訳用プロンプトを作成
                prompt = (
                    "以下の英語の文章を1文ずつ日本語に翻訳してください。"
                    "結果は以下の形式の完全なJSONオブジェクトで出力してください。\n\n"
                    "{\n"
                )
                for i, sentence in enumerate(sentences, 1):
                    # ダブルクォートをエスケープ
                    escaped_sentence = sentence.replace('"', '\\"')
                    prompt += f'  "文{i}": "{escaped_sentence}",\n'
                # 最後のカンマを削除するために条件分岐
                if prompt.endswith(",\n"):
                    prompt = prompt.rstrip(",\n") + "\n"
                prompt += "}\n\n"
                prompt += "必ず完全なJSON形式で出力してください。"

                # ChatCompletion APIを呼び出す
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that translates English sentences to Japanese and formats the output as JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,  # 必要に応じて調整
                    temperature=0
                )

                # レスポンスから翻訳結果を取得
                translation_content = response.choices[0].message.content.strip()

                # コードブロックを取り除く関数
                def extract_json(content):
                    # ```jsonで始まり```で終わる場合は取り除く
                    if content.startswith("```json") and content.endswith("```"):
                        return content[len("```json"): -len("```")].strip()
                    return content

                translation_json = extract_json(translation_content)

                # JSON形式であることを仮定してパース
                try:
                    translations = json.loads(translation_json)
                except json.JSONDecodeError as e:
                    st.error("翻訳結果のJSON解析に失敗しました。レスポンスの内容を確認してください。")
                    st.text(f"エラー詳細: {str(e)}")
                    st.text("翻訳結果の生データ:")
                    st.text(translation_json)
                    st.stop()

                # 日本語の文章をリストに格納
                japanese_sentences = list(translations.values())
                english_sentences = sentences  # 元の英語文リストを使用

                # セッションステートにデータを保存
                st.session_state.japanese_sentences = japanese_sentences
                st.session_state.english_sentences = english_sentences

                st.success("翻訳が完了しました！")

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# 翻訳結果の表示
if 'japanese_sentences' in st.session_state:
    st.header("日本語訳:")
    for idx, jp_sentence in enumerate(st.session_state.japanese_sentences, 1):
        with st.expander(f"{idx}.{jp_sentence}"):
            st.write(st.session_state.english_sentences[idx-1])