// assets/dashAgGridComponentFunctions.js
window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

window.dashAgGridComponentFunctions.DateTimeFilter = function DateTimeFilter(props) {
  const { model, onModelChange, filterParams, getValue, getHandler, onUiChange } = props;
  const initial = model || { operator: 'equals', from: '', to: '' };
  const [operator, setOperator] = React.useState(initial.operator);
  const [from, setFrom] = React.useState(initial.from || '');
  const [to, setTo] = React.useState(initial.to || '');
  const [appliedModel, setAppliedModel] = React.useState(model || null);
  const showApply = filterParams && typeof filterParams.applyButton !== 'undefined'
    ? !!filterParams.applyButton : true;

  // parsing helpers (ISO tolerant, strip fractional seconds)
  function parseInputToDate(s) {
    if (!s) return null;
    const m = s.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})$/);
    if (m) return new Date(m[1], m[2]-1, m[3], m[4], m[5], m[6]);
    const d = new Date(s); return isNaN(d) ? null : d;
  }
  function parseCellDate(v) {
    if (v == null) return null;
    if (v instanceof Date) return isNaN(v.getTime()) ? null : v;
    let d = new Date(v);
    if (!isNaN(d)) return d;
    d = new Date(String(v).replace(/\.\d+/, ''));
    return isNaN(d) ? null : d;
  }
  const toSeconds = d => Math.floor(d.getTime()/1000);

  // expose imperative handler to AG Grid (so grid can call doesFilterPass, getModel, setModel)
  React.useEffect(() => {
    if (typeof getHandler === 'function') {
      getHandler({
        isFilterActive: () => !!(appliedModel && (appliedModel.from || appliedModel.to)),
        doesFilterPass: (params) => {
          const cellVal = (typeof params.value !== 'undefined') ? params.value
            : (params.data && props.colDef && props.colDef.field ? params.data[props.colDef.field] : undefined);
          const cellDate = parseCellDate(cellVal);
          if (!cellDate) return false;
          const cellSec = toSeconds(cellDate);
          const op = appliedModel ? appliedModel.operator : null;
          const fromDate = appliedModel && appliedModel.from ? parseInputToDate(appliedModel.from) : null;
          const toDate = appliedModel && appliedModel.to ? parseInputToDate(appliedModel.to) : null;
          const fromSec = fromDate ? toSeconds(fromDate) : null;
          const toSec = toDate ? toSeconds(toDate) : null;
          if (!op) return true;
          switch (op) {
            case 'equals': return fromSec !== null && cellSec === fromSec;
            case 'lessThan': return fromSec !== null && cellSec < fromSec;
            case 'greaterThan': return fromSec !== null && cellSec > fromSec;
            case 'inRange': return fromSec !== null && toSec !== null && cellSec >= fromSec && cellSec <= toSec;
            default: return false;
          }
        },
        getModel: () => appliedModel,
        setModel: (m) => {
          setAppliedModel(m);
          const mm = m || { operator: 'equals', from: '', to: '' };
          setOperator(mm.operator || 'equals');
          setFrom(mm.from || '');
          setTo(mm.to || '');
        }
      });
    }
  }, [appliedModel, getHandler]);

  function apply() {
    const m = (!from && !to) ? null : { operator, from, to };
    setAppliedModel(m);
    if (typeof onModelChange === 'function') onModelChange(m);
  }
  function reset() {
    setOperator('equals'); setFrom(''); setTo('');
    setAppliedModel(null);
    if (typeof onModelChange === 'function') onModelChange(null);
  }

  // UI (React elements)
  return React.createElement('div', { style: { padding: 8, minWidth: 320, fontFamily: 'Arial, sans-serif' } },
    React.createElement('div', { style: { display: 'flex', gap: 8, marginBottom: 8 } },
      React.createElement('select', { value: operator, onChange: e => setOperator(e.target.value) },
        React.createElement('option', { value: 'equals' }, 'Equals'),
        React.createElement('option', { value: 'lessThan' }, 'Before'),
        React.createElement('option', { value: 'greaterThan' }, 'After'),
        React.createElement('option', { value: 'inRange' }, 'In range')
      ),
      React.createElement('input', { type: 'datetime-local', step: 1, value: from, onChange: e => setFrom(e.target.value) }),
      React.createElement('input', { type: 'datetime-local', step: 1, value: to, onChange: e => setTo(e.target.value) })
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
};
