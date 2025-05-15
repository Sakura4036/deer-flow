import logging
import os
import time
from typing import List

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def get_text_by_lang(content: List[dict], lang=None, return_key="text"):
    """Get text by language, if lang is None, return the first text"""
    if not content:
        return ""
    if lang is None:
        lang = ["EN", "CN", "JP"]
    if not isinstance(lang, list):
        lang = [lang]
    for la in lang:
        for c in content:
            if c["lang"] == la:
                return c[return_key]
    return content[0][return_key]


def html_to_markdown(html_text: str, return_markdown: bool = False) -> str:
    """
    Convert HTML to Markdown
    """
    if not html_text:
        return ""
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_text, "html.parser")

    if return_markdown:
        # 将sup、sub标签转为相应的Markdown格式
        for sup in soup.find_all("sup"):
            sup.string = f"^{sup.text}^"
        for sub in soup.find_all("sub"):
            sub.string = f"~{sub.text}~"

        sep = "\n\n"
    else:
        sep = "\n"

    # 处理div标签中的内容
    lines = []
    for div in soup.find_all("div"):
        content = div.get_text(strip=True)
        lines.append(content)

    # 将处理后的内容连接成一个字符串并返回
    markdown_text = f"{sep}".join(lines)
    return markdown_text


class PatsnapAPIClient:
    api_key: str = os.environ.get("PATSNAP_API_KEY")
    api_secret: str = os.environ.get("PATSNAP_API_SECRET")
    _token: str = None
    _token_expire: int = None

    def __init__(self, api_key: str = None, api_secret: str = None) -> None:
        if api_key:
            self.api_key = api_key
        if api_secret:
            self.api_secret = api_secret

    def get_bearer_token(self) -> str:
        """Get bearer token"""
        if not self.api_key and not self.api_secret:
            raise Exception("PATSNAP_API_KEY and PATSNAP_API_SECRET are required, please set them in the environment variables or pass them as arguments.")

        url = "https://connect.zhihuiya.com/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = "grant type=client credentials"
        auth = (self.api_key, self.api_secret)

        response = requests.post(url, headers=headers, data=data, auth=auth)
        response.raise_for_status()
        response = response.json()
        if response["status"]:
            self._token = response["data"]["token"]
        else:
            raise Exception(f"get_bearer_token Error: {response}")
        # token expires in 25 minutes
        self._token_expire = time.time() + 1500

        return self._token

    @property
    def token(self):
        # Check if token doesn't exist or has expired
        if not self._token or (self._token_expire and self._token_expire < time.time()):
            return self.get_bearer_token()
        return self._token

    def patent_search(
            self,
            query: str,
            limit: int = 10,
            offset: int = 0,
            stemming: int = 0,
            sort: List[dict] = None,
            collapse_type: str = None,
            collapse_by: str = None,
            collapse_order: str = None,
    ) -> List[dict]:
        """
        get data from zhihuiya patent query api
        :param query: query string
        :param limit: num of data
        :param offset: offset of data
        :param stemming: 是否开启截词：开启截词，在保留原词的同时，并扩展其对应的单复数及时态
        :param sort: 字段排序, [{"field": "field_name", "order": "asc"}].
            field support: "PBDT_YEARMONTHDAY", "apply_date", "ISD","SCORE".
            order support: "asc", "desc"
        :param collapse_type: 选择专利去重条件, 如：ALL不去重、APNO按申请号去重、DOCDB按简单同族去重、INPADOC按inpadoc同族去重，以及EXTEND按patsnap同族去重，空值默认为ALL
        :param collapse_by: 选择专利去重的排序字段，如：APD按申请日排序、PBD按公开日排序、AUTHORITY按受理局排序，以及SCORE按照查询相关性排序
        :param collapse_order: 选择专利去重的排序顺序，如果collapse_type等于APNO，collapse_by等于APD或PBD，collapse_order的有效值应该为OLDEST或LATEST
        example:
            {
                "pn": "US11205304B2",
                "apdt": 20211108,
                "apno": "US17/521392",
                "pbdt": 20230815,
                "title": "Techniques for using multiple symbols to provide feedback for a sidelink transmission",
                "inventor": "ELSHAFIE, AHMED | YANG, WEI | HOSSEINI, SEYEDKIANOUSH",
                "patent_id": "718ead9c-4f3c-4674-8f5a-24e126827269",
                "current_assignee": "QUALCOMM INCORPORATED",
                "original_assignee": "QUALCOMM INCORPORATED"
            }
        """
        # P002: 专利检索
        api_url = "https://connect.zhihuiya.com/search/patent/query-search-patent/v2"

        params = {"apikey": self.api_key}
        payload = {
            "sort": sort,
            "limit": limit,
            "offset": offset,
            "stemming": stemming,
            "query_text": query,
            "collapse_type": collapse_type,
            "collapse_by": collapse_by,
            "collapse_order": collapse_order,
            "collapse_order_authority": ["CN", "US", "EP", "JP", "KR"],
        }

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}",
        }

        response = requests.request(
            "POST", api_url, params=params, json=payload, headers=headers
        )
        response.raise_for_status()

        data = response.json()
        if data["error_code"] != 0:
            logger.error(f"patent_search error_code: {data['error_code']}")
            raise Exception(data["error_msg"])
        data = data["data"]
        # total = data['total_search_result_count']
        data = data["results"]
        return data

    def get_patent_title_abstract(
            self, patent_id: str, patent_number: str = None, lang: str = "en"
    ) -> dict:
        """Get patent title and abstract."""
        if not patent_id and not patent_number:
            return None

        # P011: 简单著录项
        api_simple_bibliography_url = (
            "https://connect.zhihuiya.com/basic-patent-data/simple-bibliography"
        )

        params = {
            "patent_id": patent_id,
            "patent_number": patent_number,
            "apikey": self.api_key,
        }

        payload = None

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}",
        }

        response = requests.request(
            "GET",
            api_simple_bibliography_url,
            params=params,
            data=payload,
            headers=headers,
        )
        response.raise_for_status()

        response = response.json()
        if response["error_code"] != 0:
            logger.error(f"get_patent_title_abstract error_code: {response['error_code']}")
            raise Exception(response["error_msg"])
        data = {
            "patent_id": patent_id,
            "patent_number": patent_number,
            "patent_type": "",
            "title": "",
            "abstract": "",
        }
        try:
            d = response["data"][0]
            data = {
                "patent_id": d["patent_id"],
                "patent_number": d["pn"],
                "patent_type": d["bibliographic_data"]["patent_type"],
                "title": get_text_by_lang(
                    d["bibliographic_data"].get("invention_title"), lang=lang
                ),
                "abstract": get_text_by_lang(
                    d["bibliographic_data"].get("abstracts"), lang=lang
                ),
            }
        except Exception as e:
            logger.error(
                f"Error getting patent {patent_id} / {patent_number} title and abstract: {e}"
            )
            # raise e

        return data

    def get_patent_claims(
            self, patent_id: str, patent_number: str = None, lang: str = "en"
    ) -> dict:
        """Get patent claims."""
        if not patent_id and not patent_number:
            return None

        # P018: 权利说明书
        api_claim_url = "https://connect.zhihuiya.com/basic-patent-data/claim-data"

        params = {
            "patent_id": patent_id,
            "patent_number": patent_number,
            "replace_by_related": "0",
            "apikey": self.api_key,
        }

        payload = None

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}",
        }

        response = requests.request(
            "GET", api_claim_url, params=params, data=payload, headers=headers
        )
        response.raise_for_status()
        response = response.json()
        if response["error_code"] != 0:
            logger.error(f"get_patent_claims error_code: {response['error_code']}")
            raise Exception(response["error_msg"])

        data = {
            "patent_id": patent_id,
            "patent_number": patent_number,
            "claims": "",
            "claim_count": 0,
        }
        try:
            d = response["data"][0]
            data = {
                "patent_id": d["patent_id"],
                "patent_number": d["pn"],
                "claims": html_to_markdown(
                    get_text_by_lang(
                        d.get("claims"), lang=lang, return_key="claim_text"
                    )
                ),
                "claim_count": d["claim_count"],
            }
        except Exception as e:
            logger.error(
                f"Error getting patent {patent_id} / {patent_number} claims: {e}"
            )
            # raise e
        return data

    def get_patent_core_invention_points(
            self, patent_id: str, patent_number: str = None, lang: str = "en"
    ) -> dict:
        """Get patent core invention points."""
        if not patent_id and not patent_number:
            return None

        # AI31: 专利核心发明点
        api_core_invention_points_url = (
            "https://connect.zhihuiya.com/search/patent/patent-core-invention-points"
        )

        params = {"apikey": self.api_key}

        payload = {"patent_id": patent_id, "pn": patent_number, "lang": lang.lower()}

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}",
        }

        response = requests.request(
            "POST",
            api_core_invention_points_url,
            params=params,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        response = response.json()
        if response["error_code"] != 0:
            logger.error(f"get_patent_core_invention_points error_code: {response['error_code']}")
            raise Exception(response["error_msg"])

        data = {
            "patent_id": patent_id,
            "patent_number": patent_number,
            "core_invention_points": [],
            "enhancement_proposals": [],
        }
        try:
            d = response["data"][0]
            data = {
                "patent_id": d["patent_id"],
                "patent_number": d["pn"],
                "core_invention_points": d.get("core_invention_points", {}).get(
                    "sentence", []
                ),
                "enhancement_proposals": d.get("enhancement_proposals", {}).get(
                    "sentence", []
                ),
            }
        except Exception as e:
            logger.error(
                f"Error getting patent {patent_id} / {patent_number} core invention points: {e}"
            )
            # raise e
        return data

    def get_patent_legal_status(
            self, patent_id: str, patent_number: str = None
    ):
        """Get patent legal status."""
        if not patent_id and not patent_number:
            return None

        # P013: 法律状态
        api_legal_status_url = (
            "https://connect.zhihuiya.com/basic-patent-data/legal-status"
        )

        params = {
            "patent_id": patent_id,
            "patent_number": patent_number,
            "apikey": self.api_key,
        }

        payload = None

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}",
        }

        response = requests.request(
            "GET", api_legal_status_url, params=params, data=payload, headers=headers
        )
        response.raise_for_status()
        response = response.json()
        if response["error_code"] != 0:
            logger.error(f"get_patent_legal_status error_code: {response['error_code']}")
            raise Exception(response["error_msg"])

        data = {
            "patent_id": patent_id,
            "patent_number": patent_number,
            "event_status": [],
            "legal_status": [],
            "simple_legal_status": [],
        }
        try:
            d = response["data"][0]
            data = {
                "patent_id": d["patent_id"],
                "patent_number": d["pn"],
                "event_status": d.get("patent_legal", {}).get("event_status", []),
                "legal_status": d.get("patent_legal", {}).get("legal_status", []),
                "simple_legal_status": d.get("patent_legal", {}).get(
                    "simple_legal_status", []
                ),
            }
        except Exception as e:
            logger.error(
                f"Error getting patent {patent_id} / {patent_number} legal status: {e}"
            )
            # raise e
        return data

    def get_patent_content(
            self,
            patent_id: str,
            patent_number: str = None,
            lang: str = "en",
            title_abstract: bool = True,
            claims: bool = False,
            core_invention_points: bool = True,
            legal_status: bool = False,
    ):
        """Get patent content.

        Args:
            patent_id: str, patsnap patent id
            patent_number: str = None, patent number
            lang: str, language
            title_abstract: bool, get title and abstract
            claims: bool, get claims
            core_invention_points: bool, get core invention points
            legal_status: bool, get legal status
        """
        data = {}
        if title_abstract:
            data.update(self.get_patent_title_abstract(patent_id, patent_number, lang))
        if claims:
            data.update(self.get_patent_claims(patent_id, patent_number, lang))
        if core_invention_points:
            data.update(
                self.get_patent_core_invention_points(patent_id, patent_number, lang)
            )
        if legal_status:
            data.update(self.get_patent_legal_status(patent_id, patent_number))

        return data

    def similar_patent_search(
            self,
            patent_id: str,
            patent_number: str = None,
            limit: int = 10,
            offset: int = 0,
            relevancy: str = "50%",
            country=None,
    ) -> List[dict]:
        """Similar patent search."""
        params = {"apikey": self.api_key}

        # P007: 相似专利检索
        api_url = "https://connect.zhihuiya.com/search/patent/similar-search-patent/v2"

        payload = {
            "limit": limit,
            "apd_to": "*",
            "offset": offset,
            "pbd_to": "*",
            "country": country,
            "apd_from": "*",
            "pbd_from": "*",
            "patent_id": patent_id,
            "relevancy": relevancy,
            "patent_number": patent_number,
        }

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.token}",
        }

        response = requests.request(
            "POST", api_url, params=params, json=payload, headers=headers
        )
        response.raise_for_status()

        data = response.json()
        if data["error_code"] != 0:
            logger.error(f"similar_patent_search error_code: {data['error_code']}")
            raise Exception(data["error_msg"])
        data = data["data"]
        data = data["results"]
        return data
