#!/usr/bin/env python3
"""
ALMQUIST Grants Database Setup
Creates SQLite database for Czech grants/subsidies RAG system

Database: /home/puzik/almquist_grants.db

Tables:
- grant_programs: Grant programs/funds
- grant_calls: Specific grant calls/announcements
- grant_applications: Individual applications
- grant_recipients: Successful recipients
- grant_evaluations: Success/failure analysis
- crawl_history: Crawler tracking
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "/home/puzik/almquist_grants.db"


def create_database():
    """Create grants database with all tables"""

    print("=" * 70)
    print("🏦 ALMQUIST GRANTS DATABASE SETUP")
    print("=" * 70)
    print(f"\n📂 Database: {DB_PATH}")

    # Remove existing database
    if os.path.exists(DB_PATH):
        print(f"⚠️  Removing existing database...")
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table 1: Grant Programs
    print("\n📋 Creating table: grant_programs")
    cursor.execute("""
    CREATE TABLE grant_programs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_code TEXT UNIQUE,           -- e.g., "OP PIK", "OP TAK"
        program_name TEXT,                  -- Full program name
        fund_name TEXT,                     -- EFRR, ESF, FS, EZFRV, národní
        managing_authority TEXT,            -- MPO, MŠMT, etc.
        period TEXT,                        -- 2014-2020, 2021-2027
        total_allocation REAL,              -- Total budget
        currency TEXT DEFAULT 'CZK',
        program_url TEXT,                   -- Official program page
        description TEXT,                   -- Program description
        priority_axes TEXT,                 -- JSON array of priority axes
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table 2: Grant Calls
    print("📋 Creating table: grant_calls")
    cursor.execute("""
    CREATE TABLE grant_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        call_code TEXT UNIQUE,              -- Unique call identifier
        program_id INTEGER,                 -- FK to grant_programs
        call_name TEXT,                     -- Call title
        call_type TEXT,                     -- dotace/příspěvek/návratná pomoc
        announcement_date TEXT,             -- When announced
        submission_start TEXT,              -- Application period start
        submission_end TEXT,                -- Application deadline
        evaluation_date TEXT,               -- When evaluated
        budget_total REAL,                  -- Total call budget
        budget_allocated REAL,              -- Actually allocated
        num_applications INTEGER,           -- Total applications
        num_approved INTEGER,               -- Approved applications
        num_rejected INTEGER,               -- Rejected applications
        success_rate REAL,                  -- % approved
        call_url TEXT,                      -- URL to call details
        eligibility_criteria TEXT,          -- Who can apply
        evaluation_criteria TEXT,           -- How evaluated (JSON)
        priorities TEXT,                    -- Supported priorities (JSON)
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (program_id) REFERENCES grant_programs(id)
    )
    """)

    # Table 3: Grant Applications
    print("📋 Creating table: grant_applications")
    cursor.execute("""
    CREATE TABLE grant_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id TEXT UNIQUE,         -- Official application ID
        call_id INTEGER,                    -- FK to grant_calls
        project_name TEXT,                  -- Project title
        applicant_name TEXT,                -- Organization/person
        applicant_ico TEXT,                 -- IČO (company ID)
        applicant_type TEXT,                -- firma/obec/neziskovka/FO
        application_date TEXT,              -- When submitted
        decision_date TEXT,                 -- When decided
        status TEXT,                        -- schváleno/zamítnuto/storno
        requested_amount REAL,              -- Requested funding
        approved_amount REAL,               -- Approved funding
        paid_amount REAL,                   -- Actually paid out
        eu_cofinancing_rate REAL,           -- % EU funding
        national_cofinancing_rate REAL,     -- % national funding
        own_resources_rate REAL,            -- % own resources
        project_start_date TEXT,            -- Project start
        project_end_date TEXT,              -- Project end
        project_location TEXT,              -- NUTS code / city
        project_summary TEXT,               -- Project description
        evaluation_score REAL,              -- Evaluation points
        evaluator_comments TEXT,            -- Why approved/rejected
        success_factors TEXT,               -- What made it succeed (JSON)
        failure_reasons TEXT,               -- Why rejected (JSON)
        application_url TEXT,               -- URL to application details
        added_to_rag INTEGER DEFAULT 0,    -- Whether in RAG
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (call_id) REFERENCES grant_calls(id)
    )
    """)

    # Table 4: Grant Recipients
    print("📋 Creating table: grant_recipients")
    cursor.execute("""
    CREATE TABLE grant_recipients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_ico TEXT,                 -- IČO
        recipient_name TEXT,                -- Organization name
        recipient_type TEXT,                -- Type of organization
        recipient_nuts TEXT,                -- Location (NUTS)
        recipient_city TEXT,                -- City
        total_grants_received INTEGER,      -- Count of grants
        total_amount_received REAL,         -- Sum of all grants
        first_grant_date TEXT,              -- First grant received
        last_grant_date TEXT,               -- Most recent grant
        success_rate REAL,                  -- % of applications approved
        avg_grant_amount REAL,              -- Average grant size
        programs TEXT,                      -- List of programs (JSON)
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(recipient_ico, recipient_name)
    )
    """)

    # Table 5: Grant Evaluations
    print("📋 Creating table: grant_evaluations")
    cursor.execute("""
    CREATE TABLE grant_evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER,             -- FK to grant_applications
        evaluation_date TEXT,               -- When evaluated
        evaluator_type TEXT,                -- Typ hodnotitele
        evaluation_phase TEXT,              -- Phase 1/2/etc.
        criteria_name TEXT,                 -- Criterion name
        criteria_score REAL,                -- Score for this criterion
        criteria_max_score REAL,            -- Max possible score
        criteria_weight REAL,               -- Weight in final score
        evaluator_notes TEXT,               -- Detailed comments
        is_critical_failure INTEGER DEFAULT 0, -- Critical rejection reason
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES grant_applications(id)
    )
    """)

    # Table 6: Crawl History
    print("📋 Creating table: crawl_history")
    cursor.execute("""
    CREATE TABLE crawl_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,                        -- ms2021/dotaceeu/mpo/hlidacstatu
        crawl_type TEXT,                    -- programs/calls/applications
        start_time TEXT,
        end_time TEXT,
        records_crawled INTEGER,
        records_new INTEGER,
        records_updated INTEGER,
        records_failed INTEGER,
        status TEXT,                        -- success/failed/partial
        error_message TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create indexes
    print("\n🔍 Creating indexes...")

    cursor.execute("CREATE INDEX idx_applications_status ON grant_applications(status)")
    cursor.execute("CREATE INDEX idx_applications_call ON grant_applications(call_id)")
    cursor.execute("CREATE INDEX idx_applications_applicant ON grant_applications(applicant_ico)")
    cursor.execute("CREATE INDEX idx_applications_rag ON grant_applications(added_to_rag)")
    cursor.execute("CREATE INDEX idx_calls_program ON grant_calls(program_id)")
    cursor.execute("CREATE INDEX idx_recipients_ico ON grant_recipients(recipient_ico)")
    cursor.execute("CREATE INDEX idx_evaluations_app ON grant_evaluations(application_id)")

    conn.commit()

    print("\n✅ Database created successfully!")
    print(f"📊 Tables: grant_programs, grant_calls, grant_applications,")
    print(f"           grant_recipients, grant_evaluations, crawl_history")
    print(f"🔍 Indexes: 7 created for performance")

    # Print schema
    print("\n" + "=" * 70)
    print("📋 DATABASE SCHEMA")
    print("=" * 70)

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"\n{table_name}:")
        for col in columns:
            col_id, col_name, col_type, not_null, default, pk = col
            flags = []
            if pk:
                flags.append("PK")
            if not_null:
                flags.append("NOT NULL")
            if default:
                flags.append(f"DEFAULT {default}")
            flags_str = " " + " ".join(flags) if flags else ""
            print(f"  {col_name:30s} {col_type:15s}{flags_str}")

    conn.close()

    print("\n" + "=" * 70)
    print("🚀 Ready for crawling!")
    print("=" * 70)


if __name__ == "__main__":
    create_database()
