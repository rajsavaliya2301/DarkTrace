"""Check ES index mapping."""
import asyncio, json
from elasticsearch import AsyncElasticsearch

async def check():
    es = AsyncElasticsearch(['http://elasticsearch:9200'], basic_auth=('elastic', 'darktrace_es_pass'))
    mapping = await es.indices.get_mapping(index='crawled_content')
    props = mapping['crawled_content']['mappings']['properties']
    for field in ['document_type', 'source_type', 'language', 'site_name', 'scoring.severity']:
        if field in props:
            print(field + ': type=' + props[field].get("type", "?"))
        else:
            print(field + ': NOT FOUND')
    await es.close()
    
asyncio.run(check())
