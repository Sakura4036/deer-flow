# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import logging
from typing import Annotated

from langchain_core.tools import tool
from .decorators import log_io

from src.crawler import Crawler

logger = logging.getLogger(__name__)


@tool
@log_io
def crawl_tool(
        url: Annotated[str, "The url to crawl."],
        max_length: Annotated[int, "The maximum length of the content."] = 1000,
) -> str:
    """Use this to crawl an url and get a readable content in Markdown format."""
    try:
        crawler = Crawler()
        article = crawler.crawl(url).to_markdown()
        content = "URL: " + url + "\n\n" + article[:max_length] if len(article) > max_length else article
        return content
    except BaseException as e:
        error_msg = f"Failed to crawl. Error: {repr(e)}"
        logger.error(error_msg)
        return error_msg
