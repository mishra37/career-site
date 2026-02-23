#!/usr/bin/env python3
"""
Seed data generator for CareerMatch.

Generates ~10,000 diverse, realistic job listings and inserts them into SQLite.
Also migrates the existing 50 jobs from data/jobs.json.

Usage:
    python seed_data.py           # generate + seed
    python seed_data.py --reset   # wipe DB and re-seed
"""

from __future__ import annotations

import json
import random
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

from database import get_db, init_db, insert_job, get_job_count

# ── Taxonomy ────────────────────────────────────────────────

INDUSTRIES = {
    "Technology": {
        "department": "Engineering",
        "roles": {
            "Intern": [
                "Software Engineering Intern", "Frontend Intern", "Backend Intern",
                "QA Intern", "DevOps Intern", "Data Science Intern",
                "Mobile Development Intern", "Cloud Engineering Intern",
                "Security Engineering Intern", "Site Reliability Intern",
            ],
            "Entry": [
                "Junior Software Engineer", "Junior Frontend Developer",
                "Junior Backend Developer", "Junior QA Engineer",
                "Junior Data Analyst", "Junior Mobile Developer",
                "Associate Software Engineer", "Junior DevOps Engineer",
                "Junior Cloud Engineer", "Junior Security Engineer",
                "Junior Full-Stack Developer", "Junior Site Reliability Engineer",
                "Junior Platform Engineer", "Junior iOS Developer",
                "Junior Android Developer", "Junior Embedded Engineer",
            ],
            "Mid": [
                "Software Engineer", "Frontend Developer", "Backend Developer",
                "Full-Stack Developer", "Mobile Developer", "QA Engineer",
                "Data Engineer", "DevOps Engineer", "Cloud Engineer",
                "Security Engineer", "Platform Engineer", "ML Engineer",
                "iOS Developer", "Android Developer", "Embedded Systems Engineer",
                "Site Reliability Engineer", "Infrastructure Engineer",
                "Release Engineer", "Build Engineer", "Automation Engineer",
            ],
            "Senior": [
                "Senior Software Engineer", "Senior Frontend Developer",
                "Senior Backend Developer", "Senior Full-Stack Developer",
                "Senior Mobile Developer", "Senior QA Engineer",
                "Senior Data Engineer", "Senior DevOps Engineer",
                "Senior Cloud Engineer", "Senior Security Engineer",
                "Senior ML Engineer", "Senior Platform Engineer",
                "Senior iOS Developer", "Senior Android Developer",
                "Senior Site Reliability Engineer", "Senior Infrastructure Engineer",
                "Senior Embedded Engineer", "Senior Automation Engineer",
            ],
            "Lead": [
                "Lead Software Engineer", "Principal Engineer",
                "Staff Engineer", "Tech Lead", "Lead Data Engineer",
                "Lead DevOps Engineer", "Lead Security Engineer",
                "Staff Frontend Engineer", "Staff Backend Engineer",
                "Lead Mobile Engineer", "Lead SRE", "Lead QA Engineer",
            ],
            "Manager": [
                "Engineering Manager", "QA Manager", "DevOps Manager",
                "Data Engineering Manager", "Security Engineering Manager",
                "Frontend Engineering Manager", "Backend Engineering Manager",
                "Mobile Engineering Manager", "Platform Engineering Manager",
            ],
            "Director": [
                "Director of Engineering", "Director of Data Engineering",
                "Director of Platform", "Director of Security",
                "Director of Infrastructure", "Director of QA",
            ],
            "VP": ["VP of Engineering", "VP of Technology", "VP of Infrastructure"],
            "C-Suite": ["CTO", "Chief Information Officer", "Chief Technology Officer"],
        },
        "skills_pool": [
            "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "C#",
            "React", "Angular", "Vue.js", "Next.js", "Node.js", "Express.js", "Svelte",
            "Django", "Flask", "FastAPI", "Spring Boot", "Ruby on Rails", "ASP.NET",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "DynamoDB",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Pulumi",
            "CI/CD", "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "ArgoCD",
            "REST APIs", "GraphQL", "gRPC", "Microservices", "Event-Driven Architecture",
            "Linux", "Bash", "Git", "Agile", "Scrum", "Kanban",
            "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
            "React Native", "Swift", "Kotlin", "Flutter", "SwiftUI",
            "Webpack", "Vite", "Tailwind CSS", "SASS", "CSS-in-JS",
            "Jest", "Cypress", "Playwright", "Selenium", "Vitest",
            "OAuth", "JWT", "HTTPS", "Encryption", "OWASP",
            "System Design", "Data Structures", "Algorithms",
            "Kafka", "RabbitMQ", "NATS", "Apache Spark",
            "Prometheus", "Grafana", "Datadog", "New Relic",
        ],
        "salary_ranges": {
            "Intern": (40000, 75000), "Entry": (70000, 110000),
            "Mid": (100000, 160000), "Senior": (140000, 220000),
            "Lead": (170000, 260000), "Manager": (180000, 270000),
            "Director": (220000, 330000), "VP": (280000, 420000),
            "C-Suite": (350000, 550000),
        },
        "descriptions": [
            "Join our engineering team to build scalable, high-performance systems that serve millions of users.",
            "Work on cutting-edge technology to solve complex problems in a fast-paced, collaborative environment.",
            "Design and implement robust software solutions that drive business growth and improve user experience.",
            "Be part of a world-class engineering team building the next generation of our platform.",
            "Contribute to open-source projects and help shape the future of our technology stack.",
            "Build distributed systems that handle billions of requests with high reliability.",
            "Help us reimagine how people interact with technology through innovative software.",
            "Join a team obsessed with code quality, developer experience, and shipping great products.",
            "Work across the stack to deliver features that directly impact our users.",
            "Build the infrastructure that powers our growing suite of products and services.",
        ],
        "visa_rate": 0.40,
    },
    "Data Science & AI": {
        "department": "Data Science",
        "roles": {
            "Intern": [
                "Data Science Intern", "Machine Learning Intern",
                "AI Research Intern", "Data Analytics Intern",
                "NLP Intern", "Computer Vision Intern",
            ],
            "Entry": [
                "Junior Data Scientist", "Junior ML Engineer",
                "Junior Data Analyst", "Junior AI Engineer",
                "Associate Data Scientist", "Junior Research Engineer",
                "Junior NLP Engineer", "Junior Analytics Engineer",
            ],
            "Mid": [
                "Data Scientist", "Machine Learning Engineer",
                "AI Engineer", "Data Analyst", "Research Engineer",
                "NLP Engineer", "Computer Vision Engineer",
                "Applied Scientist", "Analytics Engineer",
                "MLOps Engineer", "Recommendation Systems Engineer",
                "Deep Learning Engineer",
            ],
            "Senior": [
                "Senior Data Scientist", "Senior ML Engineer",
                "Senior AI Engineer", "Senior Research Engineer",
                "Senior NLP Engineer", "Senior Computer Vision Engineer",
                "Senior Applied Scientist", "Senior Analytics Engineer",
                "Senior MLOps Engineer", "Senior Deep Learning Engineer",
            ],
            "Lead": [
                "Lead Data Scientist", "Principal ML Engineer",
                "Staff ML Engineer", "Lead AI Researcher",
                "Lead Applied Scientist", "Principal Data Scientist",
            ],
            "Manager": [
                "Data Science Manager", "ML Engineering Manager",
                "AI Research Manager", "Analytics Manager",
            ],
            "Director": [
                "Director of Data Science", "Director of AI",
                "Director of Machine Learning", "Director of Analytics",
            ],
            "VP": ["VP of Data Science", "VP of AI", "VP of Analytics"],
            "C-Suite": ["Chief Data Officer", "Chief AI Officer"],
        },
        "skills_pool": [
            "Python", "R", "SQL", "TensorFlow", "PyTorch", "Scikit-learn",
            "Pandas", "NumPy", "SciPy", "Keras", "XGBoost", "LightGBM",
            "Hugging Face", "Transformers", "BERT", "GPT", "LLMs",
            "Natural Language Processing", "Computer Vision", "Deep Learning",
            "Machine Learning", "Neural Networks", "Reinforcement Learning",
            "Statistical Modeling", "A/B Testing", "Bayesian Methods",
            "Feature Engineering", "Model Deployment", "MLOps",
            "Apache Spark", "Databricks", "Airflow", "dbt",
            "Tableau", "Power BI", "Looker", "Data Visualization",
            "AWS SageMaker", "Google Vertex AI", "Azure ML",
            "Docker", "Kubernetes", "Git", "Jupyter",
            "OpenCV", "YOLO", "Stable Diffusion", "RAG",
            "Vector Databases", "Pinecone", "Weaviate", "LangChain",
            "Data Pipelines", "ETL", "Data Warehousing", "Snowflake",
            "BigQuery", "Redshift", "Delta Lake",
        ],
        "salary_ranges": {
            "Intern": (45000, 80000), "Entry": (80000, 120000),
            "Mid": (110000, 175000), "Senior": (150000, 240000),
            "Lead": (180000, 280000), "Manager": (190000, 290000),
            "Director": (240000, 360000), "VP": (300000, 450000),
            "C-Suite": (370000, 580000),
        },
        "descriptions": [
            "Apply machine learning and statistical methods to solve impactful business problems at scale.",
            "Build and deploy ML models that power intelligent features used by millions of users.",
            "Join our AI team to push the boundaries of what's possible with modern machine learning.",
            "Work on cutting-edge NLP, computer vision, and deep learning projects.",
            "Design and implement data pipelines and ML infrastructure for production systems.",
            "Drive data-driven decision making through advanced analytics and experimentation.",
            "Build recommendation systems and personalization engines that delight users.",
            "Research and develop novel AI techniques to advance our product capabilities.",
            "Create scalable ML solutions from prototype to production deployment.",
            "Collaborate with engineering and product teams to bring AI innovations to market.",
        ],
        "visa_rate": 0.45,
    },
    "Healthcare": {
        "department": "Healthcare",
        "roles": {
            "Intern": [
                "Healthcare Intern", "Clinical Research Intern",
                "Public Health Intern", "Health Informatics Intern",
                "Nursing Intern", "Pharmacy Intern",
            ],
            "Entry": [
                "Certified Nursing Assistant", "Medical Records Clerk",
                "Pharmacy Technician", "Lab Assistant",
                "Patient Care Technician", "Medical Scribe",
                "Licensed Practical Nurse", "Home Health Aide",
                "Medical Assistant", "Phlebotomist",
                "Emergency Room Technician", "Surgical Technician",
                "Dietary Aide", "Health Unit Coordinator",
            ],
            "Mid": [
                "Registered Nurse", "Physical Therapist",
                "Medical Laboratory Technician", "Dental Hygienist",
                "Respiratory Therapist", "Occupational Therapist",
                "Medical Coder", "Health Informatics Specialist",
                "Nurse Practitioner", "Physician Assistant",
                "Clinical Pharmacist", "Radiologic Technologist",
                "Speech-Language Pathologist", "Dialysis Nurse",
                "ICU Nurse", "OR Nurse", "Pediatric Nurse",
                "Emergency Room Nurse", "Travel Nurse",
                "Case Manager", "Clinical Data Analyst",
                "Public Health Nurse", "School Nurse",
            ],
            "Senior": [
                "Senior Registered Nurse", "Senior Physical Therapist",
                "Senior Pharmacist", "Senior Lab Technician",
                "Clinical Research Coordinator", "Senior Nurse Practitioner",
                "Senior Physician Assistant", "Senior Radiologist",
                "Senior Clinical Pharmacist", "Clinical Nurse Specialist",
            ],
            "Lead": [
                "Charge Nurse", "Lead Physical Therapist",
                "Lead Pharmacist", "Lead Health Informatics",
                "Lead Clinical Research Coordinator", "Nurse Educator",
            ],
            "Manager": [
                "Nurse Manager", "Pharmacy Manager",
                "Lab Manager", "Clinical Operations Manager",
                "Case Management Manager", "Health Services Manager",
            ],
            "Director": [
                "Director of Nursing", "Director of Clinical Operations",
                "Director of Pharmacy", "Director of Patient Services",
                "Chief Nursing Officer",
            ],
            "VP": ["VP of Clinical Services", "VP of Patient Care", "VP of Medical Affairs"],
        },
        "skills_pool": [
            "Patient Care", "Clinical Assessment", "IV Therapy",
            "Ventilator Management", "EHR Systems", "Epic", "Cerner",
            "HIPAA Compliance", "Medication Administration", "Wound Care",
            "CPR", "ACLS", "BLS", "Triage", "Phlebotomy",
            "Medical Terminology", "Anatomy", "Pharmacology",
            "Patient Education", "Care Planning", "Documentation",
            "Infection Control", "Lab Procedures", "Diagnostic Testing",
            "Physical Rehabilitation", "Occupational Therapy",
            "Medical Coding", "ICD-10", "CPT Coding", "Health Analytics",
            "Surgical Assistance", "Radiology", "Pediatric Care",
            "Geriatric Care", "Mental Health", "Telehealth",
            "Emergency Medicine", "Critical Care", "Oncology",
            "Cardiac Care", "Neonatal Care", "Dialysis",
            "Home Health", "Hospice Care", "Public Health",
        ],
        "salary_ranges": {
            "Intern": (30000, 45000), "Entry": (35000, 55000),
            "Mid": (55000, 95000), "Senior": (85000, 130000),
            "Lead": (100000, 145000), "Manager": (110000, 160000),
            "Director": (140000, 210000), "VP": (180000, 280000),
        },
        "descriptions": [
            "Provide compassionate, evidence-based patient care in a dynamic healthcare setting.",
            "Join our clinical team dedicated to improving patient outcomes through innovative care delivery.",
            "Work alongside leading medical professionals to advance healthcare quality and safety.",
            "Be part of a patient-centered organization committed to excellence in clinical care.",
            "Deliver high-quality nursing care to patients across diverse medical specialties.",
            "Support patient recovery through evidence-based therapeutic interventions and care planning.",
            "Help transform healthcare delivery through technology, data, and innovative clinical practices.",
            "Collaborate with interdisciplinary teams to ensure comprehensive patient-centered care.",
        ],
        "visa_rate": 0.15,
    },
    "Finance": {
        "department": "Finance",
        "roles": {
            "Intern": ["Finance Intern", "Accounting Intern"],
            "Entry": [
                "Junior Financial Analyst", "Staff Accountant",
                "Junior Auditor", "Tax Associate",
            ],
            "Mid": [
                "Financial Analyst", "Senior Accountant", "Auditor",
                "Tax Specialist", "Risk Analyst", "Compliance Analyst",
                "Budget Analyst", "Investment Analyst",
            ],
            "Senior": [
                "Senior Financial Analyst", "Senior Auditor",
                "Senior Tax Specialist", "Senior Risk Analyst",
                "Quantitative Analyst", "Portfolio Analyst",
            ],
            "Lead": [
                "Lead Financial Analyst", "Principal Risk Analyst",
                "Lead Compliance Analyst",
            ],
            "Manager": [
                "Finance Manager", "Accounting Manager", "Tax Manager",
                "Audit Manager", "Risk Manager",
            ],
            "Director": [
                "Director of Finance", "Director of Accounting",
                "Director of Risk Management",
            ],
            "VP": ["VP of Finance", "VP of Financial Planning"],
            "C-Suite": ["CFO", "Chief Risk Officer"],
        },
        "skills_pool": [
            "Financial Analysis", "Financial Modeling", "Excel",
            "VBA", "SQL", "Tableau", "Power BI", "Python",
            "GAAP", "IFRS", "SOX Compliance", "Budgeting",
            "Forecasting", "Risk Assessment", "Portfolio Management",
            "Bloomberg Terminal", "Reuters", "SAP", "QuickBooks",
            "Audit", "Tax Preparation", "Regulatory Compliance",
            "M&A", "Valuation", "DCF Modeling", "Monte Carlo",
            "Derivatives", "Fixed Income", "Equity Research",
        ],
        "salary_ranges": {
            "Intern": (45000, 70000), "Entry": (60000, 90000),
            "Mid": (85000, 130000), "Senior": (120000, 180000),
            "Lead": (150000, 220000), "Manager": (140000, 210000),
            "Director": (190000, 300000), "VP": (250000, 400000),
            "C-Suite": (300000, 500000),
        },
        "descriptions": [
            "Drive financial strategy and provide analytical insights to support business decision-making.",
            "Join our finance team to help shape the financial future of our organization.",
            "Analyze complex financial data to identify trends, risks, and opportunities for growth.",
        ],
        "visa_rate": 0.25,
    },
    "Design": {
        "department": "Design",
        "roles": {
            "Intern": ["Design Intern", "UX Research Intern"],
            "Entry": [
                "Junior UX Designer", "Junior UI Designer",
                "Junior Graphic Designer",
            ],
            "Mid": [
                "UX Designer", "UI Designer", "Product Designer",
                "Graphic Designer", "UX Researcher", "Visual Designer",
                "Motion Designer", "Content Designer",
            ],
            "Senior": [
                "Senior UX Designer", "Senior Product Designer",
                "Senior UI Designer", "Senior UX Researcher",
                "Senior Visual Designer",
            ],
            "Lead": [
                "Lead Product Designer", "Principal Designer",
                "Lead UX Researcher",
            ],
            "Manager": ["Design Manager", "UX Research Manager"],
            "Director": ["Director of Design", "Director of UX"],
            "VP": ["VP of Design"],
        },
        "skills_pool": [
            "Figma", "Sketch", "Adobe XD", "Adobe Illustrator",
            "Adobe Photoshop", "InVision", "Zeplin", "Framer",
            "User Research", "Usability Testing", "A/B Testing",
            "Wireframing", "Prototyping", "Design Systems",
            "Typography", "Color Theory", "Interaction Design",
            "Information Architecture", "User Flows", "Personas",
            "Accessibility", "WCAG", "Responsive Design",
            "HTML", "CSS", "Motion Design", "After Effects",
        ],
        "salary_ranges": {
            "Intern": (35000, 55000), "Entry": (55000, 85000),
            "Mid": (80000, 130000), "Senior": (120000, 180000),
            "Lead": (150000, 220000), "Manager": (150000, 220000),
            "Director": (190000, 280000), "VP": (240000, 380000),
        },
        "descriptions": [
            "Create intuitive, beautiful user experiences that delight our customers and drive engagement.",
            "Join our design team to shape the visual and interactive experience of our products.",
            "Work closely with engineering and product teams to bring designs from concept to reality.",
        ],
        "visa_rate": 0.25,
    },
    "Marketing": {
        "department": "Marketing",
        "roles": {
            "Intern": ["Marketing Intern", "Content Intern"],
            "Entry": [
                "Marketing Coordinator", "Content Writer",
                "Social Media Coordinator", "SEO Specialist",
            ],
            "Mid": [
                "Digital Marketing Manager", "Content Strategist",
                "SEO Manager", "Social Media Manager", "Email Marketing Manager",
                "Brand Manager", "Growth Marketing Manager", "Copywriter",
            ],
            "Senior": [
                "Senior Marketing Manager", "Senior Content Strategist",
                "Senior Brand Manager", "Senior Growth Manager",
            ],
            "Lead": [
                "Lead Marketing Strategist", "Principal Content Strategist",
            ],
            "Manager": ["Marketing Manager", "PR Manager", "Brand Marketing Manager"],
            "Director": [
                "Director of Marketing", "Director of Content",
                "Director of Growth",
            ],
            "VP": ["VP of Marketing", "VP of Brand"],
            "C-Suite": ["CMO"],
        },
        "skills_pool": [
            "Google Analytics", "Google Ads", "Facebook Ads", "SEO",
            "SEM", "Content Marketing", "Social Media Marketing",
            "Email Marketing", "Mailchimp", "HubSpot", "Marketo",
            "Copywriting", "Brand Strategy", "Market Research",
            "A/B Testing", "Conversion Optimization", "Marketing Automation",
            "Adobe Creative Suite", "Canva", "WordPress",
            "PR", "Media Relations", "Event Marketing",
        ],
        "salary_ranges": {
            "Intern": (30000, 50000), "Entry": (45000, 70000),
            "Mid": (65000, 110000), "Senior": (95000, 150000),
            "Lead": (120000, 180000), "Manager": (100000, 160000),
            "Director": (150000, 240000), "VP": (200000, 350000),
            "C-Suite": (250000, 450000),
        },
        "descriptions": [
            "Drive brand awareness and customer acquisition through creative marketing strategies.",
            "Join our marketing team to build campaigns that engage and convert audiences across channels.",
            "Shape our brand story and grow our market presence through data-driven marketing.",
        ],
        "visa_rate": 0.20,
    },
    "Sales": {
        "department": "Sales",
        "roles": {
            "Entry": [
                "Sales Development Representative", "Business Development Representative",
                "Inside Sales Representative",
            ],
            "Mid": [
                "Account Executive", "Sales Engineer", "Customer Success Manager",
                "Solutions Consultant", "Territory Manager",
            ],
            "Senior": [
                "Senior Account Executive", "Senior Sales Engineer",
                "Senior Customer Success Manager", "Strategic Account Manager",
            ],
            "Lead": ["Lead Sales Engineer", "Principal Solutions Architect"],
            "Manager": [
                "Sales Manager", "Customer Success Manager",
                "Regional Sales Manager",
            ],
            "Director": [
                "Director of Sales", "Director of Business Development",
                "Director of Customer Success",
            ],
            "VP": ["VP of Sales", "VP of Revenue", "VP of Customer Success"],
        },
        "skills_pool": [
            "Salesforce", "HubSpot CRM", "Cold Calling", "Prospecting",
            "Pipeline Management", "Contract Negotiation", "Presentation Skills",
            "Solution Selling", "Consultative Selling", "Account Management",
            "Revenue Forecasting", "Territory Planning", "SaaS Sales",
            "Enterprise Sales", "Channel Sales", "Lead Generation",
            "Customer Retention", "Upselling", "Cross-selling",
        ],
        "salary_ranges": {
            "Entry": (45000, 70000), "Mid": (70000, 120000),
            "Senior": (100000, 170000), "Lead": (130000, 200000),
            "Manager": (120000, 190000), "Director": (170000, 280000),
            "VP": (220000, 380000),
        },
        "descriptions": [
            "Drive revenue growth by building strong relationships with enterprise clients.",
            "Join our sales team to help organizations discover solutions that transform their business.",
            "Partner with prospects and customers to understand their needs and deliver value.",
        ],
        "visa_rate": 0.15,
    },
    "Education": {
        "department": "Education",
        "roles": {
            "Entry": [
                "Teaching Assistant", "Tutor",
                "Junior Instructional Designer",
            ],
            "Mid": [
                "Teacher", "Curriculum Designer", "Instructional Designer",
                "EdTech Developer", "Academic Coordinator",
            ],
            "Senior": [
                "Senior Teacher", "Senior Curriculum Designer",
                "Senior Instructional Designer", "Research Scientist",
            ],
            "Lead": ["Lead Curriculum Designer", "Lead Instructional Designer"],
            "Manager": ["Education Program Manager", "Academic Administrator"],
            "Director": ["Director of Education", "Director of Curriculum"],
            "VP": ["VP of Academic Affairs"],
        },
        "skills_pool": [
            "Curriculum Development", "Lesson Planning", "Classroom Management",
            "Student Assessment", "Educational Technology", "LMS",
            "Instructional Design", "E-learning", "SCORM",
            "Pedagogy", "Differentiated Instruction", "Remote Teaching",
            "Google Classroom", "Canvas", "Blackboard", "Moodle",
            "Research Methods", "Data Analysis", "Grant Writing",
        ],
        "salary_ranges": {
            "Entry": (35000, 50000), "Mid": (45000, 75000),
            "Senior": (65000, 100000), "Lead": (80000, 120000),
            "Manager": (85000, 130000), "Director": (110000, 180000),
            "VP": (150000, 250000),
        },
        "descriptions": [
            "Shape the next generation through innovative teaching and curriculum development.",
            "Join our education team to create engaging learning experiences that inspire students.",
            "Develop and deliver educational content that makes complex subjects accessible.",
        ],
        "visa_rate": 0.20,
    },
    "Legal": {
        "department": "Legal",
        "roles": {
            "Intern": ["Legal Intern", "Compliance Intern", "Law Clerk"],
            "Entry": [
                "Paralegal", "Legal Assistant", "Junior Compliance Analyst",
                "Legal Secretary", "Contract Administrator", "Records Clerk",
                "Immigration Paralegal", "Litigation Paralegal",
            ],
            "Mid": [
                "Corporate Attorney", "Compliance Analyst", "Contract Specialist",
                "IP Attorney", "Privacy Officer", "Regulatory Counsel",
                "Employment Attorney", "Real Estate Attorney", "Tax Attorney",
                "Environmental Compliance Specialist", "Immigration Attorney",
                "Family Law Attorney", "Criminal Defense Attorney",
                "Bankruptcy Attorney", "Securities Attorney", "Litigation Associate",
                "Legal Analyst", "E-Discovery Specialist", "Mediation Specialist",
            ],
            "Senior": [
                "Senior Corporate Attorney", "Senior Compliance Analyst",
                "Senior Contract Manager", "Senior Privacy Counsel",
                "Senior Litigation Attorney", "Senior IP Counsel",
                "Senior Employment Attorney", "Senior Tax Attorney",
                "Senior Regulatory Counsel", "Senior Legal Analyst",
            ],
            "Lead": [
                "Lead Compliance Counsel", "Principal Attorney",
                "Lead Corporate Counsel", "Lead Privacy Counsel",
            ],
            "Manager": [
                "Legal Operations Manager", "Compliance Manager",
                "Contracts Manager", "Regulatory Affairs Manager",
            ],
            "Director": [
                "Director of Legal", "Director of Compliance",
                "Director of Privacy", "Director of Regulatory Affairs",
            ],
            "VP": ["VP of Legal", "General Counsel", "Deputy General Counsel"],
        },
        "skills_pool": [
            "Legal Research", "Contract Drafting", "Contract Review",
            "Compliance", "Regulatory Affairs", "Corporate Law",
            "Intellectual Property", "Patent Law", "Trademark",
            "Data Privacy", "GDPR", "CCPA", "SOX", "HIPAA",
            "Litigation", "Negotiation", "Due Diligence",
            "Legal Writing", "Case Management", "Westlaw", "LexisNexis",
            "Employment Law", "Real Estate Law", "Tax Law", "Securities Law",
            "Environmental Law", "Immigration Law", "Family Law",
            "Mergers & Acquisitions", "Bankruptcy Law", "Mediation",
            "E-Discovery", "Document Review", "Legal Analytics",
            "Risk Assessment", "Corporate Governance", "Arbitration",
        ],
        "salary_ranges": {
            "Intern": (35000, 55000), "Entry": (50000, 75000),
            "Mid": (80000, 140000), "Senior": (130000, 200000),
            "Lead": (160000, 240000), "Manager": (140000, 210000),
            "Director": (200000, 310000), "VP": (260000, 420000),
        },
        "descriptions": [
            "Provide legal counsel to support business operations and ensure regulatory compliance.",
            "Join our legal team to navigate complex legal landscapes and protect the organization.",
            "Draft, review, and negotiate contracts while advising on legal risks and opportunities.",
            "Advise on intellectual property rights and help protect our innovation portfolio.",
            "Support M&A transactions and corporate restructuring with thorough legal analysis.",
            "Ensure the organization meets all regulatory requirements across jurisdictions.",
            "Handle complex litigation matters and develop effective legal strategies.",
            "Manage employment law matters including hiring, termination, and workplace policies.",
        ],
        "visa_rate": 0.20,
    },
    "Operations": {
        "department": "Operations",
        "roles": {
            "Entry": [
                "Operations Coordinator", "Junior Project Manager",
                "Junior Business Analyst",
            ],
            "Mid": [
                "Operations Manager", "Project Manager", "Business Analyst",
                "Supply Chain Analyst", "Procurement Specialist",
                "Process Improvement Specialist", "Logistics Coordinator",
            ],
            "Senior": [
                "Senior Operations Manager", "Senior Project Manager",
                "Senior Business Analyst", "Senior Supply Chain Manager",
            ],
            "Lead": ["Lead Business Analyst", "Lead Project Manager"],
            "Manager": [
                "Operations Manager", "Supply Chain Manager",
                "Warehouse Manager", "Procurement Manager",
            ],
            "Director": [
                "Director of Operations", "Director of Supply Chain",
                "Director of Project Management",
            ],
            "VP": ["VP of Operations", "VP of Supply Chain"],
        },
        "skills_pool": [
            "Project Management", "Agile", "Scrum", "JIRA", "Asana",
            "Process Improvement", "Lean", "Six Sigma", "Kaizen",
            "Supply Chain Management", "Logistics", "Procurement",
            "Inventory Management", "Vendor Management", "ERP",
            "SAP", "Oracle", "Data Analysis", "Excel",
            "Stakeholder Management", "Budget Management", "KPIs",
        ],
        "salary_ranges": {
            "Entry": (40000, 60000), "Mid": (60000, 100000),
            "Senior": (90000, 140000), "Lead": (110000, 170000),
            "Manager": (100000, 160000), "Director": (150000, 240000),
            "VP": (200000, 340000),
        },
        "descriptions": [
            "Optimize business processes and drive operational excellence across the organization.",
            "Join our operations team to improve efficiency and ensure smooth business operations.",
            "Lead cross-functional projects that streamline workflows and reduce costs.",
        ],
        "visa_rate": 0.20,
    },
    "Manufacturing": {
        "department": "Manufacturing & Engineering",
        "roles": {
            "Entry": [
                "Junior Mechanical Engineer", "Junior Electrical Engineer",
                "Manufacturing Associate",
            ],
            "Mid": [
                "Mechanical Engineer", "Electrical Engineer", "Quality Engineer",
                "Industrial Engineer", "Process Engineer", "Civil Engineer",
                "Manufacturing Engineer",
            ],
            "Senior": [
                "Senior Mechanical Engineer", "Senior Electrical Engineer",
                "Senior Quality Engineer", "Senior Process Engineer",
            ],
            "Lead": [
                "Lead Mechanical Engineer", "Principal Engineer",
                "Lead Quality Engineer",
            ],
            "Manager": [
                "Manufacturing Manager", "Quality Manager",
                "Engineering Manager",
            ],
            "Director": [
                "Director of Manufacturing", "Director of Engineering",
                "Director of Quality",
            ],
            "VP": ["VP of Manufacturing", "VP of Engineering"],
        },
        "skills_pool": [
            "AutoCAD", "SolidWorks", "CATIA", "MATLAB",
            "Finite Element Analysis", "3D Modeling", "GD&T",
            "Manufacturing Processes", "CNC", "Injection Molding",
            "Quality Control", "ISO 9001", "Statistical Process Control",
            "Lean Manufacturing", "Six Sigma", "DFMEA", "Root Cause Analysis",
            "PLC Programming", "SCADA", "Circuit Design",
            "Project Management", "Technical Documentation",
        ],
        "salary_ranges": {
            "Entry": (55000, 75000), "Mid": (70000, 110000),
            "Senior": (100000, 150000), "Lead": (130000, 190000),
            "Manager": (120000, 180000), "Director": (160000, 260000),
            "VP": (210000, 350000),
        },
        "descriptions": [
            "Design and optimize manufacturing systems to improve product quality and production efficiency.",
            "Apply engineering principles to solve real-world problems in manufacturing and production.",
            "Join our engineering team to develop innovative solutions for complex technical challenges.",
        ],
        "visa_rate": 0.30,
    },
    "Real Estate": {
        "department": "Real Estate & Construction",
        "roles": {
            "Entry": [
                "Property Management Associate", "Junior Real Estate Analyst",
                "Construction Coordinator",
            ],
            "Mid": [
                "Property Manager", "Real Estate Analyst", "Construction Manager",
                "Estimator", "Urban Planner", "Architect",
            ],
            "Senior": [
                "Senior Property Manager", "Senior Real Estate Analyst",
                "Senior Construction Manager", "Senior Architect",
            ],
            "Manager": ["Real Estate Manager", "Construction Program Manager"],
            "Director": [
                "Director of Real Estate", "Director of Construction",
            ],
            "VP": ["VP of Real Estate"],
        },
        "skills_pool": [
            "Property Management", "Real Estate Analysis", "Market Research",
            "Financial Modeling", "Construction Management", "Budgeting",
            "Zoning Laws", "Building Codes", "AutoCAD", "Revit",
            "Project Scheduling", "Contract Management", "Negotiation",
            "Tenant Relations", "Lease Administration", "Site Planning",
        ],
        "salary_ranges": {
            "Entry": (40000, 60000), "Mid": (60000, 100000),
            "Senior": (90000, 150000), "Manager": (110000, 170000),
            "Director": (150000, 240000), "VP": (200000, 340000),
        },
        "descriptions": [
            "Manage commercial and residential properties to maximize value and tenant satisfaction.",
            "Join our real estate team to analyze markets and drive strategic investment decisions.",
            "Oversee construction projects from planning through completion on time and under budget.",
        ],
        "visa_rate": 0.15,
    },
    "Media": {
        "department": "Media & Entertainment",
        "roles": {
            "Entry": [
                "Junior Content Creator", "Production Assistant",
                "Junior Journalist",
            ],
            "Mid": [
                "Video Producer", "Journalist", "Content Creator",
                "Audio Engineer", "Game Designer", "Animation Artist",
                "Podcast Producer",
            ],
            "Senior": [
                "Senior Video Producer", "Senior Journalist",
                "Senior Content Creator", "Senior Game Designer",
            ],
            "Lead": ["Lead Producer", "Lead Game Designer"],
            "Manager": ["Content Manager", "Production Manager"],
            "Director": [
                "Director of Content", "Creative Director",
            ],
            "VP": ["VP of Content", "VP of Creative"],
        },
        "skills_pool": [
            "Video Production", "Video Editing", "Adobe Premiere Pro",
            "Final Cut Pro", "After Effects", "DaVinci Resolve",
            "Photography", "Audio Engineering", "Pro Tools",
            "Content Strategy", "Social Media", "Storytelling",
            "Unity", "Unreal Engine", "3D Animation", "Maya", "Blender",
            "Journalism", "Copywriting", "Podcasting",
        ],
        "salary_ranges": {
            "Entry": (35000, 55000), "Mid": (55000, 90000),
            "Senior": (80000, 130000), "Lead": (100000, 160000),
            "Manager": (95000, 150000), "Director": (140000, 230000),
            "VP": (180000, 310000),
        },
        "descriptions": [
            "Create compelling content that captivates audiences across digital and traditional media.",
            "Join our creative team to produce high-quality media experiences.",
            "Tell stories that matter through innovative multimedia production.",
        ],
        "visa_rate": 0.15,
    },
    "HR": {
        "department": "Human Resources",
        "roles": {
            "Entry": ["HR Coordinator", "Recruiting Coordinator"],
            "Mid": [
                "HR Business Partner", "Recruiter", "Talent Acquisition Specialist",
                "L&D Specialist", "Compensation Analyst", "Benefits Administrator",
            ],
            "Senior": [
                "Senior HR Business Partner", "Senior Recruiter",
                "Senior Talent Acquisition Lead",
            ],
            "Manager": [
                "HR Manager", "Talent Acquisition Manager",
                "L&D Manager", "Compensation & Benefits Manager",
            ],
            "Director": [
                "Director of HR", "Director of Talent Acquisition",
                "Director of People Operations",
            ],
            "VP": ["VP of People", "VP of Human Resources"],
        },
        "skills_pool": [
            "Recruiting", "Talent Acquisition", "Employee Relations",
            "Performance Management", "Compensation", "Benefits Administration",
            "HRIS", "Workday", "BambooHR", "ADP",
            "Onboarding", "Training & Development", "HR Analytics",
            "Employment Law", "Diversity & Inclusion", "Culture Building",
            "Payroll", "Succession Planning", "Workforce Planning",
        ],
        "salary_ranges": {
            "Entry": (40000, 60000), "Mid": (60000, 95000),
            "Senior": (85000, 130000), "Manager": (100000, 160000),
            "Director": (140000, 220000), "VP": (180000, 310000),
        },
        "descriptions": [
            "Build and support a thriving workplace culture that attracts and retains top talent.",
            "Join our people team to shape employee experience and drive organizational growth.",
            "Partner with business leaders to develop people strategies aligned with company goals.",
        ],
        "visa_rate": 0.15,
    },
    "Product": {
        "department": "Product",
        "roles": {
            "Intern": ["Product Management Intern", "Product Analytics Intern"],
            "Entry": [
                "Associate Product Manager", "Junior Technical Writer",
                "Junior Product Analyst", "Product Coordinator",
            ],
            "Mid": [
                "Product Manager", "Technical Product Manager",
                "Product Analyst", "Technical Writer",
                "Product Operations Manager", "Growth Product Manager",
            ],
            "Senior": [
                "Senior Product Manager", "Senior Technical Product Manager",
                "Senior Product Analyst", "Senior Technical Writer",
            ],
            "Lead": ["Principal Product Manager", "Group Product Manager"],
            "Manager": ["Product Management Lead", "Product Operations Lead"],
            "Director": ["Director of Product", "Director of Product Management"],
            "VP": ["VP of Product"],
            "C-Suite": ["CPO"],
        },
        "skills_pool": [
            "Product Strategy", "Roadmap Planning", "User Stories",
            "Agile", "Scrum", "JIRA", "Confluence",
            "Market Research", "Competitive Analysis", "Data Analysis",
            "SQL", "A/B Testing", "User Research", "Wireframing",
            "Stakeholder Management", "Go-to-Market Strategy",
            "Technical Documentation", "API Documentation",
        ],
        "salary_ranges": {
            "Entry": (60000, 90000), "Mid": (90000, 140000),
            "Senior": (130000, 190000), "Lead": (160000, 240000),
            "Manager": (150000, 220000), "Director": (190000, 300000),
            "VP": (250000, 400000), "C-Suite": (300000, 500000),
        },
        "descriptions": [
            "Define and drive product strategy that delivers value to users and the business.",
            "Join our product team to shape the roadmap and bring innovative features to market.",
            "Work cross-functionally to identify opportunities and build products users love.",
        ],
        "visa_rate": 0.30,
    },
    "Hospitality": {
        "department": "Hospitality & Tourism",
        "roles": {
            "Intern": [
                "Hospitality Intern", "Hotel Management Intern",
                "Event Planning Intern", "Tourism Intern",
            ],
            "Entry": [
                "Front Desk Agent", "Guest Services Associate",
                "Reservations Agent", "Bellhop", "Concierge",
                "Restaurant Host", "Barista", "Banquet Server",
                "Housekeeper", "Room Attendant",
            ],
            "Mid": [
                "Hotel Manager", "Restaurant Manager", "Event Coordinator",
                "Catering Manager", "Revenue Manager", "Night Auditor",
                "Food & Beverage Manager", "Head Chef", "Sous Chef",
                "Sommelier", "Travel Agent", "Tour Operator",
                "Convention Services Manager", "Spa Manager",
                "Guest Relations Manager", "Wedding Planner",
            ],
            "Senior": [
                "Senior Hotel Manager", "Senior Event Manager",
                "Senior Revenue Manager", "Executive Chef",
                "Senior Catering Director", "Senior Travel Consultant",
            ],
            "Lead": [
                "Lead Event Planner", "Lead Revenue Analyst",
                "Head Concierge",
            ],
            "Manager": [
                "General Manager", "Operations Manager",
                "Front Office Manager", "Housekeeping Manager",
                "Food & Beverage Director", "Sales & Events Manager",
            ],
            "Director": [
                "Director of Hospitality", "Director of Events",
                "Director of Food & Beverage", "Director of Revenue Management",
            ],
            "VP": ["VP of Hospitality", "VP of Operations"],
        },
        "skills_pool": [
            "Guest Relations", "Hospitality Management", "Front Desk Operations",
            "Revenue Management", "Property Management Systems", "Opera PMS",
            "Event Planning", "Banquet Coordination", "Catering",
            "Food & Beverage Operations", "Menu Planning", "Food Safety",
            "ServSafe", "Hotel Operations", "Housekeeping Management",
            "Reservation Systems", "Customer Service", "Conflict Resolution",
            "Budget Management", "Staff Scheduling", "Inventory Control",
            "Sales & Marketing", "Social Media Marketing", "Tourism Marketing",
            "Wine Knowledge", "Culinary Arts", "Pastry Making",
            "Wedding Planning", "Conference Planning", "Travel Planning",
            "Multi-language Communication", "Luxury Service",
        ],
        "salary_ranges": {
            "Intern": (25000, 35000), "Entry": (28000, 42000),
            "Mid": (40000, 70000), "Senior": (60000, 100000),
            "Lead": (70000, 110000), "Manager": (75000, 130000),
            "Director": (100000, 180000), "VP": (140000, 260000),
        },
        "descriptions": [
            "Create memorable guest experiences in a world-class hospitality environment.",
            "Join our team to deliver exceptional service and elevate every guest interaction.",
            "Manage hotel operations to ensure seamless guest satisfaction and operational excellence.",
            "Plan and execute unforgettable events that exceed client expectations.",
            "Lead food and beverage operations to deliver culinary excellence and outstanding service.",
            "Drive revenue growth through innovative hospitality strategies and guest engagement.",
            "Support tourism operations and create unique travel experiences for guests worldwide.",
        ],
        "visa_rate": 0.10,
    },
}

