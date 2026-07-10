"""Check ES index mapping for all fields."""
import asyncio, json
from elasticsearch import AsyncElasticsearch

async def check():
    es = AsyncElasticsearch(['http://elasticsearch:9200'], basic_auth=('elastic', 'darktrace_es_pass'))
    mapping = await es.indices.get_mapping(index='crawled_content')
    props = mapping['crawled_content']['mappings']['properties']
    for field in ['document_type', 'source_type', 'language', 'site_name']:
        val = props.get(field, {})
        print(field + ': type=' + val.get("type", "MISSING"))
    # Check scoring
    scoring = props.get('scoring', {})
    print('scoring: type=' + scoring.get('type', '') + ' enabled=' + str(scoring.get('enabled', True)))
    if 'properties' in scoring:
        for sub, cfg in scoring['properties'].items():
            print('  scoring.' + sub + ': type=' + cfg.get('type', '?'))
    await es.close()
    
asyncio.run(check())
