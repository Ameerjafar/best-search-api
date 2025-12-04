import httpx
import asyncio
import json
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()

query = 'market analysis solar panel'

async def fetch_searchapi(): 
    return await fetch_api('searchapi', 'https://www.searchapi.io/api/v1/search', 
                          {'engine': 'google', 'q': query, 'api_key': os.getenv('SEARCHAPI_KEY'), 'num': 10})

async def fetch_serpapi(): 
    return await fetch_api('serpapi', 'https://serpapi.com/search.json', 
                          {'engine': 'google', 'q': query, 'api_key': os.getenv('SERPAPI_KEY'), 'num': 10})

async def fetch_serper(): 
    return await fetch_api('serper', 'https://google.serper.dev/search', 
                          {'q': query}, headers={'X-API-KEY': os.getenv('SERPER_KEY')}, path='organic')

async def fetch_google_cse(): 
    return await fetch_api('google_cse', 'https://customsearch.googleapis.com/customsearch/v1', 
                          {'key': os.getenv('GOOGLE_CSE_KEY'), 'cx': os.getenv('GOOGLE_CSE_ID'), 'q': query, 'num': 10}, 
                          path='items')

async def fetch_scrapingdog(): 
    return await fetch_api('scrapingdog', 'https://api.scrapingdog.com/google', 
                          {'api_key': os.getenv('SCRAPINGDOG_KEY'), 'query': query, 'page': 1}, 
                          path='organic_results')

async def fetch_api(name, url, params=None, headers=None, path='organic_results'):
    if not params: params = {}
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, params=params, headers=headers)
            print(f"[{name}] Status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            results = data.get(path, [])[:3]  # ✅ Only first 3
            end = time.time()
            print(f"[{name}] Found {len(results)} results")
            return {
                'api': name,
                'time_ms': round((end - start) * 1000),
                'results_count': len(results),
                'results': results  # ✅ Only 3 results saved
            }
    except httpx.HTTPStatusError as e:
        print(f"❌ [{name}] HTTP {e.response.status_code}")
        return {'api': name, 'time_ms': 0, 'results_count': 0, 'error': f"HTTP {e.response.status_code}", 'results': []}
    except Exception as e:
        print(f"❌ [{name}] Error: {str(e)}")
        return {'api': name, 'time_ms': 0, 'results_count': 0, 'error': str(e), 'results': []}

async def compare_all_apis():
    print("🚀 Starting SERP API benchmark...")
    apis = [fetch_searchapi(), fetch_serpapi(), fetch_serper(), 
            fetch_google_cse(), fetch_scrapingdog()]
    
    results = await asyncio.gather(*apis, return_exceptions=True)
    
    output = {
        'query': query,
        'timestamp': datetime.now().isoformat(),
        'comparison': [r for r in results if not isinstance(r, Exception)]
    }
    
    filename = f"serp_comparison_top3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n📊 SERP API BENCHMARK (Top 3 sites):\n")
    print(f"{'API':<12} {'Time':<8} {'Sites':<6} {'Status'}")
    print("-" * 35)
    for r in results:
        if isinstance(r, Exception): continue
        status = "✅" if r['results_count'] > 0 else "❌"
        error = f"({r.get('error', '')})" if r.get('error') else ""
        print(f"{r['api']:<12} {r['time_ms']:<8}ms {r['results_count']:<6} {status} {error}")
    
    print(f"\n💾 Saved (Top 3 only): {filename}")
    return output

if __name__ == '__main__':
    asyncio.run(compare_all_apis())
