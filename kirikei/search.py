import requests
import json
import os

from dotenv import load_dotenv

def get_google_search_results(query: str, num_results: int = 100, forced: bool = False) -> list:
  """
  Google Custom Search JSON API を使用して検索結果を取得します。

  Args:
      query (str): 検索キーワード。
      num_results (int): 取得する検索結果の件数 (最大100件)。
      forced (bool): 強制的に検索を実行するかどうか。デフォルトはFalse。

  Returns:
      list[dict]: 検索結果のリスト。各要素は辞書形式の検索結果アイテムです。
            エラーが発生した場合は空のリストを返します。
  """
  if not 1 <= num_results <= 100:
    print("Error: num_results must be between 1 and 100.")
    return []

  load_dotenv()  # .envファイルの読み込み
  # API-KEYの設定
  GOOGLE_API_KEY=os.getenv('CUSTOM_SEARCH_API_KEY')
  GOOGLE_CX_ID=os.getenv('CX_ID_KEY')

  base_url = "https://www.googleapis.com/customsearch/v1"
  results = []
  
  if forced:
    print('強制的に検索を実行します。')
    # Google Custom Search APIは1リクエストあたり最大10件の結果しか返さないため、
    # 100件取得するには複数回リクエストを送信する必要があります。
    # startパラメータで開始位置を指定します。
    for i in range(0, num_results, 10):
      start_index = i + 1
      params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX_ID,
        "q": query,
        "start": start_index,
        "num": min(10, num_results - i)  # 残りの件数を考慮して取得する件数を調整
      }

      try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # HTTPエラーがあれば例外を発生させる
        data = response.json()

        if "items" in data:
          results.extend(data["items"])
        else:
          print(f"No more results found or 'items' not in response at start_index {start_index}.")
          break # 'items'がない場合はそれ以上結果がないと判断

      except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        break
      except json.JSONDecodeError as e:
        print(f"JSON decoding failed: {e}")
        break
      except Exception as e:
        print(f"An unexpected error occurred: {e}")
        break

      # 取得したい件数に達したら終了
      if len(results) >= num_results:
        break
    
    #結果をjsonファイルに保存
    with open('search_results.json', 'w', encoding='utf-8') as f:
      json.dump(results, f, ensure_ascii=False, indent=2)
  
  else:
    print('検索結果を既存のJSONファイルから取得します。')
    # 既存のJSONファイルから検索結果を取得
    try:
      with open('search_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)
    except FileNotFoundError:
      print('search_results.jsonが見つかりません。Webから取得します。')
      return get_google_search_results(query, num_results, forced=True)

  # num_resultsで指定された件数に切り詰める（最後のループで多く取得する可能性を考慮）
  return results[:num_results]

if __name__ == "__main__":

  search_query = "BIツール 公式サイト"  # 検索キーワード
  num_to_fetch = 20

  # 環境変数からAPIキーと検索エンジンIDを取得
  print(f"Searching for '{search_query}' (top {num_to_fetch} results)...")
  search_results = get_google_search_results(search_query, num_to_fetch)

  if search_results:
    print(f"Found {len(search_results)} results:")
    for i, item in enumerate(search_results):
      print(f"--- Result {i+1} ---")
      print(f"Title: {item.get('title', 'N/A')}")
      print(f"Link: {item.get('link', 'N/A')}")
      print(f"Snippet: {item.get('snippet', 'N/A')}")
      print("-" * 20)
  else:
    print("No search results found or an error occurred.")