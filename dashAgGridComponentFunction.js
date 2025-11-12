// assets/dashAgGridComponentFunctions.js
window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

window.dashAgGridComponentFunctions.DateTimeFilter = function DateTimeFilter() {
  let params;
  let eGui;
  let selectOp, inputFrom, inputTo, btnApply, btnReset;
  let localModel = { operator: 'equals', from: '', to: '' };
  let appliedModel = null;

  const showApplyButton = () => {
    return params && params.filterParams && typeof params.filterParams.applyButton !== 'undefined'
      ? !!params.filterParams.applyButton
      : true;
  };

  function parseInputToDate(s) {
    if (!s) return null;
    const m = s.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})$/);
    if (m) return new Date(m[1], m[2] - 1, m[3], m[4], m[5], m[6]);
    const d = new Date(s);
    return isNaN(d) ? null : d;
  }

  function parseCellDate(v) {
    if (v == null) return null;
    if (v instanceof Date) return isNaN(v.getTime()) ? null : v;
    if (typeof v === 'number') {
      const d = new Date(v);
      return isNaN(d) ? null : d;
    }
    let d = new Date(v);
    if (!isNaN(d)) return d;
    const s2 = String(v).replace(/\.\d+/, '');
    d = new Date(s2);
    return isNaN(d) ? null : d;
  }

  function toSeconds(d) { return Math.floor(d.getTime() / 1000); }

  function applyModel(m) {
    appliedModel = m;
    if (params && typeof params.filterChangedCallback === 'function') {
      params.filterChangedCallback();
    }
  }

  function onInputChange() {
    localModel.operator = selectOp.value;
    localModel.from = inputFrom.value;
    localModel.to = inputTo.value;
    if (!showApplyButton()) {
      const m = (!localModel.from && !localModel.to) ? null : { ...localModel };
      applyModel(m);
    }
  }

  function onApplyClick() {
    const m = (!localModel.from && !localModel.to) ? null : { ...localModel };
    applyModel(m);
  }

  function onResetClick() {
    localModel = { operator: 'equals', from: '', to: '' };
    if (selectOp) selectOp.value = localModel.operator;
    if (inputFrom) inputFrom.value = '';
    if (inputTo) inputTo.value = '';
    applyModel(null);
  }

  function createGui() {
    eGui = document.createElement('div');
    eGui.style.padding = '8px';
    eGui.style.minWidth = '320px';
    eGui.style.fontFamily = 'Arial, sans-serif';

    const row = document.createElement('div');
    row.style.display = 'flex';
    row.style.alignItems = 'center';
    row.style.gap = '8px';
    row.style.marginBottom = '8px';

    selectOp = document.createElement('select');
    [
      { v: 'equals', t: 'Equals' },
      { v: 'lessThan', t: 'Before' },
      { v: 'greaterThan', t: 'After' },
      { v: 'inRange', t: 'In range' }
    ].forEach(o => {
      const opt = document.createElement('option');
      opt.value = o.v;
      opt.text = o.t;
      selectOp.appendChild(opt);
    });
    selectOp.value = localModel.operator;
    selectOp.addEventListener('change', onInputChange);

    inputFrom = document.createElement('input');
    inputFrom.type = 'datetime-local';
    inputFrom.step = '1';
    inputFrom.value = localModel.from;
    inputFrom.title = 'From (seconds precision)';
    inputFrom.addEventListener('input', onInputChange);

    inputTo = document.createElement('input');
    inputTo.type = 'datetime-local';
    inputTo.step = '1';
    inputTo.value = localModel.to;
    inputTo.title = 'To (seconds precision)';
    inputTo.addEventListener('input', onInputChange);

    row.appendChild(selectOp);
    row.appendChild(inputFrom);
    row.appendChild(inputTo);
    eGui.appendChild(row);

    const actions = document.createElement('div');
    if (showApplyButton()) {
      btnApply = document.createElement('button');
      btnApply.type = 'button';
      btnApply.textContent = 'Apply';
      btnApply.style.marginRight = '8px';
      btnApply.addEventListener('click', onApplyClick);

      btnReset = document.createElement('button');
      btnReset.type = 'button';
      btnReset.textContent = 'Reset';
      btnReset.addEventListener('click', onResetClick);

      actions.appendChild(btnApply);
      actions.appendChild(btnReset);
    } else {
      btnReset = document.createElement('button');
      btnReset.type = 'button';
      btnReset.textContent = 'Clear';
      btnReset.addEventListener('click', onResetClick);
      actions.appendChild(btnReset);
    }
    eGui.appendChild(actions);
  }

  return {
    init(p) {
      params = p;
      const m = params && params.model ? params.model : null;
      localModel = m ? { operator: m.operator || 'equals', from: m.from || '', to: m.to || '' } : { operator: 'equals', from: '', to: '' };
      appliedModel = m;
      createGui();
    },

    getGui() { return eGui; },

    isFilterActive() { return !!(appliedModel && (appliedModel.from || appliedModel.to)); },

    doesFilterPass(filterParams) {
      // filterParams typically contains value, node, data
      const cellVal = (typeof filterParams.value !== 'undefined') ? filterParams.value
        : (filterParams.data && params && params.colDef && params.colDef.field ? filterParams.data[params.colDef.field] : undefined);

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

    getModel() { return appliedModel; },

    setModel(m) {
      appliedModel = m;
      localModel = m ? { operator: m.operator || 'equals', from: m.from || '', to: m.to || '' } : { operator: 'equals', from: '', to: '' };
      if (selectOp) selectOp.value = localModel.operator;
      if (inputFrom) inputFrom.value = localModel.from;
      if (inputTo) inputTo.value = localModel.to;
    },

    destroy() {
      if (selectOp) selectOp.removeEventListener('change', onInputChange);
      if (inputFrom) inputFrom.removeEventListener('input', onInputChange);
      if (inputTo) inputTo.removeEventListener('input', onInputChange);
      if (btnApply) btnApply.removeEventListener('click', onApplyClick);
      if (btnReset) btnReset.removeEventListener('click', onResetClick);
      eGui = null;
      params = null;
    }
  };
};
