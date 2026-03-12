import React, {useEffect, useState, useRef} from 'react';
import axios from 'axios';

const UNITS = ['RHQ','Cavite','Laguna','Batangas','Rizal','Quezon'];
const STATUS = ['Active','Reassigned','Retired'];
const RANKS = [
  'PGEN',
  'PLTGEN',
  'PMGEN',
  'PBGEn',
  'PCOL',
  'PLTCOL',
  'PMAJ',
  'PCPT',
  'PLT',
  'PEMS',
  'PCMS',
  'PSMS',
  'PMSg',
  'PSSg',
  'PCpl',
  'Pat'
];

function TrainingInput({entries, setEntries, category}){
  function update(idx, key, value){
    const arr = entries.slice(); arr[idx] = {...arr[idx], [key]: value}; setEntries(arr);
  }
  function addRow(){ setEntries([...entries, {title:'', file:null}]); }
  function removeRow(i){ const arr = entries.slice(); arr.splice(i,1); setEntries(arr); }
  return (
    <div className="mb-3 p-2" style={{background: category==='mandatory'? '#eef6ff':'#f2fff0', borderRadius:8}}>
      <div className="d-flex justify-content-between align-items-center mb-2"><strong>{category==='mandatory' ? 'h. Mandatory Trainings (Multiple Files)':'i. Specialized Trainings (Multiple Files)'}</strong><button className="btn btn-sm btn-outline-secondary" onClick={addRow}>+</button></div>
      {entries.map((e,i)=> (
        <div key={i} className="d-flex gap-2 mb-2">
          <input className="form-control" placeholder="Certificate Title" value={e.title} onChange={ev=>update(i,'title',ev.target.value)} />
          <input type="file" accept="application/pdf" onChange={ev=>update(i,'file', ev.target.files[0])} />
          <button className="btn btn-sm btn-danger" onClick={()=>removeRow(i)}>Remove</button>
        </div>
      ))}
      {entries.length===0 && <div className="text-muted">Add at least one certificate</div>}
    </div>
  )
}

