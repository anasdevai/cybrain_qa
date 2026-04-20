/** Cybrain QS – shared utilities */

export function formatTime(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d)) return '';
  return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
}

export function formatSessionTime(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d)) return '';
  const now = new Date();
  const diffMs = now - d;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  if (diffDays === 1) return 'Gestern';
  const weekdays = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
  if (diffDays <= 7) return `${weekdays[d.getDay()]}, ${d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
  return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
}

export function getTagType(ref, fallbackType) {
  const type = (fallbackType || '').toLowerCase();
  if (type === 'sop' || ref?.startsWith('SOP-')) return 'sop';
  if (type === 'dev' || ref?.startsWith('DEV-')) return 'dev';
  if (type === 'capa' || ref?.startsWith('CAPA-')) return 'capa';
  if (type === 'ent' || ref?.startsWith('ENT-')) return 'ent';
  if (type === 'find' || ref?.startsWith('FIND-') || ref?.startsWith('A-')) return 'audit';
  return 'default';
}

export function getTagPrefix(type) {
  switch (type) {
    case 'sop': return '📄';
    case 'dev': return '⚠';
    case 'capa': return '◆';
    case 'audit': return '✓';
    case 'ent': return '✓';
    default: return '•';
  }
}

export function getSessionDotColor(session) {
  const t = (session?.title || '').toLowerCase();
  if (t.includes('dev') || t.includes('abweich') || t.includes('reinigung')) return '#c43d1b';
  if (t.includes('capa')) return '#d4933a';
  if (t.includes('audit') || t.includes('beanstand') || t.includes('entscheid')) return '#3c5dcb';
  return '#357856';
}

export function groupSessionsByDate(sessions) {
  const groups = { heute: [], gestern: [], dieseWoche: [], aelter: [] };
  const now = new Date();
  sessions.forEach(s => {
    const raw = s.updated_at || s.created_at;
    const d = raw ? new Date(raw) : null;
    if (!d || isNaN(d)) { groups.aelter.push(s); return; }
    const diffDays = Math.floor((now - d) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) groups.heute.push(s);
    else if (diffDays === 1) groups.gestern.push(s);
    else if (diffDays <= 7) groups.dieseWoche.push(s);
    else groups.aelter.push(s);
  });
  return groups;
}
