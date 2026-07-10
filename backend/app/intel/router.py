"""Intel Router — REST API endpoints for external threat intelligence lookups.

Each service is exposed under its own sub-prefix:
  /v1/intel/virustotal/...
  /v1/intel/shodan/...
  /v1/intel/otx/...

All endpoints require authentication (JWT token).
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_current_user
from app.intel.otx import OTXClient, get_otx_client
from app.intel.shodan import ShodanClient, get_shodan_client
from app.intel.virustotal import VirusTotalClient, get_vt_client

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/intel",
    tags=["Intel"],
    dependencies=[Depends(get_current_user)],
)


# =====================================================================
#  VirusTotal Endpoints
# =====================================================================


@router.get("/virustotal/check-ip/{ip}", summary="VirusTotal IP lookup")
async def vt_check_ip(
    ip: str,
    client: VirusTotalClient = Depends(get_vt_client),
):
    """Look up an IP address in VirusTotal's threat database."""
    if not client.available:
        raise HTTPException(400, detail="VirusTotal API key not configured")
    result = await client.check_ip(ip)
    if result is None:
        raise HTTPException(502, detail="VirusTotal request failed")
    return _vt_response(result, "ip_address")


@router.get(
    "/virustotal/check-domain/{domain}",
    summary="VirusTotal domain lookup",
)
async def vt_check_domain(
    domain: str,
    client: VirusTotalClient = Depends(get_vt_client),
):
    """Look up a domain in VirusTotal's threat database."""
    if not client.available:
        raise HTTPException(400, detail="VirusTotal API key not configured")
    result = await client.check_domain(domain)
    if result is None:
        raise HTTPException(502, detail="VirusTotal request failed")
    return _vt_response(result, "domain")


@router.get(
    "/virustotal/check-hash/{file_hash}",
    summary="VirusTotal file-hash lookup",
)
async def vt_check_hash(
    file_hash: str,
    client: VirusTotalClient = Depends(get_vt_client),
):
    """Look up a file hash (MD5, SHA-1, SHA-256) in VirusTotal."""
    if not client.available:
        raise HTTPException(400, detail="VirusTotal API key not configured")
    result = await client.check_hash(file_hash)
    if result is None:
        raise HTTPException(502, detail="VirusTotal request failed")
    return _vt_response(result, "file")


@router.post(
    "/virustotal/submit-url",
    summary="Submit URL to VirusTotal for scanning",
)
async def vt_submit_url(
    url: str = Query(..., description="The URL to scan"),
    client: VirusTotalClient = Depends(get_vt_client),
):
    """Submit a URL to VirusTotal for scanning and return the analysis ID."""
    if not client.available:
        raise HTTPException(400, detail="VirusTotal API key not configured")
    result = await client.submit_url(url)
    if result is None:
        raise HTTPException(502, detail="VirusTotal submission failed")
    return {"data": result.get("data", {})}


@router.get(
    "/virustotal/analysis/{analysis_id}",
    summary="Get VirusTotal analysis result",
)
async def vt_get_analysis(
    analysis_id: str,
    client: VirusTotalClient = Depends(get_vt_client),
):
    """Retrieve the result of a previously submitted URL/file analysis."""
    if not client.available:
        raise HTTPException(400, detail="VirusTotal API key not configured")
    result = await client.get_analysis(analysis_id)
    if result is None:
        raise HTTPException(502, detail="VirusTotal request failed")
    return {"data": result.get("data", {})}


# =====================================================================
#  Shodan Endpoints
# =====================================================================


@router.get("/shodan/lookup-ip/{ip}", summary="Shodan IP lookup")
async def shodan_lookup_ip(
    ip: str,
    client: ShodanClient = Depends(get_shodan_client),
):
    """Return all known services and banners for an IP address.

    Includes open ports, service banners, vulnerabilities (CVEs),
    hostnames, and geographic data.
    """
    if not client.available:
        raise HTTPException(400, detail="Shodan API key not configured")
    result = await client.lookup_ip(ip)
    if result is None:
        raise HTTPException(502, detail="Shodan request failed")
    return {"data": result}


