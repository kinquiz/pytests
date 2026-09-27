# ipaddress module
import ipaddress
from ipaddress import IPv4Network, IPv6Network

Network = IPv4Network | IPv6Network


def parse_networks(raw: str) -> list[Network]:
    # bare IP -> /32 or /128
    networks = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        # allow host bits, e.g. 10.0.0.5/8
        networks.append(ipaddress.ip_network(part, strict=False))
    return networks


def is_allowed(ip: str, networks: list[Network]) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    # version mismatch is just False
    return any(addr in net for net in networks)


if __name__ == "__main__":
    addr = ipaddress.ip_address("192.168.1.10")
    assert addr.version == 4
    assert addr.is_private
    assert not ipaddress.ip_address("8.8.8.8").is_private
    assert ipaddress.ip_address("127.0.0.1").is_loopback
    assert ipaddress.ip_address("::1").is_loopback

    net = ipaddress.ip_network("192.168.1.0/24")
    assert net.num_addresses == 256
    assert str(net.netmask) == "255.255.255.0"
    assert addr in net
    assert ipaddress.ip_address("192.168.2.1") not in net

    try:
        ipaddress.ip_network("192.168.1.5/24")
    except ValueError as e:
        print("strict:", e)
    assert ipaddress.ip_network("192.168.1.5/24", strict=False) == net

    nets = parse_networks("127.0.0.1, 10.0.0.0/8 , ,::1, 172.16.5.4/12")
    assert [str(n) for n in nets] == ["127.0.0.1/32", "10.0.0.0/8", "::1/128", "172.16.0.0/12"]

    assert is_allowed("127.0.0.1", nets)
    assert is_allowed("10.200.3.4", nets)
    assert is_allowed("172.31.255.255", nets)
    assert is_allowed("::1", nets)
    assert not is_allowed("172.32.0.1", nets)
    assert not is_allowed("8.8.8.8", nets)
    assert not is_allowed("not an ip", nets)
    assert not is_allowed("", nets)
    assert not is_allowed("127.0.0.1", [])  # fail closed

    try:
        parse_networks("10.0.0.0/33")
    except ValueError as e:
        print("bad network:", e)

    # numeric, not string order
    ips = sorted(ipaddress.ip_address(x) for x in ["10.0.0.10", "10.0.0.9", "10.0.0.100"])
    assert [str(i) for i in ips] == ["10.0.0.9", "10.0.0.10", "10.0.0.100"]

    hosts = list(ipaddress.ip_network("10.0.0.0/30").hosts())
    assert [str(h) for h in hosts] == ["10.0.0.1", "10.0.0.2"]

    print("ipaddress ok")
