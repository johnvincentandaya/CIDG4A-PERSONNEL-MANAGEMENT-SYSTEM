# CIDG RFU4A Personnel Management System - Component Report

## Executive Summary

The CIDG RFU4A Personnel Management System is a web-based application designed to manage personnel records, track Form 201 document compliance, and monitor Body Mass Index (BMI) for operational fitness across CIDG Regional Field Unit 4A. The system consists of a React-based frontend and a Python FastAPI backend.

---

## Frontend Components

### 1. App.js (Root Component)
**Purpose:** Main application entry point and routing controller.

**Key Features:**
- Sets up React Router for client-side navigation
- Defines routes for Dashboard, Form 201, and BMI Monitoring pages
- Configures Bootstrap for UI styling
- Implements a sidebar layout with main content area

**Routes:**
| Path | Component | Description |
|------|-----------|-------------|
| `/` | Redirects to `/dashboard` | Default entry point |
| `/dashboard` | Dashboard | Overview statistics |
| `/form201` | Form201 | Personnel document management |
| `/bmi` | BMIMonitor | BMI tracking and monitoring |

---

### 2. Sidebar.js (Navigation Component)
**Purpose:** Provides persistent navigation sidebar throughout the application.

**Key Features:**
- Displays CIDG RFU4A branding and logo
- Navigation links with active state highlighting
- Responsive design with Bootstrap icons
- Copyright footer

**Navigation Items:**
| Icon | Label | Route |
|------|-------|-------|
| Speedometer | Dashboard | `/dashboard` |
| Folder | Form 201 Records | `/form201` |
| Activity | BMI Monitoring | `/bmi` |

---

### 3. Dashboard.js (Overview Component)
**Purpose:** Executive overview of personnel strength and health monitoring across all units.

**Key Features:**
- Total personnel count across all units
- Active units count (6 units: RHQ, Cavite, Laguna, Batangas, Rizal, Quezon)
- BMI records for current month
- Compliance status indicator
- Embedded CIDG RFU4A video presentation (YouTube)
- Mission and Vision statements
- Organizational structure chart display
- Personnel breakdown by unit
- BMI monitoring summary by unit

**Data Sources:**
- `/api/personnel/counts` - Personnel counts per unit

---

### 4. Form201.js (Personnel Records Management)
**Purpose:** Centralized registry for all CIDG RFU4A personnel Form 201 records, including document compliance tracking.

**Key Features:**

**Personnel Information Fields:**
- Rank, Last Name, First Name, Middle Initial, Suffix
- Unit Assignment (RHQ, Cavite, Laguna, Batangas, Rizal, Quezon)
- Status (Active, Reassigned, Retired)

**Required Documents (13 total):**
| Document Type | Field Key | Description |
|---------------|-----------|-------------|
| CSC PDS Revised 2025 | `pds` | Personal Data Sheet |
| Appointment Order | `appointment` | CSC Attested Appointment |
| Promotion Orders | `promotion` | Promotion and CSC Attested Appointments |
| Designation Orders | `designation` | Designation documents |
| Reassignment Orders | `reassignment` | Reassignment documents |
| Diploma/TOR | `diploma` | Educational credentials |
| Eligibility | `eligibility` | Civil Service eligibility |
| IPER | `iper` | Individual Performance Evaluation Rating |
| SALN | `saln` | Statement of Assets, Liabilities, and Net Worth |
| PFT Results | `pft` | Physical Fitness Test results |
| RCA Orders | `rca` | Reward, Corrective Action, and other orders |
| Mandatory Trainings | `mandatory` | Multiple files with titles |
| Specialized Trainings | `specialized` | Multiple files with titles |

**Functionality:**
- Add/Edit personnel records with document uploads
- File validation (PDF, DOC, DOCX only, max 10MB)
- Filter by unit, status, and search text
- Generate Form 201 reports (Excel format)
- Document preview capability
- Tabbed modal interface (Personal Info / Documents)
- Real-time document completion tracking (X/13)

---

### 5. BMIMonitor.js (BMI Monitoring Component)
**Purpose:** Monitor Body Mass Index records and compliance across CIDG RFU4A units for operational fitness.

**Key Features:**

**BMI Record Fields:**
- Rank, Name, Unit, Age, Sex
- Height (cm), Weight (kg)
- Waist (cm), Hip (cm), Wrist (cm)
- Date Taken
- Three required photos: Front, Left, Right views

**BMI Calculations:**
- **BMI Formula:** Weight(kg) / Height(m)²
- **Classification Systems:**
  - WHO Standards: Underweight (<18.5), Normal (18.5-24.9), Overweight (25-29.9), Obese (≥30)
  - PNP Age-Adjusted Standards: Age-specific acceptable BMI ranges (18.5-24.9 for 29 and below, scaling up with age)

