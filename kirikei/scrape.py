import requests
import json

from bs4 import BeautifulSoup

def get_bi_service_list(forced=False) -> list:
  """BIツールのサービス名を取得する関数
  この関数は、IT reviewのBIカテゴリページからサービス名を取得します。
  Returns:
      list: BIツールのサービス名のリスト
  Raises:
      Exception: リクエストやパースに失敗した場合
  Notes:
      - IT reviewのBIカテゴリページをスクレイピングしてサービス名を取得します。
      - 1ページ目から15ページ目までのサービスを取得します。
      - サービス名はリストで返されます。
  Example:
      >>> get_bi_service_list()
      ['Tableau', 'Power BI', 'Looker', ...]
  """

  # https://qiita.com/go_honn/items/ec96c2246229e4ee2ea6

  # IT reviewから引っ張ってくる
  URL = 'https://www.itreview.jp/categories/bi?page={}#category-products-list-link'

  service_list = []
  
  if forced:
    print('サービス名を強制的に取得します。')
    # 1ページ目か15ページ目までのサービスを取得
    for i in range(1, 15):
      try: 
        page = requests.get(URL.format(i))
        # htmlをパース
        soup = BeautifulSoup(page.text, 'html.parser')
        # サービス名を含む要素を取得
        # class名が'product-card'のdiv要素を全て取得
        product_cards = soup.find_all('div', {'class':'product-card'})
        
        # 各サービス名をリストに追加
        for p in product_cards:
          service_name = p.find('a', text=True).string
          
          # かっこ書きのサービス名は除外
          if '（' in service_name:
            service_name = service_name.split('（')[0].strip()

          service_list.append(service_name)
        
          
      except Exception as e:
        print(f"Error occurred while processing page {i}.")
        # エラーが発生した場合はループを抜ける
        break
    
    # jsonファイルに保存
    with open('bi_services.json', 'w', encoding='utf-8') as f:
      json.dump(service_list, f, ensure_ascii=False, indent=2)
      
  else:
    print('サービス名を既存のJSONファイルから取得します。')
    # 既存のJSONファイルからサービス名を取得
    try:
      with open('bi_services.json', 'r', encoding='utf-8') as f:
        service_list = json.load(f)
    except FileNotFoundError:
      print('bi_services.jsonが見つかりません。Webから取得します。')
      return get_bi_service_list(forced=True)

  print('サービス数:', len(service_list))
  return service_list

if __name__ == "__main__":
  print(get_bi_service_list())