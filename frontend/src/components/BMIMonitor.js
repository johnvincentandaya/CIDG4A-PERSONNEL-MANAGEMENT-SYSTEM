import React, {useEffect, useState} from 'react';
import { api } from '../api';
import { RANKS } from '../constants/ranks';

function classificationClass(name){
  const key = (name || '').toLowerCase();
  if (key.includes('normal')) return 'badge-bmi badge-bmi--normal';
  if (key.includes('over')) return 'badge-bmi badge-bmi--overweight';
  if (key.includes('obese')) return 'badge-bmi badge-bmi--obese';
  if (key.includes('under')) return 'badge-bmi badge-bmi--underweight';
  return 'badge-bmi badge-bmi--normal';
}

export default function BMIMonitor(){
  const [records, setRecords] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({rank:'', name:'', unit:'RHQ', age:'', sex:'Male', height_cm:'', weight_kg:'', waist_cm:'', hip_cm:'', wrist_cm:'', date_taken: ''});
  const [front, setFront] = useState(null);
  const [left, setLeft] = useState(null);
  const [right, setRight] = useState(null);

  // filters
  const [unitFilter, setUnitFilter] = useState('All Units');
  const [monthFilter, setMonthFilter] = useState('All Months');
  const [yearFilter, setYearFilter] = useState('All Years');
  const [search, setSearch] = useState('');

  useEffect(()=>{ load(); },[])
  function load(){ api.get('/api/bmi/').then(r=>setRecords(r.data)).catch(()=>{}); }

  function openNew(){
    setForm({rank:'', name:'', unit:'RHQ', age:'', sex:'Male', height_cm:'', weight_kg:'', waist_cm:'', hip_cm:'', wrist_cm:'', date_taken: ''});
    setFront(null); setLeft(null); setRight(null);
    setShowModal(true);
  }

  function valid(){
    return form.rank && form.name && form.unit && form.age && form.height_cm && form.weight_kg && front && left && right;
  }

  async function submit(){
    if(!valid()) return alert('Please fill required fields and upload three photos');
    const data = new FormData();
    Object.keys(form).forEach(k=>{ if(form[k]) data.append(k, form[k]); });
    data.append('photo_front', front);
    data.append('photo_left', left);
    data.append('photo_right', right);
    try{
      await api.post('/api/bmi/', data, { headers: {'Content-Type':'multipart/form-data'} });
      setShowModal(false);
      load();
    }catch(err){
      alert('Error saving BMI record: '+ (err.response?.data?.detail || err.message));
    }
  }

  const monthOptions = [
    'All Months',
    'January','February','March','April','May','June',
    'July','August','September','October','November','December'
  ];

  const filteredRecords = records.filter(r => {
    let ok = true;
    if (unitFilter !== 'All Units') {
      ok = ok && r.unit === unitFilter;
    }
    if (r.date_taken && (monthFilter !== 'All Months' || yearFilter !== 'All Years')) {
      const d = new Date(r.date_taken);
      const monthName = monthOptions[d.getMonth() + 1];
      const yearVal = d.getFullYear().toString();
      if (monthFilter !== 'All Months') {
        ok = ok && monthName === monthFilter;
      }
      if (yearFilter !== 'All Years') {
        ok = ok && yearVal === yearFilter;
      }
    } else {
      if (monthFilter !== 'All Months' || yearFilter !== 'All Years') {
        ok = false;
      }
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      const haystack = [
        r.rank || '',
        r.name || '',
        r.unit || '',
      ].join(' ').toLowerCase();
      ok = ok && haystack.includes(q);
    }
    return ok;
  });

  return (
    <div>
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-eyebrow">Health Monitoring</div>
          <h1 className="page-title">BMI Monitoring</h1>
          <p className="page-subtitle">
            Monitor Body Mass Index records and compliance across CIDG RFU4A units for operational fitness.
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn-quiet">
            <i className="bi bi-heart-pulse" />
            Monthly BMI overview
          </button>
        </div>
      </div>

      <div className="card-section p-3">
        <div className="filter-bar">
          <div className="filter-controls">
            <select
              className="form-select form-select-sm"
              value={unitFilter}
              onChange={e => setUnitFilter(e.target.value)}
            >
              <option>All Units</option>
              <option>RHQ</option>
              <option>Cavite</option>
              <option>Laguna</option>
              <option>Batangas</option>
              <option>Rizal</option>
              <option>Quezon</option>
            </select>
            <select
              className="form-select form-select-sm"
              value={monthFilter}
              onChange={e => setMonthFilter(e.target.value)}
            >
              {monthOptions.map(m => (
                <option key={m}>{m}</option>
              ))}
            </select>
            <select
              className="form-select form-select-sm"
              value={yearFilter}
              onChange={e => setYearFilter(e.target.value)}
            >
              <option>All Years</option>
              {[...new Set(records
                .filter(r => r.date_taken)
                .map(r => new Date(r.date_taken).getFullYear().toString()))]
                .sort()
                .map(y => <option key={y}>{y}</option>)}
            </select>
            <input
              className="form-control form-control-sm"
              placeholder="Search by rank, name, or unit"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div>
            <button className="btn btn-outline-secondary btn-sm me-2">
              <i className="bi bi-file-earmark-text me-1" />
              Generate Report
            </button>
            <button className="btn btn-primary btn-sm" onClick={openNew}>
              <i className="bi bi-plus-lg me-1" />
              New Record
            </button>
          </div>
        </div>

        <div className="table-wrapper">
          <div style={{overflow:'auto'}}>
            <table className="table table-hover data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Name</th>
                  <th>Unit</th>
                  <th>Age</th>
                  <th>Height (cm)</th>
                  <th>Weight (kg)</th>
                  <th>BMI</th>
                  <th>Result</th>
                  <th>Classification</th>
                  <th>Date Taken</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.length === 0 && (
                  <tr>
                    <td colSpan={11}>
                      <div className="table-empty-state">
                        No BMI records captured yet. Add a new record to begin monitoring personnel BMI trends.
                      </div>
                    </td>
                  </tr>
                )}
                {filteredRecords.map(r=> (
                  <tr key={r.id}>
                    <td>{r.rank}</td>
                    <td>{r.name}</td>
                    <td>{r.unit}</td>
                    <td>{r.age}</td>
                    <td>{r.height_cm}</td>
                    <td>{r.weight_kg}</td>
                    <td>{r.bmi}</td>
                    <td>{r.result}</td>
                    <td>
                      <span className={classificationClass(r.classification)}>
                        {r.classification}
                      </span>
                    </td>
                    <td>{r.date_taken ? new Date(r.date_taken).toLocaleDateString(): ''}</td>
                    <td>
                      <button className="btn btn-sm btn-outline-primary">
                        <i className="bi bi-pencil-square" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showModal && (
        <div className="modal d-block" tabIndex={-1}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Add New BMI Record</h5>
                <button className="btn-close" onClick={()=>setShowModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="row g-2">
                  <div className="col-md-4">
                    <label>Rank *</label>
                    <select
                      className="form-select"
                      value={form.rank}
                      onChange={e=>setForm({...form,rank:e.target.value})}
                    >
                      <option value="">Select rank</option>
                      {RANKS.map(r => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-md-4"><label>Name *</label><input className="form-control" value={form.name} onChange={e=>setForm({...form,name:e.target.value})} /></div>
                  <div className="col-md-4"><label>Unit *</label><select className="form-select" value={form.unit} onChange={e=>setForm({...form,unit:e.target.value})}><option>RHQ</option><option>Cavite</option><option>Laguna</option><option>Batangas</option><option>Rizal</option><option>Quezon</option></select></div>
                  <div className="col-md-3"><label>Age *</label><input type="number" className="form-control" value={form.age} onChange={e=>setForm({...form,age:e.target.value})} /></div>
                  <div className="col-md-3"><label>Sex</label><select className="form-select" value={form.sex} onChange={e=>setForm({...form,sex:e.target.value})}><option>Male</option><option>Female</option></select></div>
                  <div className="col-md-3"><label>Height (cm) *</label><input type="number" className="form-control" value={form.height_cm} onChange={e=>setForm({...form,height_cm:e.target.value})} /></div>
                  <div className="col-md-3"><label>Weight (kg) *</label><input type="number" className="form-control" value={form.weight_kg} onChange={e=>setForm({...form,weight_kg:e.target.value})} /></div>
                  <div className="col-md-3"><label>Waist (cm)</label><input type="number" className="form-control" value={form.waist_cm} onChange={e=>setForm({...form,waist_cm:e.target.value})} /></div>
                  <div className="col-md-3"><label>Hip (cm)</label><input type="number" className="form-control" value={form.hip_cm} onChange={e=>setForm({...form,hip_cm:e.target.value})} /></div>
                  <div className="col-md-3"><label>Wrist (cm)</label><input type="number" className="form-control" value={form.wrist_cm} onChange={e=>setForm({...form,wrist_cm:e.target.value})} /></div>
                  <div className="col-md-3"><label>Date Taken</label><input type="date" className="form-control" value={form.date_taken} onChange={e=>setForm({...form,date_taken:e.target.value})} /></div>

                  <div className="col-12 mt-3"><label className="fw-bold">Photos (required)</label></div>
                  <div className="col-md-4"><label>Front View *</label><input type="file" accept="image/*" className="form-control" onChange={e=>setFront(e.target.files[0])} /></div>
                  <div className="col-md-4"><label>Left View *</label><input type="file" accept="image/*" className="form-control" onChange={e=>setLeft(e.target.files[0])} /></div>
                  <div className="col-md-4"><label>Right View *</label><input type="file" accept="image/*" className="form-control" onChange={e=>setRight(e.target.files[0])} /></div>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={()=>setShowModal(false)}>Cancel</button>
                <button className="btn btn-primary" onClick={submit} disabled={!valid()}>Save Record</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