export default function Form201(){
  const [records, setRecords] = useState([]);
  const [editId, setEditId] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [activeTab, setActiveTab] = useState('personal');
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [confirmAdd, setConfirmAdd] = useState(false);
  const [form, setForm] = useState({rank:'',last_name:'',first_name:'',mi:'',suffix:'',unit:'RHQ',status:'Active'});

  // single required doc files
  const [pds, setPds] = useState(null);
  const [pdsExisting, setPdsExisting] = useState(null);
  const [appointment, setAppointment] = useState(null);
  const [appointmentExisting, setAppointmentExisting] = useState(null);
  const [promotion, setPromotion] = useState(null);
  const [promotionExisting, setPromotionExisting] = useState(null);
  const [designation, setDesignation] = useState(null);
  const [designationExisting, setDesignationExisting] = useState(null);
  const [reassignment, setReassignment] = useState(null);
  const [reassignmentExisting, setReassignmentExisting] = useState(null);
  const [diploma, setDiploma] = useState(null);
  const [diplomaExisting, setDiplomaExisting] = useState(null);
  const [eligibility, setEligibility] = useState(null);
  const [eligibilityExisting, setEligibilityExisting] = useState(null);
  const [iper, setIper] = useState(null);
  const [iperExisting, setIperExisting] = useState(null);
  const [saln, setSaln] = useState(null);
  const [salnExisting, setSalnExisting] = useState(null);
  const [pft, setPft] = useState(null);
  const [pftExisting, setPftExisting] = useState(null);
  const [rca, setRca] = useState(null);
  const [rcaExisting, setRcaExisting] = useState(null);

  const [mandatory, setMandatory] = useState([{title:'', file:null}]);
  const [specialized, setSpecialized] = useState([{title:'', file:null}]);
  const [mandatoryExisting, setMandatoryExisting] = useState([]);
  const [specializedExisting, setSpecializedExisting] = useState([]);
  const [deleteMandatoryIds, setDeleteMandatoryIds] = useState([]);
  const [deleteSpecializedIds, setDeleteSpecializedIds] = useState([]);

  useEffect(()=>{ load() },[])
  function load(){ axios.get('http://localhost:8000/api/personnel/').then(r=>setRecords(r.data)).catch(()=>{}); }

  function resetModal(){
    setForm({rank:'',last_name:'',first_name:'',mi:'',suffix:'',unit:'RHQ',status:'Active'});
    setPds(null); setAppointment(null); setPromotion(null); setDesignation(null); setReassignment(null); setDiploma(null); setEligibility(null); setIper(null); setSaln(null); setPft(null); setRca(null);
    setPdsExisting(null); setAppointmentExisting(null); setPromotionExisting(null); setDesignationExisting(null); setReassignmentExisting(null); setDiplomaExisting(null); setEligibilityExisting(null); setIperExisting(null); setSalnExisting(null); setPftExisting(null); setRcaExisting(null);
    setMandatory([{title:'', file:null}]); setSpecialized([{title:'', file:null}]);
    setMandatoryExisting([]); setSpecializedExisting([]); setDeleteMandatoryIds([]); setDeleteSpecializedIds([]);
    setActiveTab('personal');
    setEditId(null);
  }

  function openModal(){ resetModal(); setShowModal(true); }

  function fileUrl(path){
    if (!path) return null;
    const p = path.replace(/\\\\/g,'/').replace(/\\/g,'/');
    const idx = p.indexOf('uploads/');
    if (idx>=0) return `http://localhost:8000/${p.slice(idx)}`;
    return `http://localhost:8000/${p}`;
  }

  async function editPerson(id){
    try{
      const res = await axios.get(`http://localhost:8000/api/personnel/${id}`);
      const p = res.data;
      setEditId(id);
      setForm({rank:p.rank,last_name:p.last_name,first_name:p.first_name,mi:p.mi||'',suffix:p.suffix||'',unit:p.unit,status:p.status});
      // map documents
      const docs = p.documents || [];
      const map = {};
      docs.forEach(d=> map[d.doc_type]=d.file_path);
      setPdsExisting(map['pds'] ? fileUrl(map['pds']) : null);
      setAppointmentExisting(map['appointment'] ? fileUrl(map['appointment']) : null);
      setPromotionExisting(map['promotion'] ? fileUrl(map['promotion']) : null);
      setDesignationExisting(map['designation'] ? fileUrl(map['designation']) : null);
      setReassignmentExisting(map['reassignment'] ? fileUrl(map['reassignment']) : null);
      setDiplomaExisting(map['diploma'] ? fileUrl(map['diploma']) : null);
      setEligibilityExisting(map['eligibility'] ? fileUrl(map['eligibility']) : null);
      setIperExisting(map['iper'] ? fileUrl(map['iper']) : null);
      setSalnExisting(map['saln'] ? fileUrl(map['saln']) : null);
      setPftExisting(map['pft'] ? fileUrl(map['pft']) : null);
      setRcaExisting(map['rca'] ? fileUrl(map['rca']) : null);
      // trainings
      const tr = p.trainings || [];
      setMandatoryExisting(tr.filter(t=>t.category==='mandatory').map(t=>({id:t.id,title:t.title,file_path:t.file_path,url:fileUrl(t.file_path)})));
      setSpecializedExisting(tr.filter(t=>t.category==='specialized').map(t=>({id:t.id,title:t.title,file_path:t.file_path,url:fileUrl(t.file_path)})));

      setShowModal(true);
      setActiveTab('personal');
    }catch(err){
      alert('Unable to load record');
    }
  }

  function checkRequiredPersonal(){ return form.rank.trim() && form.last_name.trim() && form.first_name.trim(); }

  function checkRequiredDocs(){
    // documents are now optional at creation; always allow submit from UI
    return true;
  }

  async function doSubmit(){
    // prepare FormData
    const data = new FormData();
    data.append('rank', form.rank);
    data.append('last_name', form.last_name);
    data.append('first_name', form.first_name);
    data.append('mi', form.mi || '');
    data.append('suffix', form.suffix || '');
    data.append('unit', form.unit);
    data.append('status', form.status);
    // single files - only append if new file selected
    let hasSingleFiles = false;
    if (pds) { data.append('pds', pds); hasSingleFiles = true; }
    if (appointment) { data.append('appointment', appointment); hasSingleFiles = true; }
    if (promotion) { data.append('promotion', promotion); hasSingleFiles = true; }
    if (designation) { data.append('designation', designation); hasSingleFiles = true; }
    if (reassignment) { data.append('reassignment', reassignment); hasSingleFiles = true; }
    if (diploma) { data.append('diploma', diploma); hasSingleFiles = true; }
    if (eligibility) { data.append('eligibility', eligibility); hasSingleFiles = true; }
    if (iper) { data.append('iper', iper); hasSingleFiles = true; }
    if (saln) { data.append('saln', saln); hasSingleFiles = true; }
    if (pft) { data.append('pft', pft); hasSingleFiles = true; }
    if (rca) { data.append('rca', rca); hasSingleFiles = true; }

    // trainings: append titles and files for new rows
    let hasTrainingFiles = false;
    mandatory.forEach(m => { if (m.file) { hasTrainingFiles = true; data.append('mandatory_titles', m.title); data.append('mandatory_files', m.file); } });
    specialized.forEach(s => { if (s.file) { hasTrainingFiles = true; data.append('specialized_titles', s.title); data.append('specialized_files', s.file); } });

    // include deletions if any (only relevant on edit)
    if (deleteMandatoryIds && deleteMandatoryIds.length>0) data.append('delete_mandatory_ids', JSON.stringify(deleteMandatoryIds));
    if (deleteSpecializedIds && deleteSpecializedIds.length>0) data.append('delete_specialized_ids', JSON.stringify(deleteSpecializedIds));

    const hasAnyFiles = hasSingleFiles || hasTrainingFiles;

    try{
      if (editId){
        await axios.put(`http://localhost:8000/api/personnel/${editId}`, data, { headers: {'Content-Type':'multipart/form-data'} });
      } else if (hasAnyFiles) {
        await axios.post('http://localhost:8000/api/personnel/', data, { headers: {'Content-Type':'multipart/form-data'} });
      } else {
        // no documents selected – call basic endpoint that only expects form fields
        await axios.post('http://localhost:8000/api/personnel/basic', data, { headers: {'Content-Type':'multipart/form-data'} });
      }
      setShowModal(false);
      load();
    }catch(err){
      let message = err.message;
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        message = detail.map(d => d.msg || JSON.stringify(d)).join('; ');
      } else if (typeof detail === 'string') {
        message = detail;
      } else if (detail) {
        message = JSON.stringify(detail);
      }
      alert('Error saving record: ' + message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-eyebrow">Personnel Records</div>
          <h1 className="page-title">Form 201 Registry</h1>
          <p className="page-subtitle">
            Centralized registry of all CIDG RFU4A personnel, including status, unit assignment, and documentary compliance.
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn-quiet">
            <i className="bi bi-funnel" />
            Saved filter: All Personnel
          </button>
        </div>
      </div>

      <div className="card-section p-3 mb-3">
        <div className="filter-bar">
          <div className="filter-controls">
            <select className="form-select form-select-sm">
              <option>All Units</option>
              {UNITS.map(u => <option key={u}>{u}</option>)}
            </select>
            <select className="form-select form-select-sm">
              <option>All Status</option>
              {STATUS.map(s => <option key={s}>{s}</option>)}
            </select>
            <input className="form-control form-control-sm" placeholder="Search by name, rank, or unit" />
          </div>
          <div>
            <button className="btn btn-outline-secondary btn-sm me-2">
              <i className="bi bi-file-earmark-text me-1" />
              Generate Report
            </button>
            <button className="btn btn-primary btn-sm" onClick={openModal}>
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
                  <th>Last Name</th>
                  <th>First Name</th>
                  <th>M.I.</th>
                  <th>Suffix</th>
                  <th>Unit</th>
                  <th>Status</th>
                  <th>Documents</th>
                  <th>Date Added</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.length === 0 && (
                  <tr>
                    <td colSpan={10}>
                      <div className="table-empty-state">
                        No personnel records found. Use the filters above or create a new record to get started.
                      </div>
                    </td>
                  </tr>
                )}
                {records.map(r=> {
                  const docCount = (r.documents || []).length;
                  const statusKey = (r.status || '').toLowerCase();
                  return (
                    <tr key={r.id}>
                      <td>{r.rank}</td>
                      <td>{r.last_name}</td>
                      <td>{r.first_name}</td>
                      <td>{r.mi}</td>
                      <td>{r.suffix}</td>
                      <td>{r.unit}</td>
                      <td>
                        <span className={`badge-status badge-status--${statusKey || 'active'}`}>
                          {r.status}
                        </span>
                      </td>
                      <td>
                        <span>{docCount}/13 docs</span>
                        {docCount < 13 && (
                          <span className="text-danger ms-2 small">(missing)</span>
                        )}
                      </td>
                      <td>{new Date(r.date_added).toLocaleDateString()}</td>
                      <td>
                        <button
                          className="btn btn-sm btn-outline-primary"
                          onClick={()=>editPerson(r.id)}
                        >
                          <i className="bi bi-pencil-square me-1" />
                          Edit
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showModal && (
        <div className="modal d-block" tabIndex={-1}>
          <div className="modal-dialog modal-xl">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">{editId ? 'Edit Personnel Record' : 'Add New Personnel Record'}</h5>
                <button className="btn-close" onClick={()=>setConfirmCancel(true)}></button>
              </div>
              <div className="modal-body">
                <ul className="nav nav-tabs mb-3">
                  <li className="nav-item"><button className={`nav-link ${activeTab==='personal' ? 'active':''}`} onClick={()=>setActiveTab('personal')}>Personal Information</button></li>
                  <li className="nav-item"><button className={`nav-link ${activeTab==='documents' ? 'active':''}`} onClick={()=>setActiveTab('documents')}>Documents (13 Required)</button></li>
                </ul>
                {activeTab==='personal' && (
                  <div>
                    <div className="row">
                      <div className="col-md-6 mb-2">
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
                      <div className="col-md-6 mb-2"><label>Last Name *</label><input className="form-control" value={form.last_name} onChange={e=>setForm({...form,last_name:e.target.value})} /></div>
                      <div className="col-md-6 mb-2"><label>First Name *</label><input className="form-control" value={form.first_name} onChange={e=>setForm({...form,first_name:e.target.value})} /></div>
                      <div className="col-md-6 mb-2"><label>Middle Initial</label><input className="form-control" value={form.mi} onChange={e=>setForm({...form,mi:e.target.value})} /></div>
                      <div className="col-md-6 mb-2"><label>Suffix</label><input className="form-control" value={form.suffix} onChange={e=>setForm({...form,suffix:e.target.value})} /></div>
                      <div className="col-md-6 mb-2"><label>Unit</label><select className="form-select" value={form.unit} onChange={e=>setForm({...form,unit:e.target.value})}>{UNITS.map(u=> <option key={u}>{u}</option>)}</select></div>
                      <div className="col-md-6 mb-2"><label>Status</label><select className="form-select" value={form.status} onChange={e=>setForm({...form,status:e.target.value})}>{STATUS.map(s=> <option key={s}>{s}</option>)}</select></div>
                    </div>
                  </div>
                )}

                {activeTab==='documents' && (
                  <div>
                    <div className="mb-2 p-2">
                      <label className="fw-bold">a. CSC PDS Revised 2025 and Personal History Statement</label>
                      <div className="d-flex gap-2 align-items-center">
                        <input type="file" accept="application/pdf" onChange={e=>setPds(e.target.files[0])} />
                        <button className="btn btn-outline-primary" onClick={()=>{}}>Upload</button>
                        {pdsExisting && <a className="btn btn-sm btn-outline-secondary" href={pdsExisting} target="_blank" rel="noreferrer">View</a>}
                        {pdsExisting && <a className="btn btn-sm btn-outline-secondary" href={pdsExisting} download>Download</a>}
                      </div>
                    </div>
                    <div className="mb-2 p-2">
                      <label className="fw-bold">b. Appointment Order and CSC Attested Appointment</label>
                      <div className="d-flex gap-2 align-items-center">
                        <input type="file" accept="application/pdf" onChange={e=>setAppointment(e.target.files[0])} />
                        <button className="btn btn-outline-primary">Upload</button>
                        {appointmentExisting && <a className="btn btn-sm btn-outline-secondary" href={appointmentExisting} target="_blank" rel="noreferrer">View</a>}
                        {appointmentExisting && <a className="btn btn-sm btn-outline-secondary" href={appointmentExisting} download>Download</a>}
                      </div>
                    </div>
                    <div className="mb-2 p-2">
                      <label className="fw-bold">c. Promotion Orders and CSC Attested Appointments</label>
                      <div className="d-flex gap-2 align-items-center">
                        <input type="file" accept="application/pdf" onChange={e=>setPromotion(e.target.files[0])} />
                        <button className="btn btn-outline-primary">Upload</button>
                        {promotionExisting && <a className="btn btn-sm btn-outline-secondary" href={promotionExisting} target="_blank" rel="noreferrer">View</a>}
                        {promotionExisting && <a className="btn btn-sm btn-outline-secondary" href={promotionExisting} download>Download</a>}
                      </div>
                    </div>
                    <div className="mb-2 p-2">
                      <label className="fw-bold">d. Designation Orders</label>
                      <div className="d-flex gap-2 align-items-center">
                        <input type="file" accept="application/pdf" onChange={e=>setDesignation(e.target.files[0])} />
                        <button className="btn btn-outline-primary">Upload</button>
                        {designationExisting && <a className="btn btn-sm btn-outline-secondary" href={designationExisting} target="_blank" rel="noreferrer">View</a>}
                        {designationExisting && <a className="btn btn-sm btn-outline-secondary" href={designationExisting} download>Download</a>}
                      </div>
                    </div>
                    <div className="mb-2 p-2">
                      <label className="fw-bold">e. Reassignment Orders</label>
                      <div className="d-flex gap-2 align-items-center">
                        <input type="file" accept="application/pdf" onChange={e=>setReassignment(e.target.files[0])} />
                        <button className="btn btn-outline-primary">Upload</button>
                        {reassignmentExisting && <a className="btn btn-sm btn-outline-secondary" href={reassignmentExisting} target="_blank" rel="noreferrer">View</a>}
                        {reassignmentExisting && <a className="btn btn-sm btn-outline-secondary" href={reassignmentExisting} download>Download</a>}
                      </div>
                    </div>
                    <div className="mb-2 p-2">
                      <label className="fw-bold">f. Diploma / Transcript of Records</label>
                      <div className="d-flex gap-2 align-items-center">
                        <input type="file" accept="application/pdf" onChange={e=>setDiploma(e.target.files[0])} />
                        <button className="btn btn-outline-primary">Upload</button>
                        {diplomaExisting && <a className="btn btn-sm btn-outline-secondary" href={diplomaExisting} target="_blank" rel="noreferrer">View</a>}
                        {diplomaExisting && <a className="btn btn-sm btn-outline-secondary" href={diplomaExisting} download>Download</a>}
                      </div>
                    </div>
                    <div className="mb-2 p-2">
                      <label className="fw-bold">g. Eligibility</label>
                      <div className="d-flex gap-2 align-items-center">
                        <input type="file" accept="application/pdf" onChange={e=>setEligibility(e.target.files[0])} />
                        <button className="btn btn-outline-primary">Upload</button>
                        {eligibilityExisting && <a className="btn btn-sm btn-outline-secondary" href={eligibilityExisting} target="_blank" rel="noreferrer">View</a>}
                        {eligibilityExisting && <a className="btn btn-sm btn-outline-secondary" href={eligibilityExisting} download>Download</a>}
                      </div>
                    </div>

                    <div className="mb-3">
                      <strong>Existing Mandatory Trainings</strong>
                      {mandatoryExisting.map((m,i)=> (
                        <div key={m.id} className="d-flex gap-2 align-items-center my-2">
                          <div>{m.title}</div>
                          <a className="btn btn-sm btn-outline-secondary" href={m.url} target="_blank" rel="noreferrer">View</a>
                          <a className="btn btn-sm btn-outline-secondary" href={m.url} download>Download</a>
                          <button className="btn btn-sm btn-danger" onClick={()=>{ setMandatoryExisting(mandatoryExisting.filter(x=>x.id!==m.id)); setDeleteMandatoryIds([...deleteMandatoryIds, m.id]); }}>Remove</button>
                        </div>
                      ))}
                    </div>
                    <TrainingInput entries={mandatory} setEntries={setMandatory} category={'mandatory'} />

                    <div className="mb-3">
                      <strong>Existing Specialized Trainings</strong>
                      {specializedExisting.map((m,i)=> (
                        <div key={m.id} className="d-flex gap-2 align-items-center my-2">
                          <div>{m.title}</div>
                          <a className="btn btn-sm btn-outline-secondary" href={m.url} target="_blank" rel="noreferrer">View</a>
                          <a className="btn btn-sm btn-outline-secondary" href={m.url} download>Download</a>
                          <button className="btn btn-sm btn-danger" onClick={()=>{ setSpecializedExisting(specializedExisting.filter(x=>x.id!==m.id)); setDeleteSpecializedIds([...deleteSpecializedIds, m.id]); }}>Remove</button>
                        </div>
                      ))}
                    </div>
                    <TrainingInput entries={specialized} setEntries={setSpecialized} category={'specialized'} />

                    <div className="mb-2 p-2">
                      <label className="fw-bold">j. IPER</label>
                      <div className="d-flex gap-2 align-items-center">
                        <input type="file" accept="application/pdf" onChange={e=>setIper(e.target.files[0])} />
                        <button className="btn btn-outline-primary">Upload</button>
                        {iperExisting && <a className="btn btn-sm btn-outline-secondary" href={iperExisting} target="_blank" rel="noreferrer">View</a>}
                        {iperExisting && <a className="btn btn-sm btn-outline-secondary" href={iperExisting} download>Download</a>}
                      </div>
                    </div>
                    <div className="mb-2 p-2">
                      <label className="fw-bold">k. SALN</label>
                      <div className="d-flex gap-2 align-items-center">
                        <input type="file" accept="application/pdf" onChange={e=>setSaln(e.target.files[0])} />
                        <button className="btn btn-outline-primary">Upload</button>
                        {salnExisting && <a className="btn btn-sm btn-outline-secondary" href={salnExisting} target="_blank" rel="noreferrer">View</a>}
                        {salnExisting && <a className="btn btn-sm btn-outline-secondary" href={salnExisting} download>Download</a>}
                      </div>
                    </div>
                    <div className="mb-2 p-2">
                      <label className="fw-bold">l. PFT Results</label>
                      <div className="d-flex gap-2 align-items-center">
                        <input type="file" accept="application/pdf" onChange={e=>setPft(e.target.files[0])} />
                        <button className="btn btn-outline-primary">Upload</button>
                        {pftExisting && <a className="btn btn-sm btn-outline-secondary" href={pftExisting} target="_blank" rel="noreferrer">View</a>}
                        {pftExisting && <a className="btn btn-sm btn-outline-secondary" href={pftExisting} download>Download</a>}
                      </div>
                    </div>
                    <div className="mb-2 p-2">
                      <label className="fw-bold">m. RCA, Long Pay, Suspension, and Other Orders</label>
                      <div className="d-flex gap-2 align-items-center">
                        <input type="file" accept="application/pdf" onChange={e=>setRca(e.target.files[0])} />
                        <button className="btn btn-outline-primary">Upload</button>
                        {rcaExisting && <a className="btn btn-sm btn-outline-secondary" href={rcaExisting} target="_blank" rel="noreferrer">View</a>}
                        {rcaExisting && <a className="btn btn-sm btn-outline-secondary" href={rcaExisting} download>Download</a>}
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={()=>setConfirmCancel(true)}>Cancel</button>
                <button className="btn btn-primary" onClick={()=>setConfirmAdd(true)} disabled={!(checkRequiredPersonal() && checkRequiredDocs())}>Add Record</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {confirmCancel && (
        <div className="modal d-block"><div className="modal-dialog"><div className="modal-content"><div className="modal-header"><h5>Confirm</h5></div><div className="modal-body">Discard changes?</div><div className="modal-footer"><button className="btn btn-secondary" onClick={()=>setConfirmCancel(false)}>No</button><button className="btn btn-danger" onClick={()=>{ setConfirmCancel(false); setShowModal(false); }}>Yes, discard</button></div></div></div></div>
      )}

      {confirmAdd && (
        <div className="modal d-block"><div className="modal-dialog"><div className="modal-content"><div className="modal-header"><h5>Confirm</h5></div><div className="modal-body">{editId ? 'Update personnel record?' : 'Save new personnel record?'}</div><div className="modal-footer"><button className="btn btn-secondary" onClick={()=>setConfirmAdd(false)}>Cancel</button><button className="btn btn-primary" onClick={()=>{ setConfirmAdd(false); doSubmit(); }}>Yes, Save</button></div></div></div></div>
      )}

    </div>
  )
}
