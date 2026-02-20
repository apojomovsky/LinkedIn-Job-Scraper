def create_tables(conn, cursor):
    cursor.execute('''
          CREATE TABLE IF NOT EXISTS jobs (
          job_id INTEGER PRIMARY KEY,
          scraped INTEGER NOT NULL DEFAULT 0,
          company_id INTEGER,
          work_type TEXT,
          formatted_work_type TEXT,
          location TEXT,
          job_posting_url TEXT,
          applies INTEGER,
          original_listed_time TEXT,
          remote_allowed INTEGER,
          application_url TEXT,
          application_type TEXT,
          expiry TEXT,
          closed_time TEXT,
          formatted_experience_level TEXT,
          description TEXT,
          title TEXT,
          skills_desc TEXT,
          views INTEGER,
          listed_time TEXT,
          posting_domain TEXT,
          sponsored INTEGER,
          applicant_tracking_system TEXT,
          job_state TEXT,
          workplace_type TEXT
        );
    ''')

    cursor.execute('''
      CREATE TABLE IF NOT EXISTS skills (
          skill_abr TEXT PRIMARY KEY,
          skill_name TEXT
      )
  ''')

    cursor.execute('''
      CREATE TABLE IF NOT EXISTS job_skills (
          job_id INTEGER,
          skill_abr TEXT,
          FOREIGN KEY (job_id) REFERENCES jobs(job_id),
          FOREIGN KEY (skill_abr) REFERENCES skills(skill_abr),
          PRIMARY KEY (job_id, skill_abr)
      )
    ''')

    cursor.execute('''
      CREATE TABLE IF NOT EXISTS industries (
          industry_id INTEGER PRIMARY KEY,
          industry_name TEXT
      )
    ''')

    cursor.execute('''
      CREATE TABLE IF NOT EXISTS job_industries (
          job_id INTEGER,
          industry_id INTEGER,
          FOREIGN KEY (job_id) REFERENCES jobs(job_id),
          FOREIGN KEY (industry_id) REFERENCES industries(industry_id),
          PRIMARY KEY (job_id, industry_id)
      )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            company_id INTEGER PRIMARY KEY,
            name TEXT,
            country TEXT,
            url TEXT
        )
    ''')

    cursor.execute('''
      CREATE TABLE IF NOT EXISTS company_specialities (
          company_id INTEGER NOT NULL,
          speciality INTEGER NOT NULL,
          FOREIGN KEY (company_id) REFERENCES companies (company_id),
          PRIMARY KEY (company_id, speciality)
      )
    ''')

    cursor.execute('''
      CREATE TABLE IF NOT EXISTS company_industries (
          company_id INTEGER NOT NULL,
          industry INTEGER NOT NULL,
          FOREIGN KEY (company_id) REFERENCES companies (company_id),
          PRIMARY KEY (company_id, industry)
      )
    ''')

    conn.commit()
    return True