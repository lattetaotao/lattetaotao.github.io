import os
import requests
import json
from datetime import datetime


def fetch_all_scholar_data(scholar_id: str, api_key: str) -> dict:
    """
    使用SerpApi获取一位作者的全部学术信息，包括所有出版物。
    """
    all_articles = []
    page_num = 0

    # 1. 设置API请求参数，这次我们加入了 "location"
    # 这是让请求成功的关键！
    print("正在向 SerpApi 发送带有Location参数的初始请求...")
    params = {
        "engine": "google_scholar_author",
        "author_id": scholar_id,
        "api_key": api_key,
        # "location": "Malaysia"  # 您可以换成任何在Playground测试有效的地点
        "hl": "en"
    }
    response = requests.get("https://serpapi.com/search.json", params=params)

    if response.status_code != 200:
        print(f"错误：初始API请求失败，状态码: {response.status_code}")
        print("返回内容:", response.text)
        return None

    data = response.json()
    print("初始请求成功！")

    # 保存作者的基础信息和引用统计
    author_info = data.get('author', {})
    # 新的、成功的JSON里，引用数据在这个'cited_by'对象里
    cited_by_info = data.get('cited_by', {})

    articles_on_page = data.get('articles', [])
    if articles_on_page:
        all_articles.extend(articles_on_page)
    print(f"已获取第 {page_num + 1} 页的文章，共 {len(articles_on_page)} 篇。")

    # 2. 处理分页，循环获取所有出版物 (这部分逻辑不变)
    while "next" in data.get("serpapi_pagination", {}):
        page_num += 1
        print(f"正在获取第 {page_num + 1} 页的文章...")
        next_page_url = data["serpapi_pagination"]["next"]
        response = requests.get(next_page_url, params={"api_key": api_key})
        if response.status_code != 200:
            print(f"错误：获取第 {page_num + 1} 页时请求失败，状态码: {response.status_code}")
            break
        data = response.json()
        articles_on_page = data.get('articles', [])
        if not articles_on_page:
            print("当前页没有文章，停止获取。")
            break
        all_articles.extend(articles_on_page)
        print(f"已获取第 {page_num + 1} 页的文章，共 {len(articles_on_page)} 篇。")

    print(f"\n所有出版物获取完毕，总共 {len(all_articles)} 篇。")

    # 3. 整合数据，并根据新的JSON结构更新解析方式
    # 我们从 cited_by_info['table'] 中提取数据
    citations_table = cited_by_info.get('table', [])

    # 安全地提取引用数、h-index等
    total_citations = citations_table[0]['citations']['all'] if len(citations_table) > 0 and 'citations' in \
                                                                citations_table[0] and 'all' in citations_table[0][
                                                                    'citations'] else 0
    h_index = citations_table[1]['h_index']['all'] if len(citations_table) > 1 and 'h_index' in citations_table[
        1] and 'all' in citations_table[1]['h_index'] else 0
    i10_index = citations_table[2]['i10_index']['all'] if len(citations_table) > 2 and 'i10_index' in citations_table[
        2] and 'all' in citations_table[2]['i10_index'] else 0

    final_data = {
        'name': author_info.get('name'),
        'affiliation': author_info.get('affiliations'),
        'interests': [i['title'] for i in author_info.get('interests', [])],
        'scholar_id': scholar_id,
        'citedby': total_citations,
        'hindex': h_index,
        'i10index': i10_index,
        'publications': {v['citation_id']: v for v in all_articles},
        'updated': str(datetime.now())
    }

    return final_data


# main() 函数保持不变，这里为了简洁省略，请保留您原来的main()函数即可
def main():
    """
    主函数：获取环境变量，调用API，并生成JSON文件。
    """
    scholar_id = os.getenv('GOOGLE_SCHOLAR_ID')
    api_key = os.getenv('SERPAPI_API_KEY')

    if not scholar_id or not api_key:
        print("错误：请确保在GitHub Secrets中设置了 GOOGLE_SCHOLAR_ID 和 SERPAPI_API_KEY")
        exit(1)

    author_data = fetch_all_scholar_data(scholar_id, api_key)

    if author_data:
        print("\n最终生成的作者数据结构：")
        print(json.dumps(author_data, indent=2, ensure_ascii=False))
        os.makedirs('results', exist_ok=True)
        with open('results/gs_data.json', 'w', encoding='utf-8') as outfile:
            json.dump(author_data, outfile, ensure_ascii=False, indent=4)
        print("\n已成功生成 results/gs_data.json")

        print(f"(((((((((((((((((((((((((()))))))){author_data.get('citedby', 0)}")
        shieldio_data = {
            "schemaVersion": 1,
            "label": "citations",
            "message": str(author_data.get('citedby', 0)),
            "color": "brightgreen"
        }
        with open('results/gs_data_shieldsio.json', 'w', encoding='utf-8') as outfile:
            json.dump(shieldio_data, outfile, ensure_ascii=False, indent=4)
        print("已成功生成 results/gs_data_shieldsio.json")


if __name__ == "__main__":
    main()