# ── Companies ────────────────────────────────────────────────

COMPANIES = {
    "Technology": [
        # Famous companies
        "Google", "Meta", "Apple", "Amazon", "Netflix", "Microsoft",
        "Nvidia", "Salesforce", "Adobe", "Uber", "Lyft", "Airbnb",
        "Stripe", "Square", "Coinbase", "Databricks", "Palantir",
        "LinkedIn", "Twitter", "Snap", "Pinterest", "Reddit",
        "Shopify", "Figma", "Notion", "Slack", "Dropbox", "Zoom",
        "Oracle", "Intel", "Cisco", "VMware", "ServiceNow",
        # Startups & mid-size
        "Decimal AI", "NovaTech", "Quantum Labs", "CloudNine Systems",
        "DataStream Inc", "PulseIO", "ByteForge", "NeuralPath",
        "CipherStack", "Orion Software", "VelocityAI", "Apex Digital",
        "SkyBridge Tech", "Lumina Labs", "TerraCode", "Nexus Engineering",
        "StackBridge", "CodeVault", "InfinityLoop", "DevHorizon",
    ],
    "Data Science & AI": [
        "Google DeepMind", "OpenAI", "Anthropic", "Meta AI", "Nvidia",
        "Databricks", "Snowflake", "Palantir", "Scale AI", "Hugging Face",
        "Decimal AI", "NeuralPath", "VelocityAI", "DeepMind Analytics",
        "Cortex AI", "Synapse Labs", "DataPrime", "AlgoVerse",
        "TensorForge", "Insight Engine", "BrainWave AI", "CogniTech",
    ],
    "Healthcare": [
        "Bay Area Medical Center", "Unity Healthcare", "Pacific Health Network",
        "Sunrise Medical Group", "Horizon Hospital", "CareFirst Clinic",
        "MedVita Systems", "HealthBridge Partners", "Cascade Health",
        "Summit Medical", "Beacon Health", "Pinnacle Healthcare",
        "Wellness First", "LifeCare Medical", "Providence Health",
        "Mercy General Hospital", "St. Josephs Medical Center",
        "Valley Health System", "Coastal Medical Group",
        "Northside Nursing Center", "Metro Dental Associates",
    ],
    "Finance": [
        "Meridian Capital", "Atlas Financial", "Pinnacle Investment Group",
        "SilverOak Partners", "Granite Financial", "Keystone Advisors",
        "Summit Wealth Management", "Redwood Securities", "Vanguard Capital",
        "Ironclad Finance", "Crestline Partners", "Harbor Financial",
    ],
    "Design": [
        "Decimal AI", "CreativeForge", "PixelCraft Studio",
        "DesignHub Agency", "Artisan Digital", "FormLab",
    ],
    "Marketing": [
        "GrowthSpark", "BrightPath Marketing", "Catalyst Agency",
        "ReachMedia", "Vantage Marketing", "Pulse Digital",
    ],
    "Sales": [
        "Decimal AI", "SalesForward", "RevenueFirst",
        "Pipeline Partners", "CloserHQ", "DealPoint",
    ],
    "Education": [
        "EduTech Academy", "BrightMinds Institute", "LearnPath",
        "Horizon Education", "NextGen Learning", "Scholaria",
    ],
    "Legal": [
        "Whitfield & Associates", "Sterling Law Group",
        "Harmon Legal Partners", "Pacific Legal Counsel",
        "Crestview Law Firm", "Meridian Compliance Group",
        "Blackstone Legal", "Summit Legal Advisors",
        "Golden Gate Law Group", "Ironbridge Compliance",
        "Apex Legal Services", "Thornton & Partners",
    ],
    "Operations": [
        "Decimal AI", "OptiFlow Solutions", "StreamLine Ops",
        "Precision Logistics", "CoreBridge Operations",
    ],
    "Manufacturing": [
        "Precision Manufacturing Co", "SteelPoint Industries",
        "Vanguard Engineering", "Atlas Fabrication",
        "Summit Manufacturing", "TerraForge",
    ],
    "Real Estate": [
        "Summit Properties", "Keystone Real Estate",
        "Metro Development Group", "Urban Edge Realty",
    ],
    "Media": [
        "Bright Media Group", "Cascade Studios",
        "Echo Entertainment", "NovaStar Productions",
    ],
    "HR": [
        "Decimal AI", "TalentBridge", "PeopleFirst HR",
        "Greenfield Consulting",
    ],
    "Product": [
        "Decimal AI", "ProductForge", "LaunchPad",
        "Catalyst Product Studio", "NovaTech", "CloudNine Systems",
        "VelocityAI", "ByteForge", "Apex Digital",
    ],
    "Hospitality": [
        "Grand Horizon Hotel", "The Ritz Collection", "Oceanview Resorts",
        "Summit Lodge", "Metropolitan Hotel Group", "Azure Bay Resort",
        "Starlight Events", "Royal Palms Hotel", "Crescent Hotels",
        "Heritage Hospitality Group", "Peak Event Management",
        "Sapphire Restaurant Group", "Meridian Catering Co",
    ],
}

