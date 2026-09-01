// Beacon Atlas real-time updates for bounty #1524.
// Read-only client: the WebSocket only receives public-safe Atlas deltas.

const DEFAULT_BACKOFF = Object.freeze({ min: 1000, max: 30000, factor: 1.8 });
const ALLOWED_TYPES = new Set([
  'hello',
  'agent.new', 'agent.updated', 'agent.heartbeat', 'agent.removed',
  'contract.new', 'contract.updated', 'contract.removed',
]);

export function realtimeUrl(locationLike = window.location) {
  const wsScheme = locationLike.protocol === 'https:' ? 'wss:' : 'ws:';
  if (locationLike.hostname === 'localhost' || locationLike.hostname === '127.0.0.1') {
    return `${wsScheme}//${locationLike.hostname}:8071/beacon/ws`;
  }
  return `${wsScheme}//${locationLike.host}/beacon/ws`;
}

export function parseRealtimeEvent(raw) {
  let event;
  try {
    event = JSON.parse(raw);
  } catch (_) {
    return null;
  }
  if (!event || event.v !== 1 || typeof event.type !== 'string' || !ALLOWED_TYPES.has(event.type)) {
    return null;
  }
  if (!Number.isInteger(event.seq) || event.seq < 0 || typeof event.data !== 'object' || event.data === null) {
    return null;
  }
  return event;
}

export class BeaconRealtimeClient {
  constructor({ url = realtimeUrl(), onEvent = () => {}, onState = () => {}, WebSocketImpl = WebSocket } = {}) {
    this.url = url;
    this.onEvent = onEvent;
    this.onState = onState;
    this.WebSocketImpl = WebSocketImpl;
    this.socket = null;
    this.closedByUser = false;
    this.retryMs = DEFAULT_BACKOFF.min;
    this.retryTimer = null;
    this.lastSeq = -1;
  }

  connect() {
    this.closedByUser = false;
    this._open();
    return this;
  }

  close() {
    this.closedByUser = true;
    if (this.retryTimer) clearTimeout(this.retryTimer);
    this.retryTimer = null;
    if (this.socket) this.socket.close();
    this.socket = null;
    this.onState({ state: 'closed' });
  }

  _open() {
    if (this.closedByUser) return;
    this.onState({ state: 'connecting', url: this.url });
    const socket = new this.WebSocketImpl(this.url);
    this.socket = socket;

    socket.addEventListener('open', () => {
      this.retryMs = DEFAULT_BACKOFF.min;
      this.lastSeq = -1;
      this.onState({ state: 'open', url: this.url });
    });

    socket.addEventListener('message', ({ data }) => {
      const event = parseRealtimeEvent(data);
      if (!event) return;
      if (event.type !== 'hello' && event.seq <= this.lastSeq) return;
      if (event.type !== 'hello') this.lastSeq = event.seq;
      this.onEvent(event);
      window.dispatchEvent(new CustomEvent('beacon:realtime', { detail: event }));
    });

    socket.addEventListener('close', () => {
      if (this.socket === socket) this.socket = null;
      if (this.closedByUser) return;
      this.onState({ state: 'reconnecting', retryMs: this.retryMs });
      const delay = this.retryMs;
      this.retryMs = Math.min(DEFAULT_BACKOFF.max, Math.round(this.retryMs * DEFAULT_BACKOFF.factor));
      this.retryTimer = setTimeout(() => this._open(), delay);
    });

    socket.addEventListener('error', () => {
      this.onState({ state: 'error' });
    });
  }
}

export function startBeaconRealtime(options = {}) {
  return new BeaconRealtimeClient(options).connect();
}
