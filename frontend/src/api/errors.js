export function formatApiError(error, fallback = 'Une erreur est survenue.') {
  const detail = error?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item;
        const path = Array.isArray(item?.loc) ? item.loc.filter((part) => part !== 'body').join('.') : '';
        return [path, item?.msg].filter(Boolean).join(': ') || JSON.stringify(item);
      })
      .join(' ');
  }
  if (typeof detail === 'object') return detail.message || JSON.stringify(detail);
  return String(detail);
}
