import os
import json

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
import pandas as pd

import search

class Service(BaseModel):
  """サービス情報を表すモデル
  Attributes:
    service_name (str): サービスの名前
    explanation (list[str]): サービスの説明
  """
  service_name: str
  explanation: list[str]
 
def get_services_from_gemini():
  """Gemini APIを使用してBIツールの情報を取得する関数
  この関数は、Gemini APIを使用して日本で利用されるBIツールのトップ10サービスとその説明を取得します。
  Returns:
    None
  """
  # https://zenn.dev/peishim/articles/2e2e8408888f59
  # https://ai.google.dev/gemini-api/docs/text-generation?hl=ja
  
  # .envファイルの読み込み
  load_dotenv()
  
  # API-KEYの設定
  GOOGLE_API_KEY=os.getenv('GEMINI_API_KEY')
  client = genai.Client(api_key=GOOGLE_API_KEY)
  
  response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="日本で利用される典型的なBIツールのトップ10サービスを有名な順にあげなさい。また、回答には説明を含むこと。回答は日本語とすること。さらに、BIツールの選定においてWeb検索は使わず、あなたが知っている情報に基づいて回答すること。", 
    # 日本語で指定しないと英語で回答される
    config={
      "temperature": 0, # 出力の多様性を制御するための温度パラメータ
      "response_mime_type": "application/json", # レスポンスのMIMEタイプをJSONに設定
      "response_schema": list[Service], # Pydanticモデルを使用してレスポンスを定義
    }
  )
  
  # レスポンスの文字列をlist[dict]型に変換
  response = json.loads(response.text)
  
  return response

if __name__ == "__main__":
  # geminiからBIツールの情報を取得する
  gemini_result = get_services_from_gemini()
  
  # Google Custom Search APIを使用してBIツールの情報を取得する
  search_query = "BIツール 公式サイト"  # 検索キーワード
  num_to_fetch = 20
  search_results = search.get_google_search_results(
    search_query, num_results=num_to_fetch)

  # geminiとsearchの結果を表にして並べて表示する
  df_gemini = pd.DataFrame([s['service_name'] for s in gemini_result], columns=['gemini'])
  df_search = pd.DataFrame([s['title'] for s in search_results], columns=['search'])

  df = pd.concat([df_gemini, df_search], axis=1)
  print(df)