@router.get("/shodan/search", summary="Shodan device search")
async def shodan_search(
    query: str = Query(..., description="Shodan search query"),
    page: int = Query(1, ge=1, le=100),
    limit: int = Query(100, ge=1, le=100),
    client: ShodanClient = Depends(get_shodan_client),
):
    """Search Shodan's database of exposed internet-connected devices."""
    if not client.available:
        raise HTTPException(400, detail="Shodan API key not configured")
    result = await client.search(query, page=page, limit=limit)
    if result is None:
        raise HTTPException(502, detail="Shodan search failed")
    return {"data": result}


@router.get("/shodan/search-count", summary="Shodan result count")
async def shodan_search_count(
    query: str = Query(..., description="Shodan search query"),
    client: ShodanClient = Depends(get_shodan_client),
):
    """Return the number of matching devices for a Shodan search."""
    if not client.available:
        raise HTTPException(400, detail="Shodan API key not configured")
    count = await client.search_count(query)
    if count is None:
        raise HTTPException(502, detail="Shodan request failed")
    return {"query": query, "total": count}


@router.get("/shodan/api-info", summary="Shodan API plan info")
async def shodan_api_info(
    client: ShodanClient = Depends(get_shodan_client),
):
    """Return Shodan API plan information and remaining credits."""
    if not client.available:
        raise HTTPException(400, detail="Shodan API key not configured")
    result = await client.api_info()
    if result is None:
        raise HTTPException(502, detail="Shodan request failed")
    return {"data": result}


@router.get("/shodan/dns/resolve", summary="Shodan DNS resolution")
async def shodan_dns_resolve(
    hostname: str = Query(..., description="Hostname to resolve"),
    client: ShodanClient = Depends(get_shodan_client),
):
    """Resolve a hostname to an IP address via Shodan's DNS resolver."""
    if not client.available:
        raise HTTPException(400, detail="Shodan API key not configured")
    result = await client.resolve_dns(hostname)
    if result is None:
        raise HTTPException(502, detail="Shodan request failed")
    return {"data": result}


@router.get("/shodan/dns/reverse", summary="Shodan reverse DNS")
async def shodan_dns_reverse(
    ip: str = Query(..., description="IP address to reverse-lookup"),
    client: ShodanClient = Depends(get_shodan_client),
):
    """Reverse DNS lookup via Shodan."""
    if not client.available:
        raise HTTPException(400, detail="Shodan API key not configured")
    result = await client.reverse_dns(ip)
    if result is None:
        raise HTTPException(502, detail="Shodan request failed")
    return {"data": result}


# =====================================================================
#  AlienVault OTX Endpoints
# =====================================================================


@router.get("/otx/check-ip/{ip}", summary="OTX IP threat intelligence")
async def otx_check_ip(
    ip: str,
    client: OTXClient = Depends(get_otx_client),
):
    """Return AlienVault OTX threat intelligence for an IP address."""
    if not client.available:
        raise HTTPException(400, detail="OTX API key not configured")
    result = await client.check_ip(ip)
    if result is None:
        raise HTTPException(502, detail="OTX request failed")
    return {"data": result}


@router.get(
    "/otx/check-ip/{ip}/passive-dns",
    summary="OTX passive DNS for IP",
)
async def otx_ip_passive_dns(
    ip: str,
    client: OTXClient = Depends(get_otx_client),
):
    """Return passive DNS resolutions for an IP from OTX."""
    if not client.available:
        raise HTTPException(400, detail="OTX API key not configured")
    result = await client.check_ip_passive_dns(ip)
    if result is None:
        raise HTTPException(502, detail="OTX request failed")
    return {"data": result}


