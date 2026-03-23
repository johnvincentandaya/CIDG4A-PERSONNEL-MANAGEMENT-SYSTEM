import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../api';

const UNITS = ['RHQ', 'Cavite', 'Laguna', 'Batangas', 'Rizal', 'Quezon'];

export default function Dashboard() {
  const [counts, setCounts] = useState({});
  const [orgChartError, setOrgChartError] = useState(false);

  useEffect(() => {
    api
      .get('/api/personnel/counts')
      .then(r => setCounts(r.data))
      .catch(() => {});
  }, []);

  const totalPersonnel = useMemo(
    () => UNITS.reduce((sum, u) => sum + (counts[u] || 0), 0),
    [counts]
  );

  return (
    <div>
      <div className="page-header"> 
        <div className="page-title-block">
          <div className="page-eyebrow">CIDG RFU4A</div>
          <h1 className="page-title">Personnel Management Overview</h1>
          <p className="page-subtitle">
            Executive view of personnel strength and health monitoring across all CIDG RFU4A units.
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn-quiet">
            <i className="bi bi-download" />
            Export Snapshot
          </button>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-card-label">Total Personnel</div>
          <div className="stat-card-value">{totalPersonnel}</div>
          <div className="stat-card-meta">Across all RFU4A units</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Active Units</div>
          <div className="stat-card-value">{UNITS.length}</div>
          <div className="stat-card-meta">RHQ and 5 provincial offices</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">BMI Records (Month)</div>
          <div className="stat-card-value">0</div>
          <div className="stat-card-meta">Monitoring coverage this month</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Compliance Status</div>
          <div className="stat-card-value">On Track</div>
          <div className="stat-card-meta">Based on latest records</div>
        </div>
      </div>

      <div className="row g-3">
        <div className="col-12 col-lg-8">
          <div className="card-elevated mb-3">
            <div className="p-3 border-bottom border-light">
              <div className="section-title">Command Briefing</div>
              <div className="d-flex justify-content-between align-items-center">
                <div className="text-muted small">
                  Audio-visual presentation of CIDG RFU4A.
                </div>
              </div>
            </div>
            <div className="p-3">
              <div className="ratio ratio-16x9">
                <iframe
                  src="https://www.youtube.com/embed/9wHgCvwvwKY"
                  title="CIDG RFU4A AVP"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                ></iframe>
              </div>
            </div>
          </div>

          <div className="mission-vision-grid mb-3">
            <div className="card-section">
              <div className="section-title">CIDG MISSION</div>
              <h4>CIDG Mission</h4>
              <p>
                Enforce the law, prevent and control crimes, maintain peace and order,
                and ensure public safety and internal security with the active support
                of the community.
              </p>
            </div>
            <div className="card-section">
              <div className="section-title">CIDG VISION</div>
              <h4>CIDG Vision</h4>
              <p>
                By 2031, the CIDG will be a dynamic, responsive and well-equipped agency
                manned by the most qualified and highly-motivated professionals in search
                of truth and justice.
              </p>
            </div>
          </div>

          <div className="card-section p-3">
            <div className="section-title">Organizational Structure</div>
            <div className="text-muted small mb-3">
              Visual representation of RFU4A organizational structure can be integrated here for quick reference.
            </div>
            <div className="text-center">
              {!orgChartError ? (
                <img
                  src="/cidg-org-chart.png"
                  alt="CIDG RFU4A Organizational Chart"
                  className="img-fluid rounded"
                  style={{ maxHeight: '500px', objectFit: 'contain' }}
                  onError={() => setOrgChartError(true)}
                />
              ) : (
                <div className="border rounded-3 p-3 text-muted small" style={{ borderStyle: 'dashed' }}>
                  Organizational chart image not found. Add your file to
                  <code className="ms-1">frontend/public/cidg-org-chart.png</code>
                  and refresh the page.
                </div>
              )}
            </div>
          </div>  
        </div>

        <div className="col-12 col-lg-4">
          <div className="card-section p-3 mb-3">
            <div className="section-title">Personnel by Unit</div>
            {UNITS.map(u => (
              <div key={u} className="metric-list-row">
                <div className="metric-list-label">{u}</div>
                <div className="metric-list-value">{counts[u] ?? 0}</div>
              </div>
            ))}
          </div>

          <div className="card-section p-3">
            <div className="section-title">BMI Monitoring (This Month)</div>
            {UNITS.map(u => (
              <div key={u} className="metric-list-row">
                <div className="metric-list-label">{u}</div>
                <div className="metric-list-value text-muted">0 records</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
