from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import time
from ddgs import DDGS
from agent.models import SearchResult


def _fetch(query: str, max_results: int, timeout: int) -> list[dict]:
    with DDGS(timeout=timeout) as ddgs:
        return list(ddgs.text(query, max_results=max_results))


def search(
    query: str,
    max_results: int = 5,
    retries: int = 1,
    timeout: int = 6,
) -> list[SearchResult]:
    """失敗時返回空列表並記錄日誌，絕不拋異常給上層。"""
    for attempt in range(retries + 1):
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(_fetch, query, max_results, timeout)
            raw = future.result(timeout=timeout)
            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                    query=query,
                    round=0,
                )
                for r in raw
            ]
        except FuturesTimeoutError:
            print(f"[search] query={query!r} timed out after {timeout}s (attempt {attempt + 1}/{retries + 1})")
        except Exception as e:
            if "No results found" in str(e) or attempt == retries:
                print(f"[search] query={query!r} failed: {e}")
                return []
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        if attempt < retries:
            time.sleep(1.5)

    return []