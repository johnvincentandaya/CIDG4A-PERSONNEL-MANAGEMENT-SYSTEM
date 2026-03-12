import React, {useEffect, useState} from 'react';
import axios from 'axios';

export default function BMIMonitor(){
  const [records, setRecords] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({rank:'', name:'', unit:'RHQ', age:'', sex:'Male', height_cm:'', weight_kg:'', waist_cm:'', hip_cm:'', wrist_cm:'', date_taken: ''});
  const [front, setFront] = useState(null);
  const [left, setLeft] = useState(null);
  const [right, setRight] = useState(null);

  useEffect(()=>{ load(); },[])
  function load(){ axios.get('http://localhost:8000/api/bmi/').then(r=>setRecords(r.data)).catch(()=>{}); }

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
      await axios.post('http://localhost:8000/api/bmi/', data, { headers: {'Content-Type':'multipart/form-data'} });
      setShowModal(false);
      load();
    }catch(err){
      alert('Error saving BMI record: '+ (err.response?.data?.detail || err.message));
    }
  }

  return (
    <div>
      <h3>BMI Monitoring</h3>
      <p>Track and monitor Body Mass Index records</p>
      <div className="card p-3">
        <div className="d-flex justify-content-between mb-3">
          <div className="d-flex gap-2">
            <select className="form-select"><option>All Units</option></select>
            <select className="form-select"><option>All Months</option></select>
            <select className="form-select"><option>All Years</option></select>
          </div>
          <div>
            <button className="btn btn-outline-secondary me-2">Generate Report</button>
            <button className="btn btn-primary" onClick={openNew}>+ New Record</button>
          </div>
        </div>
        <div style={{overflow:'auto'}}>
          <table className="table table-striped">
            <thead><tr><th>Rank</th><th>Name</th><th>Unit</th><th>Age</th><th>Height (cm)</th><th>Weight (kg)</th><th>BMI</th><th>Result</th><th>Classification</th><th>Date Taken</th><th>Actions</th></tr></thead>
            <tbody>
              {records.map(r=> (
                <tr key={r.id}><td>{r.rank}</td><td>{r.name}</td><td>{r.unit}</td><td>{r.age}</td><td>{r.height_cm}</td><td>{r.weight_kg}</td><td>{r.bmi}</td><td>{r.result}</td><td>{r.classification}</td><td>{r.date_taken ? new Date(r.date_taken).toLocaleDateString(): ''}</td><td><button className="btn btn-sm btn-outline-primary">Edit</button></td></tr>
              ))}
            </tbody>
          </table>
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
                  <div className="col-md-4"><label>Rank *</label><input className="form-control" value={form.rank} onChange={e=>setForm({...form,rank:e.target.value})} /></div>
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