**Intervention Packages:**
| Classification | Package | Duration | Recommendation |
|----------------|---------|----------|----------------|
| Severely Underweight | A | 48 weeks | Gain 1-3 kg/month |
| Underweight | A | 48 weeks | Gain 1-3 kg/month |
| Normal | B | 12 weeks | Maintain |
| Acceptable BMI | B | 12 weeks | Maintain |
| Overweight | C | 24 weeks | Lose 2 kg/month |
| Obese Class 1 | D | 36 weeks | Lose 2 kg/month |
| Obese Class 2 | E | 48 weeks | Lose 2 kg/month |
| Obese Class 3 | F | 60 weeks | Lose 2 kg/month |

**Functionality:**
- Add new BMI records with photo uploads
- Filter by unit, month, year, and search
- Generate BMI reports (PDF and Excel)
- Download individual BMI result PDFs
- Monthly weight monitoring table (14-month span)
- Weight metrics calculation (normal range, acceptable range, target weight)

---

### 6. api.js (API Configuration)
**Purpose:** Centralized Axios API client configuration.

**Key Features:**
- Dynamic base URL configuration based on environment
- Development: Connects to `http://localhost:8000`
- Production: Uses same origin (backend serves frontend)
- Custom environment variable support (`REACT_APP_API_BASE`)
- File URL absolutization for uploaded files

---

### 7. ranks.js (Constants)
**Purpose:** Military/Law enforcement rank definitions.

**Ranks Defined:**
```
PGen, MGen, BGen, Col, LtCol, Maj, Cpt, 1st Lt, 2nd Lt, Spy, PSP, PFC, NUP
```

---

## Backend Components

### 1. main.py (Application Entry Point)
**Purpose:** FastAPI application initialization and configuration.

**Key Features:**
- FastAPI app setup with CORS middleware
- Static file mounting for uploaded files
- Router inclusion for personnel and BMI modules
- Database initialization on startup

**CORS Configuration:**
- Allows origins from `http://localhost:3000`
- Supports all HTTP methods and headers

---

### 2. database.py (Database Configuration)
**Purpose:** SQLAlchemy database engine and session management.

**Key Features:**
- SQLite database support (default: `cidg_dev.db`)
- Environment variable support (`DATABASE_URL`)
- Thread-safe connection handling
- Database initialization function

**Configuration:**
- Default: `sqlite:///backend/cidg_dev.db`
- Configurable via `.env` file

---

### 3. models.py (Database Models)
**Purpose:** SQLAlchemy ORM model definitions.

**Models:**

#### Personnel
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| rank | String | Military/LER rank |
| last_name | String | Personnel last name |
| first_name | String | Personnel first name |
| mi | String | Middle initial |
| suffix | String | Name suffix (Jr., Sr., etc.) |
| unit | String | Assigned unit |
| status | String | Active/Reassigned/Retired |
| date_added | DateTime | Record creation timestamp |

**Relationships:**
- Documents (1-to-many)
- Training Certificates (1-to-many)
- BMI Records (1-to-many)

#### Document
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| personnel_id | Integer | Foreign key to Personnel |
| doc_type | String | Document type identifier |
| file_path | String | Server file path |

#### TrainingCertificate
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| personnel_id | Integer | Foreign key to Personnel |
| category | String | 'mandatory' or 'specialized' |
| title | String | Training certificate title |
| file_path | String | Server file path |

#### BMIRecord
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| personnel_id | Integer | Foreign key to Personnel (optional) |
| rank | String | Personnel rank |
| name | String | Full name |
| unit | String | Assigned unit |
| age | Integer | Age in years |
| sex | String | Male/Female |
| height_cm | Float | Height in centimeters |
| weight_kg | Float | Weight in kilograms |
| waist_cm | Float | Waist measurement |
| hip_cm | Float | Hip measurement |
| wrist_cm | Float | Wrist measurement |
| date_taken | DateTime | Measurement date |
| bmi | Float | Calculated BMI |
| classification | String | PNP BMI classification |
| result | String | BMI value as string |
| photo_front | String | Front photo path |
| photo_left | String | Left photo path |
| photo_right | String | Right photo path |

#### MonthlyWeight
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| bmi_record_id | Integer | Foreign key to BMIRecord |
| year | Integer | Year of measurement |
| month | Integer | Month of measurement (1-12) |
| weight | Float | Weight in kilograms |

---

### 4. schemas.py (Pydantic Schemas)
**Purpose:** Request/Response validation schemas for API endpoints.

**Schemas:**
- `DocumentSchema` - Document serialization
- `TrainingCertificateSchema` - Training certificate serialization
- `PersonnelCreate` - Personnel creation validation
- `PersonnelSchema` - Personnel serialization
- `BMICreate` - BMI record creation validation
- `BMISchema` - BMI record serialization

---

### 5. utils.py (Utility Functions)
**Purpose:** Shared utility functions for file handling.

**Functions:**
- `ensure_upload_folders()` - Create required upload directories
- `personnel_folder_name()` - Generate folder names for personnel files
- `bmi_folder_name()` - Generate folder names for BMI files
- `uploads_abs()` - Build absolute upload paths
- `uploads_rel()` - Build relative upload paths

---

