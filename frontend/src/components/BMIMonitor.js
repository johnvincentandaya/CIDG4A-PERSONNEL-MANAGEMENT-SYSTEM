import React, {useEffect, useState} from 'react';
import { api, absolutizePath } from '../api';
import { RANKS } from '../constants/ranks';

const UNITS = ['RHQ', 'Cavite', 'Laguna', 'Batangas', 'Rizal', 'Quezon'];

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

  // Update modal state
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [updateForm, setUpdateForm] = useState({rank:'', name:'', unit:'RHQ', age:'', sex:'Male', height_cm:'', weight_kg:'', waist_cm:'', hip_cm:'', wrist_cm:'', date_taken: ''});
  const [updateFront, setUpdateFront] = useState(null);
  const [updateLeft, setUpdateLeft] = useState(null);
  const [updateRight, setUpdateRight] = useState(null);
  const [updateRecordId, setUpdateRecordId] = useState(null);
  const [existingPhotos, setExistingPhotos] = useState({front: null, left: null, right: null});

  // filters
  const [unitFilter, setUnitFilter] = useState('All Units');
  const [monthFilter, setMonthFilter] = useState('All Months');
  const [yearFilter, setYearFilter] = useState('All Years');
  const [search, setSearch] = useState('');
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportMonth, setReportMonth] = useState('');
  const [reportYear, setReportYear] = useState('');
  const [preparedBy, setPreparedBy] = useState('');
  const [notedBy, setNotedBy] = useState('');
  const [reportType, setReportType] = useState('pdf');
  const [reportFileName, setReportFileName] = useState('bmi_report');

  // BMI History state
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [historyPersonnel, setHistoryPersonnel] = useState(null);
  const [historyRecords, setHistoryRecords] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [dateRecord, setDateRecord] = useState(null);
  const [dateLoading, setDateLoading] = useState(false);
  const [personnelList, setPersonnelList] = useState([]);
  const [selectedPersonnelId, setSelectedPersonnelId] = useState('');

  // View mode: 'latest' or 'history'
  const [viewMode, setViewMode] = useState('latest');

  useEffect(()=>{ load(); loadPersonnelList(); },[])
  
  function load(){
    api.get('/api/bmi/', { params: { latest_only: true } }).then(r=>setRecords(r.data)).catch(()=>{});
  }

  function loadPersonnelList(){
    api.get('/api/bmi/distinct-personnel').then(r=>setPersonnelList(r.data)).catch(()=>{});
  }

  function openNew(){
    setForm({rank:'', name:'', unit:'RHQ', age:'', sex:'Male', height_cm:'', weight_kg:'', waist_cm:'', hip_cm:'', wrist_cm:'', date_taken: ''});
    setFront(null); setLeft(null); setRight(null);
    setShowModal(true);
  }

  async function downloadSingleResult(record){
    const suggested = `BMI_RESULT_${(record?.name || 'personnel').replace(/\s+/g, '_')}`;
    const fileName = window.prompt('Enter file name for BMI result PDF', suggested);
    if (!fileName || !fileName.trim()) {
      alert('File name is required before generating the BMI result PDF.');
      return;
    }

    try {
      const res = await api.get(`/api/bmi/${record.id}/pdf`, {
        params: { file_name: fileName.trim() },
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${fileName.trim()}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert('Error generating BMI result PDF.');
    }
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
      loadPersonnelList();
    }catch(err){
      alert('Error saving BMI record: '+ (err.response?.data?.detail || err.message));
    }
  }

  // Update functions
  function openUpdate(record) {
    setUpdateRecordId(record.id);
    setUpdateForm({
      rank: record.rank || '',
      name: record.name || '',
      unit: record.unit || 'RHQ',
      age: record.age || '',
      sex: record.sex || 'Male',
      height_cm: record.height_cm || '',
      weight_kg: record.weight_kg || '',
      waist_cm: record.waist_cm || '',
      hip_cm: record.hip_cm || '',
      wrist_cm: record.wrist_cm || '',
      date_taken: record.date_taken ? new Date(record.date_taken).toISOString().split('T')[0] : ''
    });
    // Store existing photo paths for display
    setExistingPhotos({
      front: record.photo_front,
      left: record.photo_left,
      right: record.photo_right
    });
    // Clear file inputs (new photos optional)
    setUpdateFront(null);
    setUpdateLeft(null);
    setUpdateRight(null);
    setShowUpdateModal(true);
  }

  function updateValid() {
    return updateForm.rank && updateForm.name && updateForm.unit && 
           updateForm.age && updateForm.height_cm && updateForm.weight_kg;
  }

  async function submitUpdate() {
    if(!updateValid()) return alert('Please fill all required fields (rank, name, unit, age, height, weight)');
    
    const data = new FormData();
    Object.keys(updateForm).forEach(k => { 
      if(updateForm[k]) data.append(k, updateForm[k]); 
    });
    
    // Only append photos if new ones are selected
    if (updateFront) data.append('photo_front', updateFront);
    if (updateLeft) data.append('photo_left', updateLeft);
    if (updateRight) data.append('photo_right', updateRight);
    
    try {
      await api.put(`/api/bmi/${updateRecordId}`, data, { 
        headers: {'Content-Type':'multipart/form-data'} 
      });
      setShowUpdateModal(false);
      load();
      loadPersonnelList();
      alert('BMI record updated successfully! Previous record preserved in history.');
    } catch(err) {
      alert('Error updating BMI record: ' + (err.response?.data?.detail || err.message));
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

  // BMI History Functions
  function openHistoryModal(personnelId = null) {
    setShowHistoryModal(true);
    setHistoryError('');
    setDateRecord(null);
    setSelectedDate('');
    
    if (personnelId) {
      setSelectedPersonnelId(personnelId);
      loadHistoryById(personnelId);
    } else {
      setSelectedPersonnelId('');
      setHistoryPersonnel(null);
      setHistoryRecords([]);
    }
  }

  async function loadHistoryById(personnelId) {
    if (!personnelId) return;
    
    setHistoryLoading(true);
    setHistoryError('');
    setDateRecord(null);
    
    try {
      // Try loading by personnel_id first
      let response = await api.get(`/api/bmi/history/${personnelId}`).catch(() => null);
      
      // If no results, try by name
      if (!response || !response.data || (!response.data.history && !response.data.history?.length)) {
        const personnel = personnelList.find(p => p.id === personnelId);
        if (personnel) {
          response = await api.get(`/api/bmi/history/by-name/${encodeURIComponent(personnel.name)}`);
        }
      }
      
      if (response && response.data) {
        setHistoryPersonnel(response.data);
        setHistoryRecords(response.data.history || []);
      } else {
        setHistoryError('No BMI history found for this personnel.');
        setHistoryPersonnel(null);
        setHistoryRecords([]);
      }
    } catch (err) {
      console.error('Error loading BMI history:', err);
      setHistoryError('Error loading BMI history. Please try again.');
      setHistoryPersonnel(null);
      setHistoryRecords([]);
    } finally {
      setHistoryLoading(false);
    }
  }

  async function loadHistoryByDate() {
    if (!selectedPersonnelId || !selectedDate) {
      alert('Please select both a personnel and a date.');
      return;
    }
    
    setDateLoading(true);
    setDateRecord(null);
    
    try {
      const response = await api.get(`/api/bmi/history/${selectedPersonnelId}/by-date`, {
        params: { date: selectedDate }
      });
      setDateRecord(response.data);
    } catch (err) {
      if (err.response && err.response.status === 404) {
        setDateRecord(null);
        alert(`No BMI record found for the selected date ${selectedDate}`);
      } else {
        alert('Error fetching BMI record for the selected date.');
      }
    } finally {
      setDateLoading(false);
    }
  }

  function handlePersonnelChange(e) {
    const val = e.target.value;
    setSelectedPersonnelId(val);
    setDateRecord(null);
    setSelectedDate('');
    
    if (val) {
      loadHistoryById(val);
    } else {
      setHistoryPersonnel(null);
      setHistoryRecords([]);
    }
  }

  function handleDateChange(e) {
    setSelectedDate(e.target.value);
    setDateRecord(null);
  }

  function clearDateFilter() {
    setSelectedDate('');
    setDateRecord(null);
  }

  function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  }

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
            <button 
              className="btn btn-outline-info btn-sm me-2" 
              onClick={() => openHistoryModal()}
            >
              <i className="bi bi-clock-history me-1" />
              View History
            </button>
            <button className="btn btn-outline-secondary btn-sm me-2" onClick={()=>setShowReportModal(true)}>
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
                      <div className="btn-group btn-group-sm">
                        <button className="btn btn-outline-info" onClick={() => openHistoryModal(r.personnel_id)} title="View BMI History">
                          <i className="bi bi-clock-history" />
                        </button>
                        <button className="btn btn-outline-warning" onClick={() => openUpdate(r)} title="Update BMI Record">
                          <i className="bi bi-pencil" />
                        </button>
                        <button className="btn btn-outline-primary" onClick={()=>downloadSingleResult(r)} title="Generate BMI Result PDF">
                          <i className="bi bi-file-earmark-pdf" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* New Record Modal */}
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

      {/* Update BMI Record Modal */}
      {showUpdateModal && (
        <div className="modal d-block" tabIndex={-1}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header bg-warning">
                <h5 className="modal-title text-dark">
                  <i className="bi bi-pencil-square me-2"></i>
                  Update BMI Record
                </h5>
                <button className="btn-close" onClick={()=>setShowUpdateModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="alert alert-info mb-3">
                  <i className="bi bi-info-circle me-2"></i>
                  <small>Update the BMI record. Leave photo fields empty to keep existing photos.</small>
                </div>
                <div className="row g-2">
                  <div className="col-md-4">
                    <label>Rank *</label>
                    <select
                      className="form-select"
                      value={updateForm.rank}
                      onChange={e=>setUpdateForm({...updateForm,rank:e.target.value})}
                    >
                      <option value="">Select rank</option>
                      {RANKS.map(r => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-md-4">
                    <label>Name *</label>
                    <input className="form-control" value={updateForm.name} onChange={e=>setUpdateForm({...updateForm,name:e.target.value})} />
                  </div>
                  <div className="col-md-4">
                    <label>Unit *</label>
                    <select className="form-select" value={updateForm.unit} onChange={e=>setUpdateForm({...updateForm,unit:e.target.value})}>
                      <option>RHQ</option>
                      <option>Cavite</option>
                      <option>Laguna</option>
                      <option>Batangas</option>
                      <option>Rizal</option>
                      <option>Quezon</option>
                    </select>
                  </div>
                  <div className="col-md-3">
                    <label>Age *</label>
                    <input type="number" className="form-control" value={updateForm.age} onChange={e=>setUpdateForm({...updateForm,age:e.target.value})} />
                  </div>
                  <div className="col-md-3">
                    <label>Sex</label>
                    <select className="form-select" value={updateForm.sex} onChange={e=>setUpdateForm({...updateForm,sex:e.target.value})}>
                      <option>Male</option>
                      <option>Female</option>
                    </select>
                  </div>
                  <div className="col-md-3">
                    <label>Height (cm) *</label>
                    <input type="number" className="form-control" value={updateForm.height_cm} onChange={e=>setUpdateForm({...updateForm,height_cm:e.target.value})} />
                  </div>
                  <div className="col-md-3">
                    <label>Weight (kg) *</label>
                    <input type="number" className="form-control" value={updateForm.weight_kg} onChange={e=>setUpdateForm({...updateForm,weight_kg:e.target.value})} />
                  </div>
                  <div className="col-md-3">
                    <label>Waist (cm)</label>
                    <input type="number" className="form-control" value={updateForm.waist_cm} onChange={e=>setUpdateForm({...updateForm,waist_cm:e.target.value})} />
                  </div>
                  <div className="col-md-3">
                    <label>Hip (cm)</label>
                    <input type="number" className="form-control" value={updateForm.hip_cm} onChange={e=>setUpdateForm({...updateForm,hip_cm:e.target.value})} />
                  </div>
                  <div className="col-md-3">
                    <label>Wrist (cm)</label>
                    <input type="number" className="form-control" value={updateForm.wrist_cm} onChange={e=>setUpdateForm({...updateForm,wrist_cm:e.target.value})} />
                  </div>
                  <div className="col-md-3">
                    <label>Date Taken</label>
                    <input type="date" className="form-control" value={updateForm.date_taken} onChange={e=>setUpdateForm({...updateForm,date_taken:e.target.value})} />
                  </div>

                  <div className="col-12 mt-3">
                    <label className="fw-bold">Photos (optional - leave empty to keep existing)</label>
                  </div>
                  <div className="col-md-4">
                    <label>Front View</label>
                    {existingPhotos.front && (
                      <div className="mb-1">
                        <small className="text-muted">Current: Front photo exists</small>
                      </div>
                    )}
                    <input type="file" accept="image/*" className="form-control" onChange={e=>setUpdateFront(e.target.files[0])} />
                  </div>
                  <div className="col-md-4">
                    <label>Left View</label>
                    {existingPhotos.left && (
                      <div className="mb-1">
                        <small className="text-muted">Current: Left photo exists</small>
                      </div>
                    )}
                    <input type="file" accept="image/*" className="form-control" onChange={e=>setUpdateLeft(e.target.files[0])} />
                  </div>
                  <div className="col-md-4">
                    <label>Right View</label>
                    {existingPhotos.right && (
                      <div className="mb-1">
                        <small className="text-muted">Current: Right photo exists</small>
                      </div>
                    )}
                    <input type="file" accept="image/*" className="form-control" onChange={e=>setUpdateRight(e.target.files[0])} />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={()=>setShowUpdateModal(false)}>Cancel</button>
                <button className="btn btn-warning" onClick={submitUpdate} disabled={!updateValid()}>
                  <i className="bi bi-save me-1"></i>
                  Update BMI Record
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Report Modal */}
      {showReportModal && (
        <div className="modal d-block" tabIndex={-1}>
          <div className="modal-dialog modal-sm">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Generate BMI Report</h5>
                <button className="btn-close" onClick={()=>setShowReportModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-2">
                  <label>Month</label>
                  <select className="form-select" value={reportMonth} onChange={e=>setReportMonth(e.target.value)}>
                    <option value="">All Months</option>
                    {monthOptions.slice(1).map((m,i)=> <option key={m} value={i+1}>{m}</option>)}
                  </select>
                </div>
                <div className="mb-2">
                  <label>Year</label>
                  <select className="form-select" value={reportYear} onChange={e=>setReportYear(e.target.value)}>
                    <option value="">All Years</option>
                    {[...new Set(records.filter(r=>r.date_taken).map(r=> new Date(r.date_taken).getFullYear()))].sort().map(y=> <option key={y} value={y}>{y}</option>)}
                  </select>
                </div>
                <div className="mb-2">
                  <label>Prepared By</label>
                  <input className="form-control" value={preparedBy} onChange={e=>setPreparedBy(e.target.value)} />
                </div>
                <div className="mb-2">
                  <label>Noted By</label>
                  <input className="form-control" value={notedBy} onChange={e=>setNotedBy(e.target.value)} />
                </div>
                <div className="mb-2">
                  <label>Report Type</label>
                  <select className="form-select" value={reportType} onChange={e=>setReportType(e.target.value)}>
                    <option value="pdf">PDF</option>
                    <option value="excel">Excel</option>
                  </select>
                </div>
                <div className="mb-2">
                  <label>File Name *</label>
                  <input
                    className="form-control"
                    value={reportFileName}
                    onChange={e=>setReportFileName(e.target.value)}
                    placeholder="e.g. bmi_report_march_2026"
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={()=>setShowReportModal(false)}>Cancel</button>
                <button className="btn btn-primary" onClick={async ()=>{
                  try{
                    if (!reportFileName.trim()) {
                      alert('File name is required before generating the report.');
                      return;
                    }
                    const fd = new FormData();
                    if (reportMonth) fd.append('month', reportMonth);
                    if (reportYear) fd.append('year', reportYear);
                    if (unitFilter && unitFilter!=='All Units') fd.append('unit', unitFilter);
                    fd.append('prepared_by', preparedBy);
                    fd.append('noted_by', notedBy);
                    fd.append('report_type', reportType);
                    fd.append('file_name', reportFileName.trim());
                    const res = await api.post('/api/bmi/report', fd, { responseType: 'blob' });
                    const ext = reportType === 'excel' ? 'xlsx' : 'pdf';
                    const url = window.URL.createObjectURL(new Blob([res.data]));
                    const a = document.createElement('a'); a.href = url; a.download = `${reportFileName.trim()}.${ext}`; document.body.appendChild(a); a.click(); a.remove();
                    setShowReportModal(false);
                  }catch(err){ alert('Error generating BMI report'); }
                }} disabled={!reportFileName.trim()}>Generate</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* BMI History Modal */}
      {showHistoryModal && (
        <div className="modal d-block" tabIndex={-1} style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-xl modal-dialog-scrollable">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-clock-history me-2"></i>
                  BMI History
                </h5>
                <button className="btn-close" onClick={()=>setShowHistoryModal(false)}></button>
              </div>
              <div className="modal-body">
                {/* Personnel Selection */}
                <div className="row mb-4">
                  <div className="col-md-6">
                    <label className="fw-bold mb-2">Select Personnel</label>
                    <select 
                      className="form-select" 
                      value={selectedPersonnelId} 
                      onChange={handlePersonnelChange}
                    >
                      <option value="">-- Select Personnel --</option>
                      {personnelList.map(p => (
                        <option key={p.id || p.name} value={p.id || p.name}>
                          {p.name} {p.rank ? `(${p.rank})` : ''} - {p.unit} [{p.total_records || 0} records]
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-md-4">
                    <label className="fw-bold mb-2">Filter by Date</label>
                    <input 
                      type="date" 
                      className="form-control" 
                      value={selectedDate}
                      onChange={handleDateChange}
                    />
                  </div>
                  <div className="col-md-2 d-flex align-items-end">
                    <div className="d-grid gap-2 w-100">
                      <button 
                        className="btn btn-primary" 
                        onClick={loadHistoryByDate}
                        disabled={!selectedPersonnelId || !selectedDate || dateLoading}
                      >
                        {dateLoading ? 'Searching...' : 'Search Date'}
                      </button>
                      {(selectedDate) && (
                        <button 
                          className="btn btn-outline-secondary btn-sm"
                          onClick={clearDateFilter}
                        >
                          Clear
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Loading State */}
                {historyLoading && (
                  <div className="text-center py-4">
                    <div className="spinner-border text-primary" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="mt-2 text-muted">Loading BMI history...</p>
                  </div>
                )}

                {/* Error State */}
                {historyError && !historyLoading && (
                  <div className="alert alert-warning">
                    <i className="bi bi-exclamation-triangle me-2"></i>
                    {historyError}
                  </div>
                )}

                {/* Date Record Result */}
                {dateRecord && !historyLoading && (
                  <div className="card mb-4 border-primary">
                    <div className="card-header bg-primary text-white">
                      <i className="bi bi-calendar-check me-2"></i>
                      BMI Record as of {formatDate(dateRecord.date_taken)}
                    </div>
                    <div className="card-body">
                      <div className="row">
                        <div className="col-md-3">
                          <p className="mb-1"><strong>Rank:</strong> {dateRecord.rank}</p>
                          <p className="mb-1"><strong>Name:</strong> {dateRecord.name}</p>
                          <p className="mb-1"><strong>Unit:</strong> {dateRecord.unit}</p>
                        </div>
                        <div className="col-md-3">
                          <p className="mb-1"><strong>Age:</strong> {dateRecord.age}</p>
                          <p className="mb-1"><strong>Sex:</strong> {dateRecord.sex}</p>
                          <p className="mb-1"><strong>Date:</strong> {formatDate(dateRecord.date_taken)}</p>
                        </div>
                        <div className="col-md-3">
                          <p className="mb-1"><strong>Height:</strong> {dateRecord.height_cm} cm</p>
                          <p className="mb-1"><strong>Weight:</strong> {dateRecord.weight_kg} kg</p>
                          <p className="mb-1"><strong>BMI:</strong> {dateRecord.bmi}</p>
                        </div>
                        <div className="col-md-3">
                          <p className="mb-1"><strong>Classification:</strong></p>
                          <span className={classificationClass(dateRecord.classification)}>
                            {dateRecord.classification}
                          </span>
                          <p className="mb-1 mt-2"><strong>Result:</strong> {dateRecord.result}</p>
                        </div>
                      </div>
                      {dateRecord.waist_cm && (
                        <div className="mt-2">
                          <small className="text-muted">
                            Measurements: Waist {dateRecord.waist_cm}cm | Hip {dateRecord.hip_cm || '-'}cm | Wrist {dateRecord.wrist_cm || '-'}cm
                          </small>
                        </div>
                      )}
                      <div className="mt-3">
                        <button 
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => downloadSingleResult(dateRecord)}
                        >
                          <i className="bi bi-file-earmark-pdf me-1"></i>
                          Download PDF
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* History Records Table */}
                {historyRecords.length > 0 && !historyLoading && (
                  <div>
                    <div className="d-flex justify-content-between align-items-center mb-3">
                      <h6 className="mb-0">
                        <i className="bi bi-list-ul me-2"></i>
                        BMI History Records ({historyRecords.length} total)
                      </h6>
                      {historyPersonnel && (
                        <span className="badge bg-secondary">
                          Latest: {formatDate(historyPersonnel.latest_bmi?.date_taken)}
                        </span>
                      )}
                    </div>
                    
                    <div className="table-responsive">
                      <table className="table table-sm table-hover">
                        <thead className="table-light">
                          <tr>
                            <th>Date Taken</th>
                            <th>Rank</th>
                            <th>Name</th>
                            <th>Unit</th>
                            <th>Age</th>
                            <th>Height</th>
                            <th>Weight</th>
                            <th>BMI</th>
                            <th>Classification</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {historyRecords.map((rec, index) => (
                            <tr key={rec.id || index} className={index === 0 ? 'table-primary' : ''}>
                              <td>{formatDate(rec.date_taken)}</td>
                              <td>{rec.rank}</td>
                              <td>{rec.name}</td>
                              <td>{rec.unit}</td>
                              <td>{rec.age}</td>
                              <td>{rec.height_cm} cm</td>
                              <td>{rec.weight_kg} kg</td>
                              <td><strong>{rec.bmi}</strong></td>
                              <td>
                                <span className={classificationClass(rec.classification)}>
                                  {rec.classification}
                                </span>
                              </td>
                              <td>
                                <button 
                                  className="btn btn-sm btn-outline-primary"
                                  onClick={() => downloadSingleResult(rec)}
                                  title="Download PDF"
                                >
                                  <i className="bi bi-file-earmark-pdf"></i>
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Empty State - No Selection */}
                {!selectedPersonnelId && !historyLoading && !historyError && (
                  <div className="text-center py-5 text-muted">
                    <i className="bi bi-person-plus" style={{ fontSize: '3rem' }}></i>
                    <p className="mt-3">Select a personnel above to view their BMI history.</p>
                  </div>
                )}

                {/* Empty State - No History */}
                {selectedPersonnelId && historyRecords.length === 0 && !historyLoading && !historyError && (
                  <div className="text-center py-5 text-muted">
                    <i className="bi bi-clipboard-x" style={{ fontSize: '3rem' }}></i>
                    <p className="mt-3">No BMI history found for this personnel.</p>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={()=>setShowHistoryModal(false)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
