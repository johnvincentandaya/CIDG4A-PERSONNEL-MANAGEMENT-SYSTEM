import React, {useEffect, useState} from 'react';
import { api, absolutizePath } from '../api';
import { RANKS } from '../constants/ranks';

const UNITS = ['RHQ','Cavite','Laguna','Batangas','Rizal','Quezon'];
const STATUS = ['Active','Reassigned','Retired'];
const ALLOWED_FILE_EXTENSIONS = ['pdf', 'doc', 'docx'];
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;
const FILE_ACCEPT_ATTR = '.pdf,.doc,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword';

const DOC_FIELDS = [
  { key: 'pds', label: 'a. CSC PDS Revised 2025 and Personal History Statement' },
  { key: 'appointment', label: 'b. Appointment Order and CSC Attested Appointment' },
  { key: 'promotion', label: 'c. Promotion Orders and CSC Attested Appointments' },
  { key: 'designation', label: 'd. Designation Orders' },
  { key: 'reassignment', label: 'e. Reassignment Orders' },
  { key: 'diploma', label: 'f. Diploma / Transcript of Records' },
  { key: 'eligibility', label: 'g. Eligibility' },
  { key: 'iper', label: 'j. IPER' },
  { key: 'saln', label: 'k. SALN' },
  { key: 'pft', label: 'l. PFT Results' },
  { key: 'rca', label: 'm. RCA, Long Pay, Suspension, and Other Orders' },
];

