import assert from 'node:assert/strict';
import { actionForeground, luminance } from '../static/js/color/contrast.js';
for (const color of ['#FB2835', '#FF6611', '#FE8F15', '#FDCD61', '#8D071C', '#000', '#fff', '#777']) {
  const fg = luminance(actionForeground(color));
  const bg = luminance(color);
  assert.ok((Math.max(fg, bg) + .05) / (Math.min(fg, bg) + .05) >= 4.5, `${color} lacks readable action text`);
}
assert.equal(actionForeground('#8D071C'), '#FFFFFF');
assert.equal(actionForeground('#FB2835'), '#0D0F14');
console.log('PIGEON action contrast: all 8 palette and boundary cases passed');
