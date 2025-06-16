import asyncio
from typing import Annotated, TypedDict, List
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langchain_core.tools import tool

from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages

from pathlib import Path
from typing import Any, Dict
import logging
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage
from tenacity import retry, stop_after_attempt

class NoToolCallsError(Exception):
    """Raised when a response is expected to contain tool calls but doesn't"""
    pass


@retry(stop=stop_after_attempt(3))
async def ainvoke_llm_with_retry(llm:ChatOpenAI, llm_input, must_used_tool:bool=False, **kwargs):
    response = await llm.ainvoke(llm_input, **kwargs)
    if not must_used_tool:
        return response
    messages = response.get("messages")
    for msg in messages:
        if isinstance(msg, ToolMessage):
            return response
    raise NoToolCallsError("LLM response does not contain required tool calls")

# 创建加法工具
# Create addition tool
@tool
def add_numbers(a: int, b: int) -> int:
    """将两个数字相加。
    
    Args:
        a: 第一个数字
        b: 第二个数字
        
    Returns:
        两个数字的和
    """
    return a + b

# 创建删除工具
# Create deletion tool
@tool
def delete_number(numbers: List[int], index: int) -> List[int]:
    """从列表中删除指定位置的数字。
    
    Args:
        numbers: 数字列表
        index: 要删除数字的索引位置
        
    Returns:
        删除后的数字列表
    """
    if 0 <= index < len(numbers):
        return numbers[:index] + numbers[index+1:]
    else:
        return numbers

# 初始化工具列表
# Initialize list of tools
tools = [add_numbers, delete_number]

async def main(query:str):
    # Initialize the model
    model = ChatOpenAI(base_url="https://ark.cn-beijing.volces.com/api/v3", 
                       model="deepseek-r1-250528", 
                       api_key="0d093166-7f8f-4ac2-b3e5-f38091ebd9d1",
                    )
    agent = create_react_agent(name="add",
                               model=model,
                               tools=tools)
    result = await ainvoke_llm_with_retry(agent, {
        "messages": [   
            {
                "role":"system",
                "content": "You are a helpful math assistant, use tools for math calc."
            },
            {
                "role": "user", 
                "content": query
            }
        ],
    })
    
    print("运行结果 (Result):", result)
    

if __name__ == "__main__":
    asyncio.run(main("我需要计算5加3然后减去2。"))
