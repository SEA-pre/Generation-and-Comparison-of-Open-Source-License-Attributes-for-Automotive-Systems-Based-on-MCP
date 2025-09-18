# Generation-and-Comparison-of-Open-Source-License-Attributes-for-Automotive-Systems-Based-on-MCP
base on LLM（deepseek、hunyuan, better to chatgpt\grok\claude）、tldrlegal、choosealicense and SCA

启动服务：
pip install fastapi uvicorn requests pydantic
python3 mcp_service.py
# 或使用 uvicorn 直接
uvicorn mcp_service:app --host 0.0.0.0 --port 8000

请求json示例：
{
  "product_id": "vehicle-fw-001",
  "scan_id": "scan-20250901-0001",
  "components": [
    {"component_name": "busybox", "license_id": "GPL-2.0"},
    {"component_name": "my-embedded-crypto", "license_id": "UNKNOWN-LICENSE-XYZ", "license_text_snippet": "This software is licensed under the terms of..."}
  ]
}

License
Papers (papers/): Licensed under CC BY 4.0.
Data (data/): Licensed under CC0 1.0.
Code (code/): Licensed under MIT License