@router.get(
    "/otx/check-ip/{ip}/malware",
    summary="OTX malware samples for IP",
)
async def otx_ip_malware(
    ip: str,
    client: OTXClient = Depends(get_otx_client),
):
    """Return malware samples associated with an IP from OTX."""
    if not client.available:
        raise HTTPException(400, detail="OTX API key not configured")
    result = await client.check_ip_malware(ip)
    if result is None:
        raise HTTPException(502, detail="OTX request failed")
    return {"data": result}


@router.get(
    "/otx/check-ip/{ip}/urls",
    summary="OTX URLs associated with IP",
)
async def otx_ip_urls(
    ip: str,
    client: OTXClient = Depends(get_otx_client),
):
    """Return URLs associated with an IP address from OTX."""
    if not client.available:
        raise HTTPException(400, detail="OTX API key not configured")
    result = await client.check_ip_url_list(ip)
    if result is None:
        raise HTTPException(502, detail="OTX request failed")
    return {"data": result}


@router.get(
    "/otx/check-domain/{domain}",
    summary="OTX domain threat intelligence",
)
async def otx_check_domain(
    domain: str,
    client: OTXClient = Depends(get_otx_client),
):
    """Return AlienVault OTX threat intelligence for a domain."""
    if not client.available:
        raise HTTPException(400, detail="OTX API key not configured")
    result = await client.check_domain(domain)
    if result is None:
        raise HTTPException(502, detail="OTX request failed")
    return {"data": result}


@router.get(
    "/otx/check-domain/{domain}/passive-dns",
    summary="OTX passive DNS for domain",
)
async def otx_domain_passive_dns(
    domain: str,
    client: OTXClient = Depends(get_otx_client),
):
    """Return passive DNS data for a domain from OTX."""
    if not client.available:
        raise HTTPException(400, detail="OTX API key not configured")
    result = await client.check_domain_passive_dns(domain)
    if result is None:
        raise HTTPException(502, detail="OTX request failed")
    return {"data": result}


@router.get(
    "/otx/check-domain/{domain}/malware",
    summary="OTX malware for domain",
)
async def otx_domain_malware(
    domain: str,
    client: OTXClient = Depends(get_otx_client),
):
    """Return malware samples associated with a domain from OTX."""
    if not client.available:
        raise HTTPException(400, detail="OTX API key not configured")
    result = await client.check_domain_malware(domain)
    if result is None:
        raise HTTPException(502, detail="OTX request failed")
    return {"data": result}


@router.get(
    "/otx/check-domain/{domain}/urls",
    summary="OTX URLs for domain",
)
async def otx_domain_urls(
    domain: str,
    client: OTXClient = Depends(get_otx_client),
):
    """Return URLs associated with a domain from OTX."""
    if not client.available:
        raise HTTPException(400, detail="OTX API key not configured")
    result = await client.check_domain_url_list(domain)
    if result is None:
        raise HTTPException(502, detail="OTX request failed")
    return {"data": result}


@router.get(
    "/otx/check-hash/{file_hash}",
    summary="OTX file hash threat intelligence",
)
async def otx_check_hash(
    file_hash: str,
    client: OTXClient = Depends(get_otx_client),
):
    """Return OTX threat intelligence for a file hash (MD5/SHA-1/SHA-256)."""
    if not client.available:
        raise HTTPException(400, detail="OTX API key not configured")
    result = await client.check_hash(file_hash)
    if result is None:
        raise HTTPException(502, detail="OTX request failed")
    return {"data": result}


@router.get(
    "/otx/check-hash/{file_hash}/analysis",
    summary="OTX file hash analysis",
)
async def otx_hash_analysis(
    file_hash: str,
    client: OTXClient = Depends(get_otx_client),
):
    """Return analysis results for a file hash from OTX."""
    if not client.available:
        raise HTTPException(400, detail="OTX API key not configured")
    result = await client.check_hash_analysis(file_hash)
    if result is None:
        raise HTTPException(502, detail="OTX request failed")
    return {"data": result}


