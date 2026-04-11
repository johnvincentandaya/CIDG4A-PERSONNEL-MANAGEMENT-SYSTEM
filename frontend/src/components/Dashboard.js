import React, { useEffect, useMemo, useState, useContext } from 'react';
import { api } from '../api';
import { RefreshContext } from '../contexts/RefreshContext';

const UNITS = ['RHQ', 'Cavite', 'Laguna', 'Batangas', 'Rizal', 'Quezon'];

export default function Dashboard() {
  const [counts, setCounts] = useState({});
  const [bmiCounts, setBmiCounts] = useState({});
  const [loadError, setLoadError] = useState('');

  const { version } = useContext(RefreshContext);

  useEffect(() => {
    api
      .get('/api/personnel/counts')
      .then(r => setCounts(r.data))
      .catch((err) => {
        console.error('Failed to load personnel counts', err);
        setLoadError('Unable to load dashboard counts. Please refresh.');
      });
    
    api
      .get('/api/bmi/counts')
      .then(r => setBmiCounts(r.data))
      .catch((err) => {
        console.error('Failed to load BMI counts', err);
        setLoadError('Unable to load dashboard counts. Please refresh.');
      });
  }, [version]);

  const totalPersonnel = useMemo(
    () => counts.total ?? UNITS.reduce((sum, u) => sum + (counts[u] || 0), 0),
    [counts]
  );

  const totalBMIInputs = useMemo(
    () => bmiCounts.total ?? UNITS.reduce((sum, u) => sum + (bmiCounts[u]?.total || 0), 0),
    [bmiCounts]
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
        {loadError && (
          <div className="alert alert-warning mb-2" role="alert">{loadError}</div>
        )}
        <div className="stat-card">
          <div className="stat-card-label">Form 201 Inputs</div>
          <div className="stat-card-value">{totalPersonnel}</div>
          <div className="stat-card-meta">Total Form 201 records encoded</div>
        </div>
        {/* Active Units card removed per spec */}
        <div className="stat-card">
          <div className="stat-card-label">BMI Inputs</div>
          <div className="stat-card-value">{totalBMIInputs}</div>
          <div className="stat-card-meta">Total BMI records encoded</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">BMI Records (Month)</div>
          <div className="stat-card-value">{bmiCounts.total_monthly || 0}</div>
          <div className="stat-card-meta">Monitoring coverage this month</div>
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
                <div className="metric-list-value">{bmiCounts[u]?.monthly || 0} records</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
