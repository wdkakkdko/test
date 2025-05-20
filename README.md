# Install

## Install library(想定環境:Python 3.11.3)

```
pip install opencv-python ttkbootstrap pillow numpy pandas google-generativeai

```
## Setup
以下のURLを参照し、APIトークンを発行したうえで、Applicationクラス内のコンストラクタ(__init__関数)で定義されたself.GEMINI_API_KEYにAPIトークンを代入してください

参照：https://ai.google.dev/gemini-api/docs/quickstart?hl=ja&lang=python

```
self.GEMINI_API_KEY = "" #Gemini apiのtokenを指定(ダブルクォーテーション内に貼り付け)
        
```

## Run

```
python3 gui3_object.py
```

## Note
Gemini API(gemini-2.0-flash-lite)を利用しているため、1分間で登録するデータ数を30データ以内、一日で登録するデータ数を1500データ以内に抑えること
csvファイルは一行目のヘッダ行に|name|position|を記載しておく必要があります(name:商品名、position:棚番号を想定)