LOCATIONS = [
    # USA (20)
    "San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA",
    "Boston, MA", "Chicago, IL", "Denver, CO", "Los Angeles, CA",
    "Miami, FL", "Atlanta, GA", "Portland, OR", "Houston, TX",
    "Phoenix, AZ", "Nashville, TN", "Dallas, TX",
    "Raleigh, NC", "Philadelphia, PA", "San Diego, CA",
    "San Jose, CA", "Washington, DC",
    # UK (3)
    "London, UK", "Manchester, UK", "Edinburgh, UK",
    # Canada (3)
    "Toronto, Canada", "Vancouver, Canada", "Montreal, Canada",
    # India (4)
    "Bangalore, India", "Mumbai, India", "Hyderabad, India", "Delhi, India",
    # Australia (2)
    "Sydney, Australia", "Melbourne, Australia",
    # Europe (3)
    "Berlin, Germany", "Amsterdam, Netherlands", "Dublin, Ireland",
    # Asia-Pacific (3)
    "Singapore", "Tokyo, Japan", "Seoul, South Korea",
]

REMOTE_TYPES = ["On-site", "Remote", "Hybrid"]
REMOTE_WEIGHTS = [0.35, 0.35, 0.30]

COMPANY_SIZES = ["1-50", "51-200", "201-1000", "1001-5000", "5000+"]

