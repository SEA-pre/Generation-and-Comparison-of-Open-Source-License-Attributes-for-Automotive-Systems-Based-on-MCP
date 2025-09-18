#!/usr/bin/env python3
# mcp_service.py
"""
MCP 中间件示例（FastAPI）
功能：
- 接收来自 SCA 的扫描结果（组件 + license）
- 调用 DeepSeek LLM：
    1) 检索原文（原文检索提示词）
    2) 根据原文抽取属性（属性分析提示词）
- 将结果返回给 SCA（或扫描触发者）
注意：DeepSeek 与 SCA 的真实 endpoint/credential 需要在运行前配置
"""
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

# ========== 配置部分 ==========
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/*****************")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "**************")
SCA_API_URL = os.getenv("SCA_API_URL", "******************")  # SCA接口


# ========== 数据模型 ==========
class LicenseRequest(BaseModel):
    component: str
    license: str
    missing_attributes: list  # SCA传来的缺失属性


# ========== 调用 DeepSeek ==========
async def query_deepseek(messages: list):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.3
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ========== MCP 主处理 ==========
@app.post("/mcp/process")
async def process_license(req: LicenseRequest):
    # Step 1: 检索许可证原文
    raw_license = await query_deepseek([
        {
            "role": "system",
            "content": "你是一名开源许可证助手，负责从外部知识库检索开源许可证原文。"
        },
        {
            "role": "user",
            "content": f"""
任务：根据输入的许可证名称：

输入许可证：{req.license}

要求：
- 如果检索到多个版本，返回最新稳定版本的全文。
- 直接返回许可证完整原文，不要附加解释。
- 如果无法检索到，请说明“未找到原文”。
"""
        }
    ])

    # Step 2: 提取许可证属性
    attributes_json = await query_deepseek([
        {
            "role": "system",
            "content": "你是一名开源许可证解析专家，负责将许可证原文转换为结构化属性。"
        },
        {
            "role": "user",
            "content": f"""
任务：根据以下许可证原文，提取三个维度的结构化属性：
1. 允许的 (permissions)：许可证赋予用户的权力（例如：Distribute, Modify, Commercial Use）。
2. 必要的 (conditions)：用户在行使权力时必须遵守的条件（例如：Include Copyright, Include License, State Changes）。
3. 限制的 (limitations)：许可证中声明的免责条款或使用限制（例如：Hold Liable, Use Trademark）。

许可证原文：
{raw_license}

输出要求：
- 必须使用 JSON 格式。
- JSON 字段为：permissions, conditions, limitations。
- 每个字段对应一个字符串数组。
- 不要包含额外的解释或文本。
"""
        }
    ])

    # Step 3: 构造结果 JSON
    result = {
        "component": req.component,
        "license": req.license,
        "license_text": raw_license,
        "attributes": attributes_json
    }

    # Step 4: 可选 - 将结果回传给 SCA 工具
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(SCA_API_URL, json=result)
    except Exception as e:
        print(f"[WARN] 无法回传至SCA工具: {e}")

    return result
