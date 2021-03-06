import scrapy.utils.request
from OpenSSL import SSL
from scrapy.core.downloader.contextfactory import ScrapyClientContextFactory


# patching scrappy to avoid canonalizing urls in the reactor
def request_fingerprint_non_canonicalize(request, include_headers=None):
    if include_headers:
        include_headers = tuple([h.lower() for h in sorted(include_headers)])
    cache = scrapy.utils.request._fingerprint_cache.setdefault(request, {})
    if include_headers not in cache:
        fp = scrapy.utils.request.hashlib.sha1()
        fp.update(request.method.encode('utf-8'))
        fp.update(request.url.encode('utf-8'))
        fp.update(request.body or ''.encode('utf-8'))
        if include_headers:
            for hdr in include_headers:
                if hdr in request.headers:
                    fp.update(hdr)
                    for v in request.headers.getlist(hdr):
                        fp.update(v)
        cache[include_headers] = fp.hexdigest()
    return cache[include_headers]


scrapy.utils.request.request_fingerprint = request_fingerprint_non_canonicalize


# following https://github.com/scrapy/scrapy/issues/1429#issuecomment-131782133
# this seems to be the best option to avoid SSLv3 issues
class CustomContextFactory(ScrapyClientContextFactory):
    """
    Custom context factory that allows SSL negotiation.
    """

    def __init__(self):
        # Use SSLv23_METHOD so we can use protocol negotiation
        self.method = SSL.SSLv23_METHOD