function TrainingInput({entries, setEntries, category, validateFile}){
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
          <input
            type="file"
            accept={FILE_ACCEPT_ATTR}
            onChange={ev=>{
              const nextFile = ev.target.files?.[0] || null;
              const validated = validateFile(nextFile);
              if (!validated && nextFile) {
                ev.target.value = '';
              }
              update(i,'file', validated);
            }}
          />
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
  const [deleteDocTypes, setDeleteDocTypes] = useState([]);
  const [deleteMandatoryIds, setDeleteMandatoryIds] = useState([]);
  const [deleteSpecializedIds, setDeleteSpecializedIds] = useState([]);
  const [docStatus, setDocStatus] = useState({});
  const [previewOpen, setPreviewOpen] = useState({});

  // filters
  const [unitFilter, setUnitFilter] = useState('All Units');
  const [statusFilter, setStatusFilter] = useState('All Status');
  const [search, setSearch] = useState('');
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportUnit, setReportUnit] = useState('All Units');
  const [reportStatus, setReportStatus] = useState('All Status');

  useEffect(()=>{ load() },[])
  function load(){ api.get('/api/personnel/').then(r=>setRecords(r.data)).catch(()=>{}); }

  function resetModal(){
    setForm({rank:'',last_name:'',first_name:'',mi:'',suffix:'',unit:'RHQ',status:'Active'});
    setPds(null); setAppointment(null); setPromotion(null); setDesignation(null); setReassignment(null); setDiploma(null); setEligibility(null); setIper(null); setSaln(null); setPft(null); setRca(null);
    setPdsExisting(null); setAppointmentExisting(null); setPromotionExisting(null); setDesignationExisting(null); setReassignmentExisting(null); setDiplomaExisting(null); setEligibilityExisting(null); setIperExisting(null); setSalnExisting(null); setPftExisting(null); setRcaExisting(null);
    setMandatory([{title:'', file:null}]); setSpecialized([{title:'', file:null}]);
    setMandatoryExisting([]); setSpecializedExisting([]); setDeleteDocTypes([]); setDeleteMandatoryIds([]); setDeleteSpecializedIds([]);
    setDocStatus({}); setPreviewOpen({});
    setActiveTab('personal');
    setEditId(null);
  }

  function openModal(){ resetModal(); setShowModal(true); }

  function fileUrl(path){
    return absolutizePath(path);
  }

  function validateFile(file){
    if (!file) return null;
    const ext = (file.name.split('.').pop() || '').toLowerCase();
    if (!ALLOWED_FILE_EXTENSIONS.includes(ext)) {
      alert(`Unsupported file type: ${file.name}. Allowed: PDF, DOC, DOCX.`);
      return null;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      alert(`File too large: ${file.name}. Max size is 10MB.`);
      return null;
    }
    return file;
  }

  function buildExistingDoc(doc){
    if (!doc) return null;
    const filePath = doc.file_url || doc.file_path;
    const fileName = doc.file_name || (filePath ? filePath.split('/').pop() : null);
    const fileType = (doc.file_type || (fileName ? fileName.split('.').pop() : '') || '').toUpperCase();
    return {
      id: doc.id,
      docType: doc.doc_type,
      filePath,
      fileName,
      fileType,
      uploadDate: doc.upload_date,
      url: fileUrl(filePath),
    };
  }

  const docFiles = { pds, appointment, promotion, designation, reassignment, diploma, eligibility, iper, saln, pft, rca };
  const setDocFiles = {
    pds: setPds,
    appointment: setAppointment,
    promotion: setPromotion,
    designation: setDesignation,
    reassignment: setReassignment,
    diploma: setDiploma,
    eligibility: setEligibility,
    iper: setIper,
    saln: setSaln,
    pft: setPft,
    rca: setRca,
  };
  const existingDocs = {
    pds: pdsExisting,
    appointment: appointmentExisting,
    promotion: promotionExisting,
    designation: designationExisting,
    reassignment: reassignmentExisting,
    diploma: diplomaExisting,
    eligibility: eligibilityExisting,
    iper: iperExisting,
    saln: salnExisting,
    pft: pftExisting,
    rca: rcaExisting,
  };
  const setExistingDocs = {
    pds: setPdsExisting,
    appointment: setAppointmentExisting,
    promotion: setPromotionExisting,
    designation: setDesignationExisting,
    reassignment: setReassignmentExisting,
    diploma: setDiplomaExisting,
    eligibility: setEligibilityExisting,
    iper: setIperExisting,
    saln: setSalnExisting,
    pft: setPftExisting,
    rca: setRcaExisting,
  };

  function docTypeIcon(meta){
    const type = (meta?.fileType || '').toLowerCase();
    if (type === 'pdf') return 'bi-file-earmark-pdf text-danger';
    if (type === 'doc' || type === 'docx') return 'bi-file-earmark-word text-primary';
    return 'bi-file-earmark';
  }

  function getDocStatus(docKey){
    if (docStatus[docKey]) return docStatus[docKey];
    if (docFiles[docKey] && existingDocs[docKey]) return 'File replaced';
    if (docFiles[docKey] && !existingDocs[docKey]) return 'New file selected';
    if (existingDocs[docKey]) return 'File uploaded';
    return 'No file uploaded';
  }

  function statusClass(status){
    if (status === 'File replaced') return 'text-bg-warning';
    if (status === 'File uploaded') return 'text-bg-success';
    if (status === 'Removed') return 'text-bg-danger';
    return 'text-bg-secondary';
  }

  function handleSingleFileChange(docKey, selectedFile, inputEl){
    const validated = validateFile(selectedFile);
    if (!validated) {
      if (inputEl) inputEl.value = '';
      return;
    }
    const existing = existingDocs[docKey];
    if (existing && !window.confirm(`A file already exists (${existing.fileName || 'existing file'}). Replace it?`)) {
      if (inputEl) inputEl.value = '';
      return;
    }
    setDocFiles[docKey](validated);
    setDocStatus(prev => ({ ...prev, [docKey]: existing ? 'File replaced' : 'File uploaded' }));
    if (deleteDocTypes.includes(docKey)) {
      setDeleteDocTypes(prev => prev.filter(t => t !== docKey));
    }
  }

  function removeExistingDoc(docKey){
    const existing = existingDocs[docKey];
    if (!existing) return;
    const ok = window.confirm(`Remove ${existing.fileName || 'this file'}? This will delete it when you save changes.`);
    if (!ok) return;
    setExistingDocs[docKey](null);
    setDocFiles[docKey](null);
    setDeleteDocTypes(prev => (prev.includes(docKey) ? prev : [...prev, docKey]));
    setDocStatus(prev => ({ ...prev, [docKey]: 'Removed' }));
    setPreviewOpen(prev => ({ ...prev, [docKey]: false }));
  }

  async function editPerson(id){
    try{
      const res = await api.get(`/api/personnel/${id}`);
      const p = res.data;
      setEditId(id);
      setForm({rank:p.rank,last_name:p.last_name,first_name:p.first_name,mi:p.mi||'',suffix:p.suffix||'',unit:p.unit,status:p.status});
      const docs = p.documents || [];
      const map = {};
      docs.forEach(d => { map[d.doc_type] = buildExistingDoc(d); });
      setPdsExisting(map.pds || null);
      setAppointmentExisting(map.appointment || null);
      setPromotionExisting(map.promotion || null);
      setDesignationExisting(map.designation || null);
      setReassignmentExisting(map.reassignment || null);
      setDiplomaExisting(map.diploma || null);
      setEligibilityExisting(map.eligibility || null);
      setIperExisting(map.iper || null);
      setSalnExisting(map.saln || null);
      setPftExisting(map.pft || null);
      setRcaExisting(map.rca || null);
      setDocStatus({});
      setDeleteDocTypes([]);
      setPreviewOpen({});
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
    return true;
  }

  async function doSubmit(){
    const data = new FormData();
    data.append('rank', form.rank);
    data.append('last_name', form.last_name);
    data.append('first_name', form.first_name);
    data.append('mi', form.mi || '');
    data.append('suffix', form.suffix || '');
    data.append('unit', form.unit);
    data.append('status', form.status);
    let hasSingleFiles = false;
    Object.entries(docFiles).forEach(([key, value]) => {
      if (value) {
        data.append(key, value);
        hasSingleFiles = true;
      }
    });

    // trainings: append titles and files for new rows
    let hasTrainingFiles = false;
    mandatory.forEach(m => { if (m.file) { hasTrainingFiles = true; data.append('mandatory_titles', m.title); data.append('mandatory_files', m.file); } });
    specialized.forEach(s => { if (s.file) { hasTrainingFiles = true; data.append('specialized_titles', s.title); data.append('specialized_files', s.file); } });

    // include deletions if any (only relevant on edit)
    if (deleteDocTypes && deleteDocTypes.length>0) data.append('delete_doc_types', JSON.stringify(deleteDocTypes));
    if (deleteMandatoryIds && deleteMandatoryIds.length>0) data.append('delete_mandatory_ids', JSON.stringify(deleteMandatoryIds));
    if (deleteSpecializedIds && deleteSpecializedIds.length>0) data.append('delete_specialized_ids', JSON.stringify(deleteSpecializedIds));

    const hasAnyFiles = hasSingleFiles || hasTrainingFiles;

    try{
      if (editId){
        await api.put(`/api/personnel/${editId}`, data, { headers: {'Content-Type':'multipart/form-data'} });
      } else if (hasAnyFiles) {
        await api.post('/api/personnel/', data, { headers: {'Content-Type':'multipart/form-data'} });
      } else {
        // no documents selected – call basic endpoint that only expects form fields
        await api.post('/api/personnel/basic', data, { headers: {'Content-Type':'multipart/form-data'} });
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

  const filteredRecords = records.filter(r => {
    let ok = true;
    if (unitFilter !== 'All Units') {
      ok = ok && r.unit === unitFilter;
    }
    if (statusFilter !== 'All Status') {
      ok = ok && r.status === statusFilter;
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      const haystack = [
        r.rank || '',
        r.last_name || '',
        r.first_name || '',
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
            <select
              className="form-select form-select-sm"
              value={unitFilter}
              onChange={e => setUnitFilter(e.target.value)}
            >
              <option>All Units</option>
              {UNITS.map(u => <option key={u}>{u}</option>)}
            </select>
            <select
              className="form-select form-select-sm"
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
            >
              <option>All Status</option>
              {STATUS.map(s => <option key={s}>{s}</option>)}
            </select>
            <input
              className="form-control form-control-sm"
              placeholder="Search by name, rank, or unit"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div>
            <button className="btn btn-outline-secondary btn-sm me-2" onClick={()=>setShowReportModal(true)}>
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
                {filteredRecords.length === 0 && (
                  <tr>
                    <td colSpan={10}>
                      <div className="table-empty-state">
                        No personnel records found. Use the filters above or create a new record to get started.
                      </div>
                    </td>
                  </tr>
                )}
                {filteredRecords.map(r=> {
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
                    {DOC_FIELDS.map(doc => {
                      const existing = existingDocs[doc.key];
                      const selected = docFiles[doc.key];
                      const status = getDocStatus(doc.key);
                      const hasPreview = existing && existing.fileType && existing.fileType.toLowerCase() === 'pdf';
                      return (
                        <div key={doc.key} className="mb-3 p-3 border rounded" style={{background:'#f8fafc'}}>
                          <label className="fw-bold d-block mb-2">{doc.label}</label>
                          <div className="d-flex flex-wrap align-items-center gap-2 mb-2">
                            <span className={`badge ${statusClass(status)}`}>{status}</span>
                            {existing && (
                              <span className="text-muted small">
                                File already uploaded:{' '}
                                <a href={existing.url} target="_blank" rel="noreferrer">{existing.fileName || 'Open file'}</a>
                                {existing.uploadDate ? ` • ${new Date(existing.uploadDate).toLocaleString()}` : ''}
                              </span>
                            )}
                          </div>
                          <div className="d-flex flex-wrap align-items-center gap-2 mb-2">
                            <input
                              type="file"
                              accept={FILE_ACCEPT_ATTR}
                              onChange={e=>handleSingleFileChange(doc.key, e.target.files?.[0], e.target)}
                            />
                            {selected && (
                              <span className="small text-primary">
                                Selected: {selected.name}
                              </span>
                            )}
                            {existing && (
                              <>
                                <button
                                  type="button"
                                  className="btn btn-sm btn-outline-secondary"
                                  onClick={()=>{
                                    window.open(existing.url, '_blank', 'noopener,noreferrer');
                                    if (hasPreview) {
                                      setPreviewOpen(prev => ({...prev, [doc.key]: !prev[doc.key]}));
                                    }
                                  }}
                                >
                                  View
                                </button>
                                <button
                                  type="button"
                                  className="btn btn-sm btn-outline-danger"
                                  onClick={()=>removeExistingDoc(doc.key)}
                                >
                                  Remove
                                </button>
                              </>
                            )}
                          </div>
                          {existing && (
                            <div className="small text-muted d-flex align-items-center gap-2">
                              <i className={`bi ${docTypeIcon(existing)}`} />
                              <span>{existing.fileType || 'FILE'}</span>
                              <span>{existing.filePath}</span>
                            </div>
                          )}
                          {hasPreview && previewOpen[doc.key] && (
                            <div className="mt-2 p-2 border rounded bg-white">
                              <div className="small text-muted mb-1">PDF Preview</div>
                              <iframe title={`preview-${doc.key}`} src={existing.url} style={{width:'100%',height:260,border:0}} />
                            </div>
                          )}
                        </div>
                      );
                    })}

                    <div className="mb-3">
                      <strong>Existing Mandatory Trainings</strong>
                      {mandatoryExisting.map((m)=> (
                        <div key={m.id} className="d-flex gap-2 align-items-center my-2">
                          <div>{m.title}</div>
                          <a className="btn btn-sm btn-outline-secondary" href={m.url} target="_blank" rel="noreferrer">View</a>
                          <button className="btn btn-sm btn-danger" onClick={()=>{ if(window.confirm('Remove this training file?')) { setMandatoryExisting(mandatoryExisting.filter(x=>x.id!==m.id)); setDeleteMandatoryIds([...deleteMandatoryIds, m.id]); } }}>Remove</button>
                        </div>
                      ))}
                    </div>
                    <TrainingInput entries={mandatory} setEntries={setMandatory} category={'mandatory'} validateFile={validateFile} />

                    <div className="mb-3">
                      <strong>Existing Specialized Trainings</strong>
                      {specializedExisting.map((m)=> (
                        <div key={m.id} className="d-flex gap-2 align-items-center my-2">
                          <div>{m.title}</div>
                          <a className="btn btn-sm btn-outline-secondary" href={m.url} target="_blank" rel="noreferrer">View</a>
                          <button className="btn btn-sm btn-danger" onClick={()=>{ if(window.confirm('Remove this training file?')) { setSpecializedExisting(specializedExisting.filter(x=>x.id!==m.id)); setDeleteSpecializedIds([...deleteSpecializedIds, m.id]); } }}>Remove</button>
                        </div>
                      ))}
                    </div>
                    <TrainingInput entries={specialized} setEntries={setSpecialized} category={'specialized'} validateFile={validateFile} />
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={()=>setConfirmCancel(true)}>Cancel</button>
                <button className="btn btn-primary" onClick={()=>setConfirmAdd(true)} disabled={!(checkRequiredPersonal() && checkRequiredDocs())}>{editId ? 'Update Record' : 'Add Record'}</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showReportModal && (
        <div className="modal d-block" tabIndex={-1}>
          <div className="modal-dialog modal-sm">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Generate Form 201 Report</h5>
                <button className="btn-close" onClick={()=>setShowReportModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-2">
                  <label>Unit</label>
                  <select className="form-select" value={reportUnit} onChange={e=>setReportUnit(e.target.value)}>
                    <option>All Units</option>
                    {UNITS.map(u=> <option key={u}>{u}</option>)}
                  </select>
                </div>
                <div className="mb-2">
                  <label>Status</label>
                  <select className="form-select" value={reportStatus} onChange={e=>setReportStatus(e.target.value)}>
                    <option>All Status</option>
                    {STATUS.map(s=> <option key={s}>{s}</option>)}
                  </select>
                </div>
                <div className="mb-2">
                  <label>Report Type</label>
                  <select className="form-select" defaultValue="excel">
                    <option value="excel">Excel (.xlsx)</option>
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={()=>setShowReportModal(false)}>Cancel</button>
                <button className="btn btn-primary" onClick={async ()=>{
                  try{
                    const fd = new FormData();
                    fd.append('unit', reportUnit);
                    fd.append('status', reportStatus);
                    fd.append('report_type', 'excel');
                    const res = await api.post('/api/personnel/report', fd, { responseType: 'blob' });
                    const url = window.URL.createObjectURL(new Blob([res.data]));
                    const a = document.createElement('a');
                    a.href = url; a.download = 'form201_report.xlsx'; document.body.appendChild(a); a.click(); a.remove();
                    setShowReportModal(false);
                  }catch(err){ alert('Error generating report'); }
                }}>Generate</button>
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
