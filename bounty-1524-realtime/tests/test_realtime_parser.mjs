import fs from 'node:fs';

const source = fs.readFileSync(new URL('../site/beacon/realtime.js', import.meta.url), 'utf8');

if (!source.includes("'agent.heartbeat'") || !source.includes("'contract.updated'")) {
  throw new Error('expected event types missing');
}
if (!source.includes('event.seq <= this.lastSeq')) {
  throw new Error('out-of-order event guard missing');
}
if (!source.includes("wss:")) {
  throw new Error('secure WebSocket upgrade missing');
}

console.log('realtime.js static contract checks passed');
