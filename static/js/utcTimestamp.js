// Application record timestamps are stored in UTC. Calendar event wall times
// have separate timezone semantics and must not use this helper.
export function utcTimestampDate(value) {
  const naive = typeof value === 'string'
    && /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?$/.test(value);
  return new Date(naive ? value.replace(' ', 'T') + 'Z' : value);
}
