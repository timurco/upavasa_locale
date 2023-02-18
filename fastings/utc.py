from datetime import datetime

def offset():
        d1 = datetime.now().replace(second=0, microsecond=0)
        d2 = datetime.utcnow().replace(second=0, microsecond=0)
        r = d1 - d2
        return r