"""External Threat Intelligence Integrations.

Provides Python clients for VirusTotal, Shodan, and AlienVault OTX APIs
to enrich entities (IPs, domains, URLs, file hashes) with reputation data
from public threat intelligence feeds.

Each client gracefully degrades when the corresponding API key is missing.
"""

from app.intel.virustotal import VirusTotalClient
from app.intel.shodan import ShodanClient
from app.intel.otx import OTXClient

__all__ = [
    "VirusTotalClient",
    "ShodanClient",
    "OTXClient",
]