RECRUITER_FIRST_NAMES = [
    "Sarah", "Mike", "Emily", "James", "Jessica", "David", "Amanda",
    "Chris", "Rachel", "Alex", "Lauren", "Ryan", "Megan", "Brian",
    "Ashley", "Kevin", "Jennifer", "Matt", "Lisa", "Tom",
]

RECRUITER_LAST_NAMES = [
    "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas",
    "Hernandez", "Moore", "Martin", "Lee", "Clark", "Lewis",
]

RECRUITER_ROLES = [
    "Technical Recruiter", "Senior Recruiter", "Talent Acquisition Specialist",
    "Recruiting Manager", "HR Coordinator", "People Operations",
]

LEVEL_WEIGHTS = {
    "Intern": 0.08, "Entry": 0.22, "Mid": 0.28, "Senior": 0.20,
    "Lead": 0.09, "Manager": 0.06, "Director": 0.04,
    "VP": 0.02, "C-Suite": 0.01,
}

INDUSTRY_TARGETS = {
    "Technology": 2500, "Data Science & AI": 1000,
    "Healthcare": 800, "Finance": 600,
    "Design": 400, "Marketing": 500, "Sales": 500,
    "Education": 400, "Legal": 600, "Operations": 500,
    "Manufacturing": 400, "Real Estate": 300, "Media": 300,
    "HR": 300, "Product": 400, "Hospitality": 400,
}

