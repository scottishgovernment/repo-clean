import os

my_servers = {}

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
if not ok:
    print("\n*** Need to set environment variables ***")
    exit(-1)


def get_my_servers():
    SERVERS = ['JENKINS', 'NEXUS']
    for x in SERVERS:
        try:
            my_servers[x] = os.environ[x]
        except KeyError:
            raise RuntimeError(
                "You must set '%s' as an Env Var (hint: use .env)" % x)

    print("\nSERVERS:")
    for x in SERVERS:
        print("%s : \t%s" % (x, my_servers[x]))


# eof