@router.get("/otx/pulses", summary="Recent OTX pulses")
async def otx_pulses(
    limit: int = Query(20, ge=1, le=50),
    page: int = Query(1, ge=1),
    client: OTXClient = Depends(get_otx_client),
):
    """Return recent OTX pulses (threat intelligence collections)."""
    if not client.available:
        raise HTTPException(400, detail="OTX API key not configured")
    result = await client.get_pulses(limit=limit, page=page)
    if result is None:
        raise HTTPException(502, detail="OTX request failed")
    return {"data": result}


# =====================================================================
#  Unified Enrichment Endpoint
# =====================================================================


@router.get(
    "/enrich/{entity_type}/{value}",
    summary="Unified enrichment across all intel sources",
)
async def enrich_entity(
    entity_type: str,
    value: str,
    vt: VirusTotalClient = Depends(get_vt_client),
    shodan: ShodanClient = Depends(get_shodan_client),
    otx: OTXClient = Depends(get_otx_client),
):
    """Query all configured threat-intel sources for a given entity.

    Supported entity types: ``ip``, ``domain``, ``hash``.

    Results are aggregated from every available source (VirusTotal,
    Shodan, OTX).  Sources without a configured API key are skipped.
    """
    if entity_type not in ("ip", "domain", "hash"):
        raise HTTPException(
            400, detail=f"Unsupported entity type: {entity_type}. Use ip, domain, or hash."
        )

    results: Dict[str, Any] = {"entity_type": entity_type, "value": value}

    # VirusTotal
    if vt.available:
        try:
            if entity_type == "ip":
                results["virustotal"] = await vt.check_ip(value)
            elif entity_type == "domain":
                results["virustotal"] = await vt.check_domain(value)
            else:
                results["virustotal"] = await vt.check_hash(value)
        except Exception as e:
            logger.warning("VirusTotal enrichment failed for %s: %s", value, e)
            results["virustotal"] = {"error": str(e)}

    # Shodan (IP only — most useful)
    if shodan.available and entity_type == "ip":
        try:
            results["shodan"] = await shodan.lookup_ip(value)
        except Exception as e:
            logger.warning("Shodan enrichment failed for %s: %s", value, e)
            results["shodan"] = {"error": str(e)}

    # OTX
    if otx.available:
        try:
            if entity_type == "ip":
                results["otx"] = await otx.check_ip(value)
            elif entity_type == "domain":
                results["otx"] = await otx.check_domain(value)
            else:
                results["otx"] = await otx.check_hash(value)
        except Exception as e:
            logger.warning("OTX enrichment failed for %s: %s", value, e)
            results["otx"] = {"error": str(e)}

    if len(results) == 2:  # only entity_type + value
        results["note"] = "No threat-intel sources are configured. Set VIRUSTOTAL_API_KEY, SHODAN_API_KEY, and/or OTX_API_KEY in .env"

    return results


# =====================================================================
#  Internal helpers
# =====================================================================


def _vt_response(
    raw: Dict[str, Any], indicator_type: str
) -> Dict[str, Any]:
    """Extract the relevant attributes from a VirusTotal response."""
    data = raw.get("data") or {}
    attrs = data.get("attributes", {}) if isinstance(data, dict) else {}
    stats = attrs.get("last_analysis_stats", {})

    # Summary
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    harmless = stats.get("harmless", 0)
    undetected = stats.get("undetected", 0)
    total = malicious + suspicious + harmless + undetected

    return {
        "indicator_type": indicator_type,
        "detections": {
            "malicious": malicious,
            "suspicious": suspicious,
            "harmless": harmless,
            "undetected": undetected,
            "total_engines": total,
        },
        "reputation": attrs.get("reputation"),
        "last_analysis_date": attrs.get("last_analysis_date"),
        "categories": attrs.get("categories", {}),
        "tags": attrs.get("tags", []),
        "raw": raw,
    }