# Requirements/responsibilities templates
REQ_TEMPLATES = {
    "Technology": [
        "{years}+ years of experience in software development",
        "Proficiency in {skill1} and {skill2}",
        "Experience with {skill3} or similar technologies",
        "Strong understanding of data structures and algorithms",
        "Experience building and deploying production systems",
        "Excellent problem-solving and communication skills",
        "Bachelor's degree in Computer Science or related field, or equivalent experience",
        "Experience with version control systems (Git)",
        "Familiarity with CI/CD pipelines and DevOps practices",
    ],
    "Data Science & AI": [
        "{years}+ years of experience in data science or machine learning",
        "Strong proficiency in {skill1} and {skill2}",
        "Experience with {skill3} or similar ML frameworks",
        "Solid foundation in statistics, probability, and linear algebra",
        "Experience deploying ML models to production environments",
        "Ability to communicate complex technical findings to non-technical audiences",
        "MS or PhD in Computer Science, Statistics, or related quantitative field preferred",
        "Experience with experiment design and A/B testing",
        "Familiarity with MLOps practices and model monitoring",
    ],
    "Legal": [
        "{years}+ years of legal experience in relevant practice area",
        "Strong {skill1} and {skill2} skills",
        "Experience with {skill3} or related legal domains",
        "Excellent legal writing and research abilities",
        "J.D. from an accredited law school and active bar membership",
        "Ability to manage multiple cases and meet deadlines",
        "Strong analytical and critical thinking skills",
        "Experience with legal research tools and case management systems",
    ],
    "Healthcare": [
        "{years}+ years of clinical or healthcare experience",
        "Proficiency in {skill1} and {skill2}",
        "Current licensure/certification in relevant specialty",
        "Experience with {skill3} or similar healthcare systems",
        "Strong patient communication and empathy skills",
        "Knowledge of HIPAA regulations and compliance requirements",
        "Ability to work in fast-paced clinical environments",
        "BLS/CPR certification required",
    ],
    "Hospitality": [
        "{years}+ years of experience in hospitality or related field",
        "Strong {skill1} and {skill2} skills",
        "Experience with {skill3} or similar hospitality systems",
        "Excellent customer service and communication abilities",
        "Ability to work flexible hours including weekends and holidays",
        "Knowledge of food safety regulations and standards",
        "Experience managing guest complaints and conflict resolution",
        "Strong organizational and multitasking abilities",
    ],
    "_default": [
        "{years}+ years of experience in a similar role",
        "Strong {skill1} skills",
        "Experience with {skill2} and {skill3}",
        "Excellent communication and collaboration skills",
        "Bachelor's degree in a relevant field or equivalent experience",
        "Ability to work independently and in a team environment",
        "Strong attention to detail and organizational skills",
    ],
}

