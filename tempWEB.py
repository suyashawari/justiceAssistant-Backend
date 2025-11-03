# To install: pip install tavily-python
from tavily import TavilyClient
client = TavilyClient("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")
response = client.search(
    query="java spring boot "
)
print(response)