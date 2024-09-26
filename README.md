# 千葉県案内チャットボットバックエンド

## 概要

本プロジェクトは、千葉県に関する行政情報、銘菓情報、旅行情報などをもとに、ユーザーの質問に最適な回答を生成するチャットボットアプリケーションのバックエンドです。

## 必要なもの

- Python 3.12.3

## セットアップ

1. アプリケーションを実行します。<br />
Pythonを実行するための仮想環境を構築します。下記のリンクを参考してください。<br />
https://qiita.com/futakuchi0117/items/6030458a96f62cb64d37<br />
https://qiita.com/fiftystorm36/items/b2fd47cf32c7694adc2e

2. 必要なPythonパッケージをインストールします。
```
pip install -r requirements.txt
```

3. `.env` ファイルをプロジェクトのルートディレクトリに作成し、`SECRET_KEY`と`OPENAI_API_KEY` を設定します。
```
SECRET_KEY=あなたの秘密鍵
OPENAI_API_KEY=あなたの秘密鍵
```

## 実行方法
```
py app.py
```

2. ブラウザを開き、`http://localhost:5000` にアクセスして、アプリケーションをテストします。