RESP_TEMPLATES = {
    "Technology": [
        "Design, develop, and maintain high-quality software solutions",
        "Collaborate with cross-functional teams to define and implement new features",
        "Write clean, testable, and well-documented code",
        "Participate in code reviews and contribute to engineering best practices",
        "Troubleshoot and resolve complex technical issues",
        "Mentor junior team members and contribute to team growth",
    ],
    "Data Science & AI": [
        "Develop and deploy machine learning models to solve business problems",
        "Analyze large datasets to extract insights and identify patterns",
        "Design and run experiments to validate hypotheses and measure impact",
        "Build and maintain data pipelines and ML infrastructure",
        "Collaborate with engineering and product teams to integrate ML solutions",
        "Present findings and recommendations to stakeholders",
        "Stay current with the latest research in machine learning and AI",
    ],
    "Legal": [
        "Research and analyze legal issues and provide guidance to business teams",
        "Draft, review, and negotiate contracts and legal documents",
        "Ensure compliance with applicable laws, regulations, and policies",
        "Manage litigation and dispute resolution proceedings",
        "Advise on legal risks and develop mitigation strategies",
        "Maintain organized case files and legal documentation",
    ],
    "Healthcare": [
        "Provide direct patient care in accordance with established protocols",
        "Assess patient conditions and develop appropriate care plans",
        "Administer medications and treatments as prescribed",
        "Document patient information accurately in EHR systems",
        "Collaborate with interdisciplinary healthcare teams",
        "Educate patients and families on health conditions and treatments",
        "Maintain compliance with healthcare regulations and safety standards",
    ],
    "Hospitality": [
        "Ensure exceptional guest experiences from check-in to check-out",
        "Manage daily operations including staffing, inventory, and budgets",
        "Handle guest inquiries, complaints, and special requests professionally",
        "Coordinate events and functions to meet client specifications",
        "Maintain high standards of cleanliness, safety, and service quality",
        "Train and develop team members to deliver outstanding hospitality",
        "Monitor revenue metrics and implement strategies for growth",
    ],
    "_default": [
        "Contribute to team goals and organizational objectives",
        "Collaborate with cross-functional teams on key initiatives",
        "Analyze and solve complex problems in your domain",
        "Communicate progress and insights to stakeholders",
        "Stay current with industry trends and best practices",
        "Participate in team meetings and planning sessions",
    ],
}


