import React, {useEffect, useState} from 'react';
import axios from 'axios';

export default function Dashboard(){
  const [counts, setCounts] = useState({});
  useEffect(()=>{
    axios.get('http://localhost:8000/api/personnel/counts').then(r=>setCounts(r.data)).catch(()=>{});
  },[]);
  const units = ['RHQ','Cavite','Laguna','Batangas','Rizal','Quezon'];
  return (
    <div>
      <h3>CRIMINAL INVESTIGATION AND DETECTION GROUP REGION 4A</h3>
      <p>Welcome to CIDG RFU4A Personnel Management System</p>
      <div className="row">
        <div className="col-12 col-lg-8">
          <div className="card mb-3">
            <div className="card-body">Audio-Visual Presentation (placeholder)</div>
          </div>
          <div className="card mb-3">
            <div className="card-body">Organizational Chart (placeholder)</div>
          </div>
          <div className="d-flex gap-3">
            <div className="card flex-fill bg-primary text-white p-3">Mission</div>
            <div className="card flex-fill bg-secondary text-white p-3">Vision</div>
          </div>
        </div>
        <div className="col-12 col-lg-4">
          <div className="card p-3 mb-3">
            <h6>Total Personnel per Unit</h6>
            {units.map(u=> (
              <div key={u} className="d-flex justify-content-between py-2 border-bottom">
                <div>{u}</div>
                <div className="fw-bold">{counts[u] ?? 0}</div>
              </div>
            ))}
          </div>
          <div className="card p-3">
            <h6>BMI Records This Month per Unit</h6>
            {units.map(u=> (
              <div key={u} className="d-flex justify-content-between py-2 border-bottom">
                <div>{u}</div>
                <div className="fw-bold">0</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
