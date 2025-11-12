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

//================

// assets/dashAgGridComponentFunctions.js
var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

dagcomponentfuncs.DateTimeFilter = React.forwardRef((props, ref) => {
  const { model, onModelChange, getValue, filterParams } = props;

  // Input state (what the user is editing)
  const initial = model || { operator: 'equals', from: '', to: '' };
  const [operator, setOperator] = React.useState(initial.operator || 'equals');
  const [from, setFrom] = React.useState(initial.from || '');
  const [to, setTo] = React.useState(initial.to || '');

  // Applied model (what the grid actually uses to filter)
  const [appliedModel, setAppliedModel] = React.useState(model || null);

  // Show apply button by default; allow override via colDef.filterParams.applyButton = false
  const showApply = filterParams && typeof filterParams.applyButton !== 'undefined'
    ? !!filterParams.applyButton
    : true;

  // --- Parsing helpers ---
  function parseInputToDate(s) {
    if (!s) return null;
    // Expecting datetime-local format: YYYY-MM-DDTHH:MM:SS
    const m = s.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})$/);
    if (m) return new Date(m[1], m[2] - 1, m[3], m[4], m[5], m[6]);
    const d = new Date(s);
    return isNaN(d) ? null : d;
  }

  function parseCellDate(v) {
    if (!v && v !== 0) return null;
    if (v instanceof Date) return isNaN(v.getTime()) ? null : v;
    if (typeof v === 'number') {
      const d = new Date(v);
      return isNaN(d) ? null : d;
    }
    // Try direct parse (handles ISO with timezone)
    let d = new Date(v);
    if (!isNaN(d)) return d;
    // Fallback: strip fractional seconds then parse
    const s2 = String(v).replace(/\.\d+/, '');
    d = new Date(s2);
    return isNaN(d) ? null : d;
  }

  function toSeconds(d) {
    return Math.floor(d.getTime() / 1000);
  }

  // Notify grid of a model change (used when applyButton is disabled or after Apply)
  function notifyModelChange(m) {
    setAppliedModel(m);
    if (onModelChange) onModelChange(m);
    if (props.filterChangedCallback) props.filterChangedCallback();
  }

  // When inputs change and apply button is disabled, auto-apply
  function onInputChange(newOperator, newFrom, newTo) {
    setOperator(newOperator);
    setFrom(newFrom);
    setTo(newTo);
    if (!showApply) {
      const modelToSend = (!newFrom && !newTo) ? null : { operator: newOperator, from: newFrom, to: newTo };
      notifyModelChange(modelToSend);
    }
  }

  // Apply / Reset handlers
  function apply() {
    const modelToApply = (!from && !to) ? null : { operator, from, to };
    notifyModelChange(modelToApply);
  }
  function reset() {
    setOperator('equals');
    setFrom('');
    setTo('');
    notifyModelChange(null);
  }

  // Expose AG Grid filter lifecycle methods
  React.useImperativeHandle(ref, () => ({
    isFilterActive: () => !!(appliedModel && (appliedModel.from || appliedModel.to)),
    doesFilterPass: (params) => {
      const cellVal = getValue ? getValue(params.node) : params.value;
      const cellDate = parseCellDate(cellVal);
      if (!cellDate) return false;
      const cellSec = toSeconds(cellDate);

      const op = appliedModel ? appliedModel.operator : null;
      const fromDate = appliedModel && appliedModel.from ? parseInputToDate(appliedModel.from) : null;
      const toDate = appliedModel && appliedModel.to ? parseInputToDate(appliedModel.to) : null;
      const fromSec = fromDate ? toSeconds(fromDate) : null;
      const toSec = toDate ? toSeconds(toDate) : null;

      if (!op) return true; // no filter applied

      switch (op) {
        case 'equals':
          return fromSec !== null && cellSec === fromSec;
        case 'lessThan':
          return fromSec !== null && cellSec < fromSec;
        case 'greaterThan':
          return fromSec !== null && cellSec > fromSec;
        case 'inRange':
          return fromSec !== null && toSec !== null && cellSec >= fromSec && cellSec <= toSec;
        default:
          return false;
      }
    },
    getModel: () => appliedModel,
    setModel: (m) => {
      const mm = m || { operator: 'equals', from: '', to: '' };
      setOperator(mm.operator || 'equals');
      setFrom(mm.from || '');
      setTo(mm.to || '');
      setAppliedModel(m);
    }
  }));

  // UI
  return React.createElement('div', { style: { padding: 8, minWidth: 320, fontFamily: 'Arial, sans-serif' } },
    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 } },
      React.createElement('select', {
        value: operator,
        onChange: e => onInputChange(e.target.value, from, to),
        'aria-label': 'Operator'
      },
        React.createElement('option', { value: 'equals' }, 'Equals'),
        React.createElement('option', { value: 'lessThan' }, 'Before'),
        React.createElement('option', { value: 'greaterThan' }, 'After'),
        React.createElement('option', { value: 'inRange' }, 'In range')
      ),
      React.createElement('input', {
        type: 'datetime-local',
        step: 1,
        value: from,
        onChange: e => onInputChange(operator, e.target.value, to),
        title: 'From (seconds precision)',
        'aria-label': 'From'
      }),
      React.createElement('input', {
        type: 'datetime-local',
        step: 1,
        value: to,
        onChange: e => onInputChange(operator, from, e.target.value),
        title: 'To (seconds precision)',
        'aria-label': 'To'
      })
    ),
    React.createElement('div', null,
      showApply
        ? React.createElement(React.Fragment, null,
            React.createElement('button', { onClick: apply, style: { marginRight: 8 } }, 'Apply'),
            React.createElement('button', { onClick: reset }, 'Reset')
          )
        : React.createElement('button', { onClick: reset }, 'Clear')
    )
  );
});