# ── Generator ────────────────────────────────────────────────


def _generate_posted_date() -> str:
    """Generate a posted date with the planned distribution."""
    today = date.today()
    r = random.random()
    if r < 0.05:        # last 24h
        days_ago = 0
    elif r < 0.20:      # last 7 days
        days_ago = random.randint(1, 6)
    elif r < 0.60:      # last 30 days
        days_ago = random.randint(7, 29)
    else:               # 30-90 days ago
        days_ago = random.randint(30, 89)
    return (today - timedelta(days=days_ago)).isoformat()


def _generate_years_exp(level: str) -> tuple[int | None, int | None]:
    """Generate years of experience range based on level."""
    ranges = {
        "Intern": (0, None), "Entry": (0, 2), "Mid": (2, 5),
        "Senior": (5, 10), "Lead": (7, 12), "Manager": (5, 12),
        "Director": (10, 18), "VP": (12, 20), "C-Suite": (15, None),
    }
    return ranges.get(level, (None, None))


def _pick_skills(pool: list[str], level: str) -> list[str]:
    """Pick a realistic number of skills for the level."""
    counts = {
        "Intern": (3, 5), "Entry": (4, 6), "Mid": (5, 8),
        "Senior": (6, 10), "Lead": (6, 10), "Manager": (5, 8),
        "Director": (4, 7), "VP": (4, 6), "C-Suite": (3, 5),
    }
    lo, hi = counts.get(level, (4, 7))
    n = min(random.randint(lo, hi), len(pool))
    return random.sample(pool, n)


