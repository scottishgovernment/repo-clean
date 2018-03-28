from collections import namedtuple
import os
from datetime import date, timedelta

EARLIEST_RELEASE_DATE = date.today() - timedelta(days=90)
STALE_DATE = EARLIEST_RELEASE_DATE - timedelta(days=1)

Args = namedtuple('Args', ['dry_run', 'verbose'])
_args = None

my_servers = {}

nexus = None
products = None

required = [
    'JENKINS',
    'NEXUS',
    'NEXUS_USER',
    'NEXUS_PASSWORD',
]

for x in required:
    ok = True
    try:
        os.environ[x]
    except KeyError:
        print("Error: set %s" % x)
        ok = False
        os.environ[x] = ''

if not ok:
    print("\n*** Need to set environment variables ***")

print("\nServers:")
SERVERS = ['JENKINS', 'NEXUS']
for x in SERVERS:
    try:
        my_servers[x] = os.environ[x]
        print("%s : \t%s" % (x, my_servers[x]))
    except KeyError:
        print("WARNING: You must set '%s' as an Env Var (hint: use .env)" % x)


def get_my_servers():
    SERVERS = ['JENKINS', 'NEXUS']
    for x in SERVERS:
        try:
            my_servers[x] = os.environ[x]
        except KeyError:
            raise RuntimeError(
                "You must set '%s' as an Env Var (hint: use .env)" % x)

    print("\nServers:")
    for x in SERVERS:
        print("%s : \t%s" % (x, my_servers[x]))


def get_products():
    from product import Product
    products = [
        Product('gov-site'),
        Product('mygov-site'),
    ]
    return products


# eof
