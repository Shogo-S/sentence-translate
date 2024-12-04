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
    exceptions = r'(?<!Mr)(?<!Mrs)(?<!Dr)(?<!Prof)(?<!Sr)(?<!Jr)(?<!vs)(?<!etc)'
    pattern = f'{exceptions}[.!?](?=\\s+[A-Z]|$)'
    
    # 文を分割
    sentences = re.split(pattern, text)
    
    # 分割後の文章を整形
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
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
                sentences = split_sentences(english_text)

                # 各文を個別に翻訳
                japanese_sentences = []
                for sentence in sentences:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a translator that translates English to Japanese."},
                            {"role": "user", "content": f"Translate this English sentence to Japanese: {sentence}"}
                        ],
                        max_tokens=1000,
                        temperature=0
                    )
                    
                    japanese_translation = response.choices[0].message.content.strip()
                    japanese_sentences.append(japanese_translation)

                st.session_state.japanese_sentences = japanese_sentences
                st.session_state.english_sentences = sentences

                st.success("翻訳が完了しました！")

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# 翻訳結果の表示
if 'japanese_sentences' in st.session_state:
    st.header("日本語訳:")
    for idx, (jp_sentence, en_sentence) in enumerate(zip(st.session_state.japanese_sentences, st.session_state.english_sentences), 1):
        with st.expander(f"{idx}. {jp_sentence}"):
            st.write("英語原文:")
            st.write(en_sentence)