def _generate_requirements(
    industry: str, skills: list[str], level: str, years_min: int | None
) -> list[str]:
    """Generate 4-6 requirements."""
    templates = REQ_TEMPLATES.get(industry, REQ_TEMPLATES["_default"])
    years = years_min or 0
    s = skills + skills  # pad for safety
    reqs = []
    for t in random.sample(templates, min(random.randint(4, 6), len(templates))):
        r = t.format(years=years, skill1=s[0], skill2=s[1], skill3=s[2] if len(s) > 2 else s[0])
        reqs.append(r)
    return reqs


def _generate_responsibilities(industry: str) -> list[str]:
    """Generate 4-6 responsibilities."""
    templates = RESP_TEMPLATES.get(industry, RESP_TEMPLATES["_default"])
    return random.sample(templates, min(random.randint(4, 6), len(templates)))


def _generate_recruiter() -> tuple[str | None, str | None, str | None]:
    """Generate recruiter info (~65% of the time)."""
    if random.random() > 0.65:
        return None, None, None
    first = random.choice(RECRUITER_FIRST_NAMES)
    last = random.choice(RECRUITER_LAST_NAMES)
    role = random.choice(RECRUITER_ROLES)
    email = f"{first.lower()}.{last.lower()}@company.com"
    return f"{first} {last}", role, email


def generate_job(industry_name: str, industry_data: dict, level: str) -> dict:
    """Generate a single job for the given industry and level."""
    roles = industry_data["roles"].get(level)
    if not roles:
        # Fall back to a nearby level
        for fallback in ["Mid", "Senior", "Entry", "Lead", "Manager"]:
            roles = industry_data["roles"].get(fallback)
            if roles:
                level = fallback
                break
    if not roles:
        return {}

    title = random.choice(roles)
    company = random.choice(COMPANIES.get(industry_name, ["Decimal AI"]))
    location = random.choice(LOCATIONS)
    remote_type = random.choices(REMOTE_TYPES, weights=REMOTE_WEIGHTS, k=1)[0]
    skills = _pick_skills(industry_data["skills_pool"], level)
    salary_range = industry_data["salary_ranges"].get(level, (50000, 100000))
    salary_min = random.randint(salary_range[0], max(salary_range[0], salary_range[1] - 10000))
    salary_max = random.randint(salary_min + 10000, max(salary_min + 10000, salary_range[1]))
    visa = random.random() < industry_data.get("visa_rate", 0.25)
    years_min, years_max = _generate_years_exp(level)
    description = random.choice(industry_data["descriptions"])
    requirements = _generate_requirements(industry_name, skills, level, years_min)
    responsibilities = _generate_responsibilities(industry_name)
    rec_name, rec_role, rec_email = _generate_recruiter()
    company_size = random.choice(COMPANY_SIZES)

    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "company": company,
        "department": industry_data["department"],
        "industry": industry_name,
        "location": location,
        "type": "Internship" if level == "Intern" else random.choices(
            ["Full-time", "Part-time", "Contract"],
            weights=[0.78, 0.08, 0.14],
            k=1,
        )[0],
        "level": level,
        "remote_type": remote_type,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": "USD",
        "description": description,
        "requirements": requirements,
        "responsibilities": responsibilities,
        "skills": skills,
        "posted_date": "",  # assigned after shuffle for even distribution
        "visa_sponsorship": visa,
        "years_experience_min": years_min,
        "years_experience_max": years_max,
        "recruiter_name": rec_name,
        "recruiter_role": rec_role,
        "recruiter_email": rec_email,
        "company_size": company_size,
    }


def _migrate_existing_jobs() -> int:
    """Migrate existing 50 jobs from data/jobs.json into SQLite."""
    json_path = Path(__file__).resolve().parent.parent / "data" / "jobs.json"
    if not json_path.exists():
        return 0

    with open(json_path) as f:
        raw_jobs = json.load(f)

    count = 0
    for j in raw_jobs:
        # Map old schema to new
        remote_type = "Remote" if j.get("remote") else "On-site"
        salary = j.get("salary", {})

        job_data = {
            "id": j["id"],
            "title": j["title"],
            "company": j["company"],
            "department": j["department"],
            "industry": _infer_industry(j["department"]),
            "location": j["location"],
            "type": j["type"],
            "level": j["level"],
            "remote_type": remote_type,
            "salary_min": salary.get("min", 0),
            "salary_max": salary.get("max", 0),
            "salary_currency": salary.get("currency", "USD"),
            "description": j["description"],
            "requirements": j.get("requirements", []),
            "responsibilities": j.get("responsibilities", []),
            "skills": j.get("skills", []),
            "posted_date": j.get("postedDate", date.today().isoformat()),
            "visa_sponsorship": random.random() < 0.30,
            "years_experience_min": None,
            "years_experience_max": None,
            "recruiter_name": None,
            "recruiter_role": None,
            "recruiter_email": None,
            "company_size": random.choice(COMPANY_SIZES),
        }

        # Infer years from level
        years_min, years_max = _generate_years_exp(j["level"])
        job_data["years_experience_min"] = years_min
        job_data["years_experience_max"] = years_max

        # Add recruiter for some
        rec_name, rec_role, rec_email = _generate_recruiter()
        job_data["recruiter_name"] = rec_name
        job_data["recruiter_role"] = rec_role
        job_data["recruiter_email"] = rec_email

        insert_job(job_data)
        count += 1

    return count


def _infer_industry(department: str) -> str:
    """Map department names to industry categories."""
    dept_lower = department.lower()
    mapping = {
        "engineering": "Technology",
        "ai": "Data Science & AI",
        "data science": "Data Science & AI",
        "data": "Technology",
        "healthcare": "Healthcare",
        "finance": "Finance",
        "accounting": "Finance",
        "design": "Design",
        "marketing": "Marketing",
        "sales": "Sales",
        "education": "Education",
        "legal": "Legal",
        "operations": "Operations",
        "manufacturing": "Manufacturing",
        "hr": "HR",
        "human resources": "HR",
        "product": "Product",
        "media": "Media",
        "real estate": "Real Estate",
        "hospitality": "Hospitality",
        "tourism": "Hospitality",
        "hotel": "Hospitality",
    }
    for key, val in mapping.items():
        if key in dept_lower:
            return val
    return "Technology"


def seed_database(reset: bool = False) -> int:
    """
    Seed the database with ~10,000 diverse jobs.

    If reset=True, wipes the jobs table first.
    Returns total number of jobs inserted.
    """
    db = get_db()
    init_db(db)

    if reset:
        db.execute("DELETE FROM jobs")
        db.commit()
        print("Cleared existing jobs.")

    existing = get_job_count()
    if existing > 0 and not reset:
        print(f"Database already has {existing} jobs. Use --reset to re-seed.")
        return existing

    # 1. Migrate existing 50 jobs
    migrated = _migrate_existing_jobs()
    print(f"Migrated {migrated} existing jobs from jobs.json")

    # 2. Generate new jobs per industry target (collect first, shuffle, then insert)
    all_jobs: list[dict] = []
    levels = list(LEVEL_WEIGHTS.keys())
    level_weights = list(LEVEL_WEIGHTS.values())

    for industry_name, target_count in INDUSTRY_TARGETS.items():
        industry_data = INDUSTRIES[industry_name]
        remaining = target_count - (migrated if industry_name == "Technology" else 0)
        remaining = max(0, remaining)

        for _ in range(remaining):
            level = random.choices(levels, weights=level_weights, k=1)[0]
            job = generate_job(industry_name, industry_data, level)
            if job:
                all_jobs.append(job)

    # Shuffle all jobs so dates are evenly distributed across industries
    random.shuffle(all_jobs)

    # Now assign posted dates and insert — this ensures every industry
    # gets a fair share of recent dates instead of clustering by industry
    for job in all_jobs:
        job["posted_date"] = _generate_posted_date()
        insert_job(job)

    total = get_job_count()
    print(f"Generated {len(all_jobs)} new jobs. Total in database: {total}")
    return total


# ── CLI ──────────────────────────────────────────────────────

if __name__ == "__main__":
    reset = "--reset" in sys.argv
    random.seed(42)  # reproducible for demos
    seed_database(reset=reset)
