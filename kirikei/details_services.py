import os
import json

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

import matplotlib.pyplot as plt
import matplotlib_venn as venn

import scrape
import search
import recall_services

class ServiceDetail(BaseModel):
  """サービス情報を表すモデル
  Attributes:
    service_name (str): サービスの名前
    url (str): サービスの公式サイトURL
    company (str): サービスを提供する会社名
    explanation (list[str]): サービスの説明
    
  Raises:
    ValueError: サービス名が空文字列の場合
  """
  
  service_name: str
  url: str
  company: str
  explanation: list[str]

class ServiceScore(BaseModel):
  """サービスのスコアを表すモデル
  Attributes:
    service_name (str): サービスの名前
    score (float): サービスのスコア
  """
  
  service_name: str
  score: float = 0.0
 
def get_service_details_from_gemini(services_list):
  """Gemini APIを使用してBIツールの情報を取得する関数
  この関数は、Gemini APIを使用して、services_listに含まれるBIツールの詳細を取得します。
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
    contents=f"以下のBIツールを知っていますか？\n{', '.join(services_list)}\n\nそれぞれのBIツールについて、名前を知っているかどうか、知っている場合は公式サイトのURL、会社名、説明を教えてください。ただし、回答は日本語で行ってください。Web検索は使用せず、あなたが知っている情報に基づいて回答してください。もし知らない情報があれば、Noneと答えてください。", 
    # 日本語で指定しないと英語で回答される
    config={
      "temperature": 0, # 出力の多様性を制御するための温度パラメータ
      "response_mime_type": "application/json", # レスポンスのMIMEタイプをJSONに設定
      "response_schema": list[ServiceDetail], # Pydanticモデルを使用してレスポンスを定義
    }
  )
  # レスポンスの文字列をlist[dict]型に変換
  response = json.loads(response.text)

  return response

def check_details(service_details: list[dict]):
  """取得したサービスの詳細情報をチェックする関数
  この関数は、取得したサービスの詳細情報が正しいかどうかをチェックします。
  
  Args:
    response (list[dict]): サービスの詳細情報のリスト
  
  Returns:
    None
  """
  # .envファイルの読み込み
  load_dotenv()
  
  # API-KEYの設定
  GOOGLE_API_KEY=os.getenv('GEMINI_API_KEY')
  client = genai.Client(api_key=GOOGLE_API_KEY)
  
  # Gemini APIを使用してBIツールの情報を取得
  response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=f"以下はLLMが返答したBIツールに関する内容です。\n\n{service_details}\n\nそれぞれのBIツールについて、Web検索を利用して、公式サイトのURL、会社名、説明が正しいかを確認し、以下の基準でスコアづけしてください。\n\n 情報が全て正しくない: 1 \n 会社名のみ正しい: 2 \n URLのみ正しい: 2 \n 会社名とURLのみ正しい: 3 \n 全ての情報が正しい: 4。\n\n ただし、回答は日本語で行ってください。", 
    # 日本語で指定しないと英語で回答される
    config={
      "temperature": 0,
      "response_mime_type": "application/json", # レスポンスのMIMEタイプをJSONに設定
      "response_schema": list[ServiceScore], # Pydanticモデルを使用してレスポンスを定義
    }
  )
  # レスポンスの文字列をlist[dict]型に変換
  response = json.loads(response.text)

  return response

def remove_unknown_services(service_details: list[dict]) -> list[dict]:
  """サービスの詳細情報から知らないサービスを除外する関数
  この関数は、サービスの詳細情報から知らないサービスを除外します。
  
  Args:
    service_details (list[dict]): サービスの詳細情報のリスト
  
  Returns:
    list: 知っているサービスの詳細情報のリスト
  """
  return [service['service_name'] for service in service_details if service['know']]

if __name__ == "__main__":
  # ITreviewからBIツールのサービス名を取得
  service_list = scrape.get_bi_service_list()  # BIツールのサービス名を取得

  # geminiからBIツールの情報を取得
  service_list_gemini = recall_services.get_services_from_gemini(service_list)
  
  # 知っているサービスのみを抽出
  known_service_list = remove_unknown_services(service_list_gemini)
  
  # geminiから知っているBIツールの詳細情報を取得
  service_details_gemini = get_service_details_from_gemini(known_service_list)
  print(service_details_gemini)
  # 結果をJSONファイルに保存
  with open('bi_service_details_gemini.json', 'w', encoding='utf-8') as f:
    json.dump(service_details_gemini, f, ensure_ascii=False, indent=2)

  services_scores = check_details(service_details_gemini)
  print(services_scores)
  
  # 知らないサービスをスコア0点として追加
  for service in service_list:
    if service not in [s['service_name'] for s in services_scores]:
      services_scores.append(dict(service_name=service, score=0.0))
  
  # 結果をJSONファイルに保存
  with open('bi_service_scores_gemini.json', 'w', encoding='utf-8') as f:
    json.dump(services_scores, f, ensure_ascii=False, indent=2)
    
  # services_scoresをヒストグラムに変換
  scores = [service['score'] for service in services_scores]
  plt.hist(scores, bins=5, edgecolor='black')
  plt.title('BI Service Scores Distribution')
  plt.xlabel('Score')
  plt.ylabel('Frequency')
  plt.xticks(range(1, 6))
  plt.grid(axis='y', alpha=0.75)
  plt.savefig('bi_service_scores_distribution.png')
  plt.show()