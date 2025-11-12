// assets/dashAgGridComponentFunctions.js
var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.DateTimeFilter = React.forwardRef((props, ref) => {
  const { model, onModelChange, colDef, getValue } = props;

  // Local state (model shape: { operator, from, to })
  let current = model || { operator: 'equals', from: '', to: '' };
  const [operator, setOperator] = React.useState(current.operator || 'equals');
  const [from, setFrom] = React.useState(current.from || '');
  const [to, setTo] = React.useState(current.to || '');

  // Helpers: parse input (datetime-local) as local Date; parse cell ISO robustly
  function parseInputToDate(s) {
    if (!s) return null;
    const m = s.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})$/);
    if (m) return new Date(m[1], m[2]-1, m[3], m[4], m[5], m[6]);
    const d = new Date(s);
    return isNaN(d) ? null : d;
  }
  function parseCellDate(s) {
    if (!s) return null;
    const d = new Date(s);
    if (!isNaN(d)) return d;
    const s2 = s.replace(/\.\d+/, ''); // strip fractional seconds
    const d2 = new Date(s2);
    return isNaN(d2) ? null : d2;
  }
  function toSeconds(d) { return Math.floor(d.getTime() / 1000); }

  // Expose AG Grid filter lifecycle methods
  React.useImperativeHandle(ref, () => ({
    isFilterActive: () => !!(from || to),
    doesFilterPass: (params) => {
      const cellVal = getValue ? getValue(params.node) : params.value;
      const cellDate = parseCellDate(cellVal);
      if (!cellDate) return false;
      const cellSec = toSeconds(cellDate);

      const fromDate = parseInputToDate(from);
      const toDate = parseInputToDate(to);
      const fromSec = fromDate ? toSeconds(fromDate) : null;
      const toSec = toDate ? toSeconds(toDate) : null;

      if (operator === 'equals') return fromSec !== null && cellSec === fromSec;
      if (operator === 'lessThan') return fromSec !== null && cellSec < fromSec;
      if (operator === 'greaterThan') return fromSec !== null && cellSec > fromSec;
      if (operator === 'inRange') return fromSec !== null && toSec !== null && cellSec >= fromSec && cellSec <= toSec;
      return false;
    },
    getModel: () => {
      if (!from && !to) return null;
      return { operator, from, to };
    },
    setModel: (m) => {
      const mm = m || { operator: 'equals', from: '', to: '' };
      setOperator(mm.operator || 'equals');
      setFrom(mm.from || '');
      setTo(mm.to || '');
    }
  }));

  // Notify grid when model changes
  function updateModel(newOperator, newFrom, newTo) {
    setOperator(newOperator); setFrom(newFrom); setTo(newTo);
    const model = (!newFrom && !newTo) ? null : { operator: newOperator, from: newFrom, to: newTo };
    onModelChange && onModelChange(model);
  }

  return React.createElement('div', { style: { padding: 8, minWidth: 260 } },
    React.createElement('select', {
      value: operator,
      onChange: e => updateModel(e.target.value, from, to),
      style: { marginRight: 8 }
    },
      React.createElement('option', { value: 'equals' }, 'Equals'),
      React.createElement('option', { value: 'lessThan' }, 'Before'),
      React.createElement('option', { value: 'greaterThan' }, 'After'),
      React.createElement('option', { value: 'inRange' }, 'In range')
    ),
    React.createElement('input', {
      type: 'datetime-local', step: 1, value: from,
      onChange: e => updateModel(operator, e.target.value, to),
      title: 'From (seconds precision)'
    }),
    React.createElement('input', {
      type: 'datetime-local', step: 1, value: to,
      onChange: e => updateModel(operator, from, e.target.value),
      style: { marginLeft: 8 },
      title: 'To (seconds precision)'
    })
  );
});
