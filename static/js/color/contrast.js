// Foreground selection for solid action colors. Independent of theme storage.
export function luminance(hex) {
  let value = String(hex || '').replace(/^#/, '');
  if (value.length === 3) value = [...value].map(c => c + c).join('');
  if (!/^[0-9a-f]{6}$/i.test(value)) return 0;
  const channel = n => { const x = n / 255; return x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; };
  return .2126 * channel(parseInt(value.slice(0, 2), 16))
    + .7152 * channel(parseInt(value.slice(2, 4), 16))
    + .0722 * channel(parseInt(value.slice(4, 6), 16));
}
export function actionForeground(background) {
  const base = luminance(background);
  const dark = (base + .05) / (luminance('#0D0F14') + .05);
  const light = 1.05 / (base + .05);
  if (dark >= light && dark >= 4.5) return '#0D0F14';
  return light >= 4.5 ? '#FFFFFF' : '#000000';
}