### 6. api/personnel.py (Personnel API Router)
**Purpose:** REST API endpoints for personnel and document management.

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/personnel/` | List all personnel |
| GET | `/api/personnel/counts` | Get personnel counts by unit |
| GET | `/api/personnel/{person_id}` | Get single personnel record |
| GET | `/api/personnel/{person_id}/documents` | Get personnel documents |
| POST | `/api/personnel/` | Create personnel with documents |
| POST | `/api/personnel/basic` | Create personnel without documents |
| POST | `/api/personnel/form201-report` | Generate Form 201 Excel report |
| PUT | `/api/personnel/{person_id}` | Update personnel and documents |

**File Handling:**
- Validates file types (PDF, DOC, DOCX only)
- Enforces 10MB size limit
- SHA256 hash comparison to avoid duplicates
- Organized storage by unit (`uploads/form_201/{UNIT}/{LASTNAME_FIRSTNAME}/`)

---

### 7. api/bmi.py (BMI API Router)
**Purpose:** REST API endpoints for BMI monitoring and reporting.

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/bmi/` | List all BMI records |
| GET | `/api/bmi/{record_id}/pdf` | Generate individual BMI PDF |
| POST | `/api/bmi/` | Create new BMI record |
| POST | `/api/bmi/report` | Generate BMI report (PDF/Excel) |
| POST | `/api/bmi/excel` | Generate BMI Excel report |

**BMI Classification Functions:**
- `compute_bmi()` - Calculate BMI from height/weight
- `classify_who_bmi()` - WHO standard classification
- `classify_pnp_bmi()` - PNP age-adjusted classification
- `compute_weight_metrics()` - Calculate target weights and ranges

**Report Features:**
- PDF reports with personnel photos
- Monthly weight monitoring table (14 months)
- Individual intervention recommendations
- Excel reports with unit grouping

---

## File Upload Structure

### Form 201 Files
```
uploads/form_201/{UNIT}/{LASTNAME_FIRSTNAME}/
├── FORM201_{LASTNAME}_{FIRSTNAME}_pds.pdf
├── FORM201_{LASTNAME}_{FIRSTNAME}_appointment.pdf
├── FORM201_{LASTNAME}_{FIRSTNAME}_promotion.pdf
├── FORM201_{LASTNAME}_{FIRSTNAME}_designation.pdf
├── FORM201_{LASTNAME}_{FIRSTNAME}_reassignment.pdf
├── FORM201_{LASTNAME}_{FIRSTNAME}_diploma.pdf
├── FORM201_{LASTNAME}_{FIRSTNAME}_eligibility.pdf
├── FORM201_{LASTNAME}_{FIRSTNAME}_iper.pdf
├── FORM201_{LASTNAME}_{FIRSTNAME}_saln.pdf
├── FORM201_{LASTNAME}_{FIRSTNAME}_pft.pdf
├── FORM201_{LASTNAME}_{FIRSTNAME}_rca.pdf
├── FORM201_{LASTNAME}_{FIRSTNAME}_mandatory_{TITLE}.pdf
└── FORM201_{LASTNAME}_{FIRSTNAME}_specialized_{TITLE}.pdf
```

### BMI Files
```
uploads/bmi/{UNIT}/{NAME}/
├── BMI_{NAME}_front.jpg
├── BMI_{NAME}_left.jpg
└── BMI_{NAME}_right.jpg
```

---

## Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.x | UI framework |
| React Router | 6.x | Client-side routing |
| Axios | Latest | HTTP client |
| Bootstrap | 5.x | CSS framework |
| Bootstrap Icons | Latest | Icon library |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.x | Runtime |
| FastAPI | Latest | Web framework |
| SQLAlchemy | Latest | ORM |
| Pydantic | Latest | Data validation |
| ReportLab | Latest | PDF generation |
| openpyxl | Latest | Excel generation |

### Database
| Technology | Purpose |
|------------|---------|
| SQLite | Local development database |

---

## Deployment Information

### Development Ports
| Service | Port | URL |
|---------|------|-----|
| Frontend | 54112 | http://localhost:54112 |
| Backend API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |

### Production
- Frontend is served by FastAPI from `/uploads` static mount
- Single-origin deployment supported
- Configurable via `REACT_APP_API_BASE` environment variable

---

## System Capabilities Summary

| Feature | Status | Description |
|---------|--------|-------------|
| Personnel CRUD | ✅ | Create, Read, Update personnel records |
| Document Upload | ✅ | 13 required documents per personnel |
| Document Management | ✅ | Add, replace, delete documents |
| Training Tracking | ✅ | Mandatory and specialized trainings |
| BMI Recording | ✅ | Body measurements with photos |
| BMI Classification | ✅ | WHO and PNP age-adjusted standards |
| BMI Reports | ✅ | PDF and Excel generation |
| Form 201 Reports | ✅ | Excel report with compliance tracking |
| Unit Filtering | ✅ | Filter by 6 regional units |
| Search | ✅ | Text search across records |
| Photo Upload | ✅ | BMI body measurement photos |

---

*Report generated for CIDG RFU4A Personnel Management System*
*Last Updated: March 2026*
