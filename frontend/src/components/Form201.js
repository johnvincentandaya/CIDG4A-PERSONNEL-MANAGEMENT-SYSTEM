import React, {useEffect, useState, useContext} from 'react';
import { api, absolutizePath } from '../api';
import { RANKS } from '../constants/ranks';
import { RefreshContext } from '../contexts/RefreshContext';

const UNITS = ['RHQ','Cavite','Laguna','Batangas','Rizal','Quezon'];
const STATUS = ['Active','Inactive','Reassign','Retired','Others'];
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
  const [form, setForm] = useState({
    rank:'',
    badge_number:'',
    last_name:'',
    first_name:'',
    mi:'',
    suffix:'',
    unit:'RHQ',
    status:'Active',
    status_custom:'',
    nup_rank:'',
    nup_entry_number:'',
    qlf:'',
    date_of_reassignment:'',
    designation:'',
    date_of_designation:'',
    highest_eligibility:'',
    contact_number:'',
    birthdate:'',
    religion:'',
    section:''
  });

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
  const [reportFileName, setReportFileName] = useState('');
  const [reportScope, setReportScope] = useState('Overall');
  const [reportSpecificUnit, setReportSpecificUnit] = useState('RHQ');
  const [reportAsOfDate, setReportAsOfDate] = useState(new Date().toISOString().slice(0,10));
  const [preparedByName, setPreparedByName] = useState('');
  const [preparedByTitle, setPreparedByTitle] = useState('');
  const [preparedBySignature, setPreparedBySignature] = useState(null);
  const [verifiedByName, setVerifiedByName] = useState('');
  const [verifiedByTitle, setVerifiedByTitle] = useState('');
  const [verifiedBySignature, setVerifiedBySignature] = useState(null);
  const [notedByName, setNotedByName] = useState('');
  const [notedByTitle, setNotedByTitle] = useState('');
  const [notedBySignature, setNotedBySignature] = useState(null);
  
  // AUT Values - PCO inputs
  const [autPMGEN, setAutPMGEN] = useState('1');
  const [autPBGEN, setAutPBGEN] = useState('1');
  const [autPCOL, setAutPCOL] = useState('2');
  const [autPLTCOL, setAutPLTCOL] = useState('3');
  const [autPMAJ, setAutPMAJ] = useState('4');
  const [autPCPT, setAutPCPT] = useState('5');
  const [autPLT, setAutPLT] = useState('6');
  const [autPCOSubtotal, setAutPCOSubtotal] = useState('22');
  
  // AUT Values - PNCO inputs
  const [autPEMS, setAutPEMS] = useState('1');
  const [autPCMS, setAutPCMS] = useState('2');
  const [autPSMS, setAutPSMS] = useState('3');
  const [autPMSG, setAutPMSG] = useState('4');
  const [autPSSG, setAutPSSG] = useState('5');
  const [autPCPL, setAutPCPL] = useState('6');
  const [autPAT, setAutPAT] = useState('7');
  const [autPNCOSubtotal, setAutPNCOSubtotal] = useState('28');
  
  // AUT Values - NUP input
  const [autNUP, setAutNUP] = useState('10');
  
  // AUT Values - Totals
  const [autTotalPersonnel, setAutTotalPersonnel] = useState('60');
  const [autTotalUniformed, setAutTotalUniformed] = useState('50');
  
  const [reportModalTab, setReportModalTab] = useState('report');

  const { bump } = useContext(RefreshContext);

  useEffect(()=>{ load() },[])
  function load(){ api.get('/api/personnel/').then(r=>setRecords(r.data)).catch(()=>{}); }

  function resetModal(){
    setForm({
      rank:'', badge_number:'', last_name:'', first_name:'', mi:'', suffix:'', unit:'RHQ', status:'Active', status_custom:'', nup_rank:'', nup_entry_number:'', qlf:'', date_of_reassignment:'', designation:'', date_of_designation:'', highest_eligibility:'', contact_number:'', birthdate:'', religion:'', section:''
    });
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
  function validateImage(file){
    if (!file) return null;
    const max = 5 * 1024 * 1024;
    const type = file.type || '';
    if (!type.startsWith('image/')) {
      alert('Unsupported signature file type. Please upload an image.');
      return null;
    }
    if (file.size > max) {
      alert('Signature file too large. Max 5MB.');
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
      setForm({
        rank:p.rank||'',
        badge_number:p.badge_number||'',
        last_name:p.last_name||'',
        first_name:p.first_name||'',
        mi:p.mi||'',
        suffix:p.suffix||'',
        unit:p.unit||'RHQ',
        status:p.status||'Active',
        status_custom:p.status_custom||'',
        nup_rank:p.nup_rank||'',
        nup_entry_number:p.nup_entry_number||'',
        qlf:p.qlf||'',
        date_of_reassignment:p.date_of_reassignment||'',
        designation:p.designation||'',
        date_of_designation:p.date_of_designation||'',
        highest_eligibility:p.highest_eligibility||'',
        contact_number:p.contact_number||'',
        birthdate:p.birthdate||'',
        religion:p.religion||'',
        section:p.section||''
      });
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

  function checkRequiredPersonal(){ 
    const basic = form.rank && form.last_name && form.first_name && form.birthdate && form.religion;
    if (!basic) return false;
    // If rank is NUP, require NUP-specific fields
    if ((form.rank || '').toUpperCase() === 'NUP') {
      if (!form.nup_rank || !form.nup_entry_number) return false;
    }
    return true;
  }

  function checkRequiredDocs(){
    return true;
  }

  async function doSubmit(){
    const data = new FormData();
    data.append('rank', form.rank);
    if (form.badge_number) data.append('badge_number', form.badge_number);
    data.append('last_name', form.last_name);
    data.append('first_name', form.first_name);
    data.append('mi', form.mi || '');
    data.append('suffix', form.suffix || '');
    data.append('unit', form.unit);
    data.append('status', form.status);
    if (form.status === 'Others' && form.status_custom) data.append('status_custom', form.status_custom);
    if (form.nup_rank) data.append('nup_rank', form.nup_rank);
    if (form.nup_entry_number) data.append('nup_entry_number', form.nup_entry_number);
    if (form.qlf) data.append('qlf', form.qlf);
    if (form.date_of_reassignment) data.append('date_of_reassignment', form.date_of_reassignment);
    if (form.designation) data.append('designation', form.designation);
    if (form.date_of_designation) data.append('date_of_designation', form.date_of_designation);
    if (form.highest_eligibility) data.append('highest_eligibility', form.highest_eligibility);
    if (form.contact_number) data.append('contact_number', form.contact_number);
    if (form.birthdate) data.append('birthdate', form.birthdate);
    if (form.religion) data.append('religion', form.religion);
    if (form.section) data.append('section', form.section);
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
      // notify other pages (Dashboard) to refresh
      try{ if (bump) bump(); }catch(e){}
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
                  <th>Badge No.</th>
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
                    <td colSpan={11}>
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
                      <td>{r.badge_number || 'N/A'}</td>
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
                <div className="small text-muted mb-2">Fields marked with * are required.</div>
                <ul className="nav nav-tabs mb-3">
                  <li className="nav-item"><button className={`nav-link ${activeTab==='personal' ? 'active':''}`} onClick={()=>setActiveTab('personal')}>Personal Information</button></li>
                  <li className="nav-item"><button className={`nav-link ${activeTab==='documents' ? 'active':''}`} onClick={()=>setActiveTab('documents')}>Documents (13 Required)</button></li>
                </ul>
                {activeTab==='personal' && (
                  <div>
                    <div className="row">
                      <div className="col-md-4 mb-2">
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

                      <div className="col-md-4 mb-2"><label>Badge Number</label><input className="form-control" value={form.badge_number} onChange={e=>setForm({...form,badge_number:e.target.value})} /></div>

                      <div className="col-md-4 mb-2"><label>Unit</label><select className="form-select" value={form.unit} onChange={e=>setForm({...form,unit:e.target.value})}>{UNITS.map(u=> <option key={u}>{u}</option>)}</select></div>

                      <div className="col-md-4 mb-2"><label>Last Name *</label><input className="form-control" value={form.last_name} onChange={e=>setForm({...form,last_name:e.target.value})} /></div>
                      <div className="col-md-4 mb-2"><label>First Name *</label><input className="form-control" value={form.first_name} onChange={e=>setForm({...form,first_name:e.target.value})} /></div>
                      <div className="col-md-4 mb-2"><label>M.I.</label><input className="form-control" value={form.mi} onChange={e=>setForm({...form,mi:e.target.value})} /></div>

                      <div className="col-md-3 mb-2"><label>Suffix</label><input className="form-control" value={form.suffix} onChange={e=>setForm({...form,suffix:e.target.value})} /></div>
                      <div className="col-md-3 mb-2"><label>QLF</label><input className="form-control" value={form.qlf} onChange={e=>setForm({...form,qlf:e.target.value})} /></div>
                      <div className="col-md-3 mb-2"><label>Birthdate *</label><input type="date" className="form-control" value={form.birthdate} onChange={e=>setForm({...form,birthdate:e.target.value})} /></div>
                      <div className="col-md-3 mb-2"><label>Religion *</label><input className="form-control" value={form.religion} onChange={e=>setForm({...form,religion:e.target.value})} /></div>

                      <div className="col-md-4 mb-2"><label>Designation</label><input className="form-control" value={form.designation} onChange={e=>setForm({...form,designation:e.target.value})} /></div>
                      <div className="col-md-4 mb-2"><label>Date of Designation</label><input type="date" className="form-control" value={form.date_of_designation} onChange={e=>setForm({...form,date_of_designation:e.target.value})} /></div>
                      <div className="col-md-4 mb-2"><label>Date of Reassignment</label><input type="date" className="form-control" value={form.date_of_reassignment} onChange={e=>setForm({...form,date_of_reassignment:e.target.value})} /></div>

                      <div className="col-md-4 mb-2"><label>Highest Eligibility</label><input className="form-control" value={form.highest_eligibility} onChange={e=>setForm({...form,highest_eligibility:e.target.value})} /></div>
                      <div className="col-md-4 mb-2"><label>Contact Number</label><input className="form-control" value={form.contact_number} onChange={e=>setForm({...form,contact_number:e.target.value})} /></div>
                      <div className="col-md-4 mb-2">
                        { (form.unit === 'RHQ' || form.unit === 'Headquarters') ? (
                          <>
                            <label>Section</label>
                            <select className="form-select" value={form.section} onChange={e=>setForm({...form,section:e.target.value})}>
                              <option value="">Office of the Regional Chief</option>
                              <option>Office of the Regional Chief</option>
                              <option>Admin and HRDD Section</option>
                              <option>Intelligence Section</option>
                              <option>Investigation Section</option>
                              <option>Operation &amp; PCR Section</option>
                            </select>
                          </>
                        ) : null }
                      </div>
                      <div className="col-md-8 mb-2"><label>Status</label><select className="form-select" value={form.status} onChange={e=>setForm({...form,status:e.target.value})}>{STATUS.map(s=> <option key={s}>{s}</option>)}</select></div>
                      { form.status === 'Others' && (
                        <div className="col-md-12 mb-2"><label>Specify Status</label><input className="form-control" value={form.status_custom} onChange={e=>setForm({...form,status_custom:e.target.value})} /></div>
                      )}
                      { form.rank === 'NUP' && (
                        <>
                          <div className="col-md-6 mb-2"><label>NUP Rank *</label><input className="form-control" value={form.nup_rank} onChange={e=>setForm({...form,nup_rank:e.target.value})} /></div>
                          <div className="col-md-6 mb-2"><label>Entry Number *</label><input className="form-control" type="number" value={form.nup_entry_number} onChange={e=>setForm({...form,nup_entry_number:e.target.value})} /></div>
                        </>
                      )}
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
            <div className="modal-dialog modal-lg">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Generate Form 201 Report</h5>
                  <button className="btn-close" onClick={()=>setShowReportModal(false)}></button>
                </div>
                <div className="modal-body">
                  <ul className="nav nav-tabs mb-3">
                    <li className="nav-item"><button className={`nav-link ${reportModalTab==='report'? 'active':''}`} onClick={()=>setReportModalTab('report')}>Report</button></li>
                    <li className="nav-item"><button className={`nav-link ${reportModalTab==='auth'? 'active':''}`} onClick={()=>setReportModalTab('auth')}>Authorized Values</button></li>
                  </ul>

                  {reportModalTab === 'report' && (
                    <div className="row">
                      <div className="col-md-6">
                        <div className="mb-2">
                          <label>Enter File Name</label>
                          <input className="form-control" value={reportFileName} onChange={e=>setReportFileName(e.target.value)} placeholder="Filename (no extension)" />
                          <div className="small text-muted mt-1">Filename will be used for the downloaded Excel file.</div>
                        </div>

                        <div className="mb-2">
                          <label>Scope</label>
                          <select className="form-select" value={reportScope} onChange={e=>setReportScope(e.target.value)}>
                            <option>Overall</option>
                            <option>RHQ only</option>
                            <option>Specific Unit</option>
                          </select>
                        </div>

                        {reportScope === 'Specific Unit' && (
                          <div className="mb-2">
                            <label>Specific Unit</label>
                            <select className="form-select" value={reportSpecificUnit} onChange={e=>setReportSpecificUnit(e.target.value)}>
                              {UNITS.map(u=> <option key={u} value={u}>{u}</option>)}
                            </select>
                          </div>
                        )}

                        <div className="mb-2">
                          <label>As-of Date</label>
                          <input type="date" className="form-control" value={reportAsOfDate} onChange={e=>setReportAsOfDate(e.target.value)} />
                        </div>
                        <div className="small text-muted">Current filters (Unit / Status) will be sent with the report if set.</div>
                      </div>

                      <div className="col-md-6">
                        <div className="mb-2">
                          <label>Prepared By</label>
                          <input className="form-control mb-1" placeholder="Name" value={preparedByName} onChange={e=>setPreparedByName(e.target.value)} />
                          <input className="form-control mb-1" placeholder="Title" value={preparedByTitle} onChange={e=>setPreparedByTitle(e.target.value)} />
                          <input type="file" accept="image/*" className="form-control" onChange={e=>setPreparedBySignature(validateImage(e.target.files?.[0] || null))} />
                        </div>

                        <div className="mb-2">
                          <label>Verified By</label>
                          <input className="form-control mb-1" placeholder="Name" value={verifiedByName} onChange={e=>setVerifiedByName(e.target.value)} />
                          <input className="form-control mb-1" placeholder="Title" value={verifiedByTitle} onChange={e=>setVerifiedByTitle(e.target.value)} />
                          <input type="file" accept="image/*" className="form-control" onChange={e=>setVerifiedBySignature(validateImage(e.target.files?.[0] || null))} />
                        </div>

                        <div className="mb-2">
                          <label>Noted By</label>
                          <input className="form-control mb-1" placeholder="Name" value={notedByName} onChange={e=>setNotedByName(e.target.value)} />
                          <input className="form-control mb-1" placeholder="Title" value={notedByTitle} onChange={e=>setNotedByTitle(e.target.value)} />
                          <input type="file" accept="image/*" className="form-control" onChange={e=>setNotedBySignature(validateImage(e.target.files?.[0] || null))} />
                        </div>
                      </div>
                    </div>
                  )}

                  {reportModalTab === 'auth' && (
                    <div className="row">
                      <div className="col-md-6">
                        <h6 className="fw-bold mb-2">PCO AUT Inputs</h6>
                        <div className="row g-2">
                          <div className="col-6"><label className="small">PMGEN</label><input type="number" className="form-control form-control-sm" value={autPMGEN} onChange={e=>setAutPMGEN(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PBGEN</label><input type="number" className="form-control form-control-sm" value={autPBGEN} onChange={e=>setAutPBGEN(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PCOL</label><input type="number" className="form-control form-control-sm" value={autPCOL} onChange={e=>setAutPCOL(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PLTCOL</label><input type="number" className="form-control form-control-sm" value={autPLTCOL} onChange={e=>setAutPLTCOL(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PMAJ</label><input type="number" className="form-control form-control-sm" value={autPMAJ} onChange={e=>setAutPMAJ(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PCPT</label><input type="number" className="form-control form-control-sm" value={autPCPT} onChange={e=>setAutPCPT(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PLT</label><input type="number" className="form-control form-control-sm" value={autPLT} onChange={e=>setAutPLT(e.target.value)} /></div>
                          <div className="col-6"><label className="small fw-bold">Subtotal PCO</label><input type="number" className="form-control form-control-sm fw-bold" value={autPCOSubtotal} onChange={e=>setAutPCOSubtotal(e.target.value)} /></div>
                        </div>
                        
                        <h6 className="fw-bold mb-2 mt-3">NUP AUT Input</h6>
                        <div className="row g-2">
                          <div className="col-6"><label className="small">NUP</label><input type="number" className="form-control form-control-sm" value={autNUP} onChange={e=>setAutNUP(e.target.value)} /></div>
                        </div>
                      </div>
                      
                      <div className="col-md-6">
                        <h6 className="fw-bold mb-2">PNCO AUT Inputs</h6>
                        <div className="row g-2">
                          <div className="col-6"><label className="small">PEMS</label><input type="number" className="form-control form-control-sm" value={autPEMS} onChange={e=>setAutPEMS(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PCMS</label><input type="number" className="form-control form-control-sm" value={autPCMS} onChange={e=>setAutPCMS(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PSMS</label><input type="number" className="form-control form-control-sm" value={autPSMS} onChange={e=>setAutPSMS(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PMSG</label><input type="number" className="form-control form-control-sm" value={autPMSG} onChange={e=>setAutPMSG(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PSSG</label><input type="number" className="form-control form-control-sm" value={autPSSG} onChange={e=>setAutPSSG(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PCPL</label><input type="number" className="form-control form-control-sm" value={autPCPL} onChange={e=>setAutPCPL(e.target.value)} /></div>
                          <div className="col-6"><label className="small">PAT</label><input type="number" className="form-control form-control-sm" value={autPAT} onChange={e=>setAutPAT(e.target.value)} /></div>
                          <div className="col-6"><label className="small fw-bold">Subtotal PNCO</label><input type="number" className="form-control form-control-sm fw-bold" value={autPNCOSubtotal} onChange={e=>setAutPNCOSubtotal(e.target.value)} /></div>
                        </div>
                        
                        <h6 className="fw-bold mb-2 mt-3">Totals AUT Inputs</h6>
                        <div className="row g-2">
                          <div className="col-6"><label className="small">Total Personnel</label><input type="number" className="form-control form-control-sm" value={autTotalPersonnel} onChange={e=>setAutTotalPersonnel(e.target.value)} /></div>
                          <div className="col-6"><label className="small">Total Uniformed Personnel</label><input type="number" className="form-control form-control-sm" value={autTotalUniformed} onChange={e=>setAutTotalUniformed(e.target.value)} /></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button className="btn btn-secondary" onClick={()=>setShowReportModal(false)}>Cancel</button>
                  <button className="btn btn-primary" disabled={!reportFileName.trim()} onClick={async ()=>{
                    try{
                      const fd = new FormData();
                      fd.append('file_name', reportFileName.trim());
                      fd.append('report_type', 'excel');
                      // include current filters
                      if (unitFilter && unitFilter !== 'All Units') fd.append('unit', unitFilter);
                      if (statusFilter && statusFilter !== 'All Status') fd.append('status', statusFilter);
                      // scope and specific unit
                      if (reportScope) fd.append('scope', reportScope);
                      if (reportScope === 'Specific Unit' && reportSpecificUnit) fd.append('specific_unit', reportSpecificUnit);
                      if (reportAsOfDate) fd.append('as_of_date', reportAsOfDate);
                      // signatories
                      if (preparedByName) fd.append('prepared_by_name', preparedByName);
                      if (preparedByTitle) fd.append('prepared_by_title', preparedByTitle);
                      if (preparedBySignature) fd.append('prepared_by_signature', preparedBySignature);
                      if (verifiedByName) fd.append('verified_by_name', verifiedByName);
                      if (verifiedByTitle) fd.append('verified_by_title', verifiedByTitle);
                      if (verifiedBySignature) fd.append('verified_by_signature', verifiedBySignature);
                      if (notedByName) fd.append('noted_by_name', notedByName);
                      if (notedByTitle) fd.append('noted_by_title', notedByTitle);
                      if (notedBySignature) fd.append('noted_by_signature', notedBySignature);
                      // authorized values (AUT) from modal
                      const authData = {
                        PCO: {
                          PMGEN: autPMGEN,
                          PBGEN: autPBGEN,
                          PCOL: autPCOL,
                          PLTCOL: autPLTCOL,
                          PMAJ: autPMAJ,
                          PCPT: autPCPT,
                          PLT: autPLT,
                          Subtotal: autPCOSubtotal
                        },
                        PNCO: {
                          PEMS: autPEMS,
                          PCMS: autPCMS,
                          PSMS: autPSMS,
                          PMSG: autPMSG,
                          PSSG: autPSSG,
                          PCPL: autPCPL,
                          PAT: autPAT,
                          Subtotal: autPNCOSubtotal
                        },
                        NUP: autNUP,
                        Totals: {
                          TotalPersonnel: autTotalPersonnel,
                          TotalUniformed: autTotalUniformed
                        }
                      };
                      fd.append('authorized_values', JSON.stringify(authData));

                      const res = await api.post('/api/personnel/report', fd, { responseType: 'blob' });
                      const disposition = res.headers && (res.headers['content-disposition'] || res.headers['Content-Disposition']);
                      let filename = '';
                      if (disposition) {
                        const m = disposition.match(/filename=(?:")?([^;\"]+)/i);
                        if (m && m[1]) filename = m[1].trim();
                      }
                      if (!filename) filename = `${reportFileName.trim()}.xlsx`;
                      const url = window.URL.createObjectURL(new Blob([res.data]));
                      const a = document.createElement('a');
                      a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
                      setShowReportModal(false);
                    }catch(err){
                      alert('Error generating report');
                    }
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
