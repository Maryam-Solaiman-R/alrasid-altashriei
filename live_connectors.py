from dataclasses import dataclass, asdict
from urllib.parse import urlparse


@dataclass(frozen=True)
class Connector:
    key: str
    authority: str
    roots: tuple[str, ...]
    priority: int = 1


# نطاق الوكيل مقصود ومحدود: مصدران رسميان فقط.
CONNECTORS = [
    Connector(
        "boe",
        "هيئة الخبراء بمجلس الوزراء",
        ("https://laws.boe.gov.sa/BoeLaws/Laws/Folders/1",),
        1,
    ),
    Connector(
        "ncar",
        "المركز الوطني للوثائق والمحفوظات",
        ("https://ncar.gov.sa/",),
        2,
    ),
]


def connector_for_url(url: str):
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    for connector in CONNECTORS:
        for root in connector.roots:
            root_host = (urlparse(root).hostname or "").lower().removeprefix("www.")
            if host == root_host or host.endswith("." + root_host):
                return connector
    return None


def public_connectors():
    return [asdict(x) for x in CONNECTORS]
