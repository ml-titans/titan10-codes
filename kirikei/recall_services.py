import os
import json

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

import matplotlib.pyplot as plt
import matplotlib_venn as venn

import scrape
import search

class Service(BaseModel):
  """サービス情報を表すモデル
  Attributes:
    service_name (str): サービスの名前
    know (bool): サービスの情報を知っているかどうか
    
  Raises:
    ValueError: サービス名が空文字列の場合
  """
  
  service_name: str
  know: bool = False
 
def get_services_from_gemini(services_list):
  """Gemini APIを使用してBIツールの情報を取得する関数
  この関数は、Gemini APIを使用して、services_listに含まれるBIツールを知っているかどうかを確認します。
  Returns:
    list[Dict]: サービスのリスト
  """
  # https://zenn.dev/peishim/articles/2e2e8408888f59
  # https://ai.google.dev/gemini-api/docs/text-generation?hl=ja
  
  # .envファイルの読み込み
  load_dotenv()
  
  # API-KEYの設定
  GOOGLE_API_KEY=os.getenv('GEMINI_API_KEY')
  client = genai.Client(api_key=GOOGLE_API_KEY)
  
  # Gemini APIを使用してBIツールの情報を取得
  response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=f"以下のBIツールを知っていますか？\n{', '.join(services_list)}\n\nそれぞれのBIツールについて、知っている場合はTrue、知らない場合はFalseで答えてください。ただし、回答は日本語で行ってください。Web検索は使用せず、あなたが知っている情報に基づいて回答してください。", 
    # 日本語で指定しないと英語で回答される
    config={
      "temperature": 0, # 出力の多様性を制御するための温度パラメータ
      "response_mime_type": "application/json", # レスポンスのMIMEタイプをJSONに設定
      "response_schema": list[Service], # Pydanticモデルを使用してレスポンスを定義
    }
  )
  # レスポンスの文字列をlist[dict]型に変換
  response = json.loads(response.text)

  # レスポンスをパースしてサービスのリストを作成
  service_know_gemini = []
  for item in response:
    if item['service_name'] and item['know'] is not None:
      service_know_gemini.append(dict(service_name=item['service_name'], know=item['know']))

  return service_know_gemini


def check_services_in_search(services_list: list, search_results: list) -> list[Service]:
  """Google Custom Search APIの結果からBIツールの情報を確認する関数
  この関数は、Google Custom Search APIの結果から、services_listに含まれるBIツールの情報を確認します。
  Returns:
    list[Service]: サービスのリスト
  """
  service_know_search = []
  
  for service in services_list:
    know = any(service.lower() in result['title'].lower() or service.lower() in result['snippet'].lower() for result in search_results)
    service_know_search.append(dict(service_name=service, know=know))
  
  return service_know_search

if __name__ == "__main__":
  # ITreviewからBIツールの情報を取得する
  service_list = scrape.get_bi_service_list() 
  
  # geminiからBIツールの情報を取得する
  service_know_gemini = get_services_from_gemini(service_list)
  print(service_know_gemini)
  
  # 結果をJSONファイルに保存
  with open('bi_service_recall_know_gemini.json', 'w', encoding='utf-8') as f:
    json.dump(service_know_gemini, f, ensure_ascii=False, indent=2)
  
  # Google Custom Search APIを使用してBIツールの公式サイトを検索する
  # 10ページまでの検索結果を取得
  query = "BIツール 公式サイト"
  service_search = search.get_google_search_results(query, num_results=100)

  # 検索結果の中にサービス名が含まれているかを確認する
  service_know_search = check_services_in_search(service_list, service_search)
  print(service_know_search)
  
  # geminiの結果と検索結果をmatplotlibのベン図で比較する
  # ここではmatplotlibを使用してベン図を描画するコードを追加することができます。
  set_gemini = set([s['service_name'] for s in service_know_gemini if s['know']])
  set_search = set([s['service_name'] for s in service_know_search if s['know']])
  venn_labels = {
      '10': len(set_gemini - set_search),
      '01': len(set_search - set_gemini),
      '11': len(set_gemini & set_search)
  }
  plt.figure(figsize=(8, 8))
  venn.venn2(subsets=venn_labels, set_labels=('Gemini', 'Search Results'))
  plt.title("Gemini vs Search Results")
  # ベン図をpngファイルとして保存
  plt.savefig('venn_diagram.png', format='png')
  plt.show()
  
  print('Geiminiのみ知っている', set_gemini - set_search)
  print('検索のみ知っている', set_search - set_gemini)