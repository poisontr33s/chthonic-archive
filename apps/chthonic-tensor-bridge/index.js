'use strict';

const path = require('path');
const fs = require('fs');

function tryLoad(...candidates) {
  for (const p of candidates) {
    if (p && fs.existsSync(p)) {
      try {
        return require(p);
      } catch (e) {
        if (e.code !== 'MODULE_NOT_FOUND') throw e;
      }
    }
  }
  return null;
}

const root = __dirname;
const addon = tryLoad(
  path.join(root, 'build', 'Release', 'chthonic_tensor_bridge.node'),
  path.join(root, 'build', 'Debug', 'chthonic_tensor_bridge.node'),
  path.join(root, 'prebuilds', `${process.platform}-${process.arch}`, 'chthonic_tensor_bridge.node'),
);

if (!addon) {
  throw new Error(
    'chthonic-tensor-bridge native addon not built. Run `npm run build` from ' +
    'apps/chthonic-tensor-bridge (or `npm run build:electron` for VS Code).',
  );
}

module.exports = addon;
