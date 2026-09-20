// DNS shim for Node in this sandbox: system getaddrinfo is broken, but direct
// UDP DNS queries to public resolvers work. Patch dns.lookup (used by net/tls)
// to resolve via dns.Resolver with explicit servers.
const dns = require('node:dns');

const resolver = new dns.Resolver({ timeout: 10, tries: 3 });
resolver.setServers(['8.8.8.8', '1.1.1.1']);

const cache = new Map();

const originalLookup = dns.lookup;

async function patchedLookup(hostname, options, callback) {
  // Normalize args (supports (hostname, callback) and (hostname, options, cb)).
  if (typeof options === 'function') {
    callback = options;
    options = {};
  }
  const family = options && options.family;
  try {
    if (!hostname || /^[0-9.]+$/.test(hostname) || hostname === 'localhost') {
      return originalLookup(hostname, options, callback);
    }
    if (family === 6) {
      const err = new Error(`no IPv6 for ${hostname}`);
      err.code = 'ENOTFOUND';
      return callback(err);
    }
    let addresses = cache.get(hostname);
    if (!addresses) {
      addresses = await new Promise((resolve, reject) => {
        resolver.resolve4(hostname, (err, res) => (err ? reject(err) : resolve(res)));
      });
      cache.set(hostname, addresses);
    }
    const ip = addresses[0];
    if (options && options.all) {
      return callback(null, addresses.map((a) => ({ address: a, family: 4 })));
    }
    return callback(null, ip, 4);
  } catch (err) {
    err.code = err.code || 'ENOTFOUND';
    return callback(err);
  }
}

Object.assign(patchedLookup, originalLookup);
dns.lookup = patchedLookup;
dns.promises && (dns.promises.lookup = require('node:util').promisify(patchedLookup));
