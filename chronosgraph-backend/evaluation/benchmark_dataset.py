# evaluation/benchmark_dataset.py

BENCHMARK_DATASET = [
    {
        "id": "hr_sick_leave",
        "domain": "HR",
        "doc1": "The company Sick Leave Policy allows for exactly 10 days of paid sick leave per year, effective from January 1, 2024 to December 31, 2025.",
        "doc2": "According to the revised Sick Leave Policy, employees are entitled to 15 days of paid sick leave annually, effective starting June 1, 2024 to December 31, 2026.",
        "query": "How many days of paid sick leave do I get in late 2024?",
        "ground_truth": "There is conflicting information regarding sick leave in late 2024. The original policy states you get 10 days, but a revised policy starting June 1, 2024, states you get 15 days."
    },
    {
        "id": "it_server_ram",
        "domain": "IT Infrastructure",
        "doc1": "The standard server RAM allocation for production environments is exactly 16GB.",
        "doc2": "According to the new infrastructure requirements, all standard servers must be configured with 32GB RAM.",
        "query": "What is the standard RAM allocation for a production server?",
        "ground_truth": "There is a contradiction in the requirements. One document states the standard RAM allocation is 16GB, while a new infrastructure requirement mandates 32GB RAM."
    },
    {
        "id": "legal_ceo_term",
        "domain": "Legal/Corporate",
        "doc1": "John Doe has been appointed as the CEO, serving a term from January 2022 to December 2025.",
        "doc2": "Jane Smith is taking over as the CEO effective June 2024, with a contract running until December 2026.",
        "query": "Who is the CEO of the company in August 2024?",
        "ground_truth": "There is conflicting information about the CEO in August 2024. One document states John Doe serves until December 2025, while another states Jane Smith takes over effective June 2024."
    },
    {
        "id": "engineering_project_alpha",
        "domain": "Engineering",
        "doc1": "Project Alpha launch date is officially Q3 2024. All marketing materials should align with this release schedule.",
        "doc2": "Due to recent delays, Project Alpha is scheduled for Q4 2024. Please update the launch timeline.",
        "query": "When is Project Alpha launching?",
        "ground_truth": "The launch date for Project Alpha is conflicting. It was originally scheduled for Q3 2024, but due to delays, it is now scheduled for Q4 2024."
    },
    {
        "id": "compliance_data_retention",
        "domain": "Compliance",
        "doc1": "Customer logs must be retained for a maximum of 30 days to comply with EU privacy laws.",
        "doc2": "All customer logs must be kept for 5 years as per the new financial auditing requirements.",
        "query": "How long do we need to retain customer logs?",
        "ground_truth": "There is conflicting information regarding customer log retention. Privacy laws mandate a maximum of 30 days, while financial auditing requirements mandate keeping them for 5 years."
    },
    {
        "id": "finance_budget_q3",
        "domain": "Finance",
        "doc1": "The approved budget for Q3 marketing is $50,000.",
        "doc2": "The Q3 marketing budget has been slashed to $20,000 due to budget cuts.",
        "query": "What is the budget for Q3 marketing?",
        "ground_truth": "There is a contradiction regarding the Q3 marketing budget. The approved budget was $50,000, but a separate document states it was slashed to $20,000."
    },
    {
        "id": "facilities_office_move",
        "domain": "Facilities",
        "doc1": "The headquarters relocation to Austin, Texas is finalized for November 2024.",
        "doc2": "The company headquarters will remain in San Francisco through the end of 2025.",
        "query": "Where will the company headquarters be in December 2024?",
        "ground_truth": "There is conflicting information about the headquarters location in December 2024. One document says it will relocate to Austin in November 2024, while another says it will remain in San Francisco through 2025."
    },
    {
        "id": "sales_commission_rate",
        "domain": "Sales",
        "doc1": "The baseline commission rate for enterprise software sales is 10%.",
        "doc2": "Effective immediately, the baseline commission for all enterprise deals has been adjusted to 12%.",
        "query": "What is the commission rate for an enterprise software sale?",
        "ground_truth": "There is a contradiction regarding the commission rate. One source says the baseline is 10%, while another states it has been adjusted to 12%."
    },
    {
        "id": "marketing_brand_colors",
        "domain": "Marketing",
        "doc1": "Our primary brand color for the logo and web headers is Ocean Blue (#0066cc).",
        "doc2": "The design team has updated the primary brand color to Midnight Navy (#000080) for all digital assets.",
        "query": "What is the primary brand color?",
        "ground_truth": "There is conflicting information regarding the primary brand color. The original guidelines specify Ocean Blue (#0066cc), while a design team update specifies Midnight Navy (#000080)."
    },
    {
        "id": "product_api_limit",
        "domain": "Product/API",
        "doc1": "Free tier users are allowed 1000 API requests per day.",
        "doc2": "To prevent abuse, the free tier API limit is strictly capped at 500 requests per day.",
        "query": "How many API requests can a free tier user make in a day?",
        "ground_truth": "There is a contradiction regarding the free tier API limit. One document states the limit is 1000 requests per day, while another says it is capped at 500 requests per day."
    },
    {
        "id": "hr_remote_work",
        "domain": "HR",
        "doc1": "Employees are permitted to work remotely up to 3 days a week.",
        "doc2": "The company is enforcing a strict return-to-office policy requiring employees to be in the office 4 days a week.",
        "query": "How many days can an employee work remotely?",
        "ground_truth": "There is conflicting information about remote work. One policy allows up to 3 days of remote work a week, while a return-to-office policy limits remote work to 1 day a week (requiring 4 days in office)."
    },
    {
        "id": "legal_ip_ownership",
        "domain": "Legal",
        "doc1": "Contractors retain the intellectual property rights to any open-source tools they develop while consulting for us.",
        "doc2": "Our contractor agreement stipulates that the company owns all intellectual property, including open-source tools, developed during the engagement.",
        "query": "Who owns the IP for open-source tools developed by contractors?",
        "ground_truth": "There is a contradiction regarding intellectual property ownership. One clause states contractors retain rights to open-source tools, while another asserts the company owns all IP developed during the engagement."
    },
    {
        "id": "security_password_rotation",
        "domain": "Security",
        "doc1": "All employee passwords must be rotated every 90 days to comply with internal security standards.",
        "doc2": "The new SSO integration means passwords now only need to be rotated every 365 days.",
        "query": "How often must employee passwords be rotated?",
        "ground_truth": "There is conflicting information on password rotation. One standard requires rotation every 90 days, but an update due to SSO states they only need to be rotated every 365 days."
    },
    {
        "id": "facilities_parking_fee",
        "domain": "Facilities",
        "doc1": "Employee parking in the basement garage is provided free of charge.",
        "doc2": "Starting next month, employee parking in the basement garage will cost $50 per month.",
        "query": "How much does employee parking in the basement garage cost?",
        "ground_truth": "There is a contradiction regarding the parking fee. One document states it is free of charge, while another says it will cost $50 per month starting next month."
    },
    {
        "id": "finance_expense_approval",
        "domain": "Finance",
        "doc1": "Expenses under $500 do not require manager approval and are auto-approved.",
        "doc2": "All expenses, regardless of amount, must be reviewed and approved by a direct manager.",
        "query": "Do I need manager approval for a $200 expense?",
        "ground_truth": "There is conflicting information on expense approvals. One policy states expenses under $500 are auto-approved, while another mandates manager approval for all expenses regardless of the amount."
    },
    {
        "id": "engineering_node_version",
        "domain": "Engineering",
        "doc1": "The backend services are standardized on Node.js version 18.x LTS.",
        "doc2": "All backend microservices must be migrated to Node.js version 20.x immediately for security compliance.",
        "query": "What version of Node.js should be used for backend services?",
        "ground_truth": "There is conflicting information about the Node.js version. One standard specifies Node.js 18.x LTS, while a security compliance update mandates immediate migration to Node.js 20.x."
    },
    {
        "id": "sales_discount_limit",
        "domain": "Sales",
        "doc1": "Sales Account Executives can offer a maximum discount of 15% without VP approval.",
        "doc2": "The maximum discretionary discount an Account Executive can offer is capped at 5%.",
        "query": "What is the maximum discount an AE can offer without VP approval?",
        "ground_truth": "There is a contradiction regarding discount limits. One source states Account Executives can offer up to a 15% discount, while another caps the discretionary discount at 5%."
    },
    {
        "id": "hr_holiday_schedule",
        "domain": "HR",
        "doc1": "The office will be closed on December 24th and 25th for the winter holiday.",
        "doc2": "The office will remain open on December 24th for half-day operations, closing only on the 25th.",
        "query": "Is the office closed on December 24th?",
        "ground_truth": "There is conflicting information about the office closure on December 24th. One notice says it will be closed, while another states it will be open for half-day operations."
    },
    {
        "id": "it_laptop_refresh",
        "domain": "IT Infrastructure",
        "doc1": "The standard employee laptop refresh cycle is every 3 years.",
        "doc2": "To reduce costs, the laptop refresh cycle has been extended to every 4 years.",
        "query": "How often can an employee get a new laptop?",
        "ground_truth": "There is a contradiction regarding the laptop refresh cycle. The standard policy says every 3 years, but a cost-reduction update extends it to every 4 years."
    },
    {
        "id": "compliance_training",
        "domain": "Compliance",
        "doc1": "Mandatory anti-bribery training must be completed by all employees within their first 30 days.",
        "doc2": "Anti-bribery training is only required for employees in the Sales and Procurement departments.",
        "query": "Who needs to take the anti-bribery training?",
        "ground_truth": "There is conflicting information on training requirements. One document states all employees must complete it, while another says it is only required for Sales and Procurement."
    },
    {
        "id": "marketing_social_media",
        "domain": "Marketing",
        "doc1": "The company's official Twitter handle is @AcmeCorpGlobal.",
        "doc2": "We have rebranded our social presence; our official Twitter handle is now @AcmeOfficial.",
        "query": "What is the company's official Twitter handle?",
        "ground_truth": "There is conflicting information about the Twitter handle. One source lists @AcmeCorpGlobal, while a rebranding notice lists @AcmeOfficial."
    },
    {
        "id": "product_mobile_app",
        "domain": "Product",
        "doc1": "The new mobile app will only be available on iOS devices at launch.",
        "doc2": "The mobile app will have a simultaneous launch on both iOS and Android platforms.",
        "query": "Which platforms will the new mobile app be available on at launch?",
        "ground_truth": "There is a contradiction regarding the app launch platforms. One document states it will be iOS only, while another states it will launch simultaneously on iOS and Android."
    },
    {
        "id": "security_visitor_policy",
        "domain": "Security",
        "doc1": "Visitors are allowed in the main lobby without a security escort.",
        "doc2": "All non-employees must be escorted by security at all times, including in the lobby area.",
        "query": "Can visitors be in the lobby unescorted?",
        "ground_truth": "There is conflicting information about the visitor policy. One guideline allows visitors in the lobby without an escort, while another mandates security escorts at all times."
    },
    {
        "id": "finance_vendor_payment",
        "domain": "Finance",
        "doc1": "Standard vendor payment terms are Net-30.",
        "doc2": "As part of the new cash flow management strategy, all vendor payments are now Net-60.",
        "query": "What are our standard payment terms for vendors?",
        "ground_truth": "There is a contradiction regarding vendor payment terms. One source states they are Net-30, while a new strategy updates them to Net-60."
    },
    {
        "id": "legal_data_hosting",
        "domain": "Legal",
        "doc1": "All European customer data must be hosted exclusively in Frankfurt data centers.",
        "doc2": "European customer data can be hosted in any AWS region located within the European Union.",
        "query": "Where must European customer data be hosted?",
        "ground_truth": "There is conflicting information on data hosting. One policy strictly requires Frankfurt data centers, while another allows hosting in any EU-based AWS region."
    },
    {
        "id": "engineering_code_review",
        "domain": "Engineering",
        "doc1": "A minimum of one peer approval is required before merging code into the main branch.",
        "doc2": "All pull requests to the main branch now require at least two approvals from senior engineers.",
        "query": "How many approvals are needed to merge a PR?",
        "ground_truth": "There is a contradiction regarding code review requirements. One standard requires a single peer approval, while an updated rule requires two approvals from senior engineers."
    },
    {
        "id": "hr_maternity_leave",
        "domain": "HR",
        "doc1": "The company offers 12 weeks of fully paid maternity leave.",
        "doc2": "Maternity leave benefits have been expanded to provide 16 weeks of fully paid leave.",
        "query": "How many weeks of paid maternity leave are offered?",
        "ground_truth": "There is conflicting information about maternity leave. One policy states 12 weeks are offered, while an update says the benefit has been expanded to 16 weeks."
    },
    {
        "id": "it_vpn_access",
        "domain": "IT Infrastructure",
        "doc1": "VPN access is granted to all full-time employees by default.",
        "doc2": "VPN access is strictly opt-in and must be requested via a ticketing system with manager approval.",
        "query": "How do full-time employees get VPN access?",
        "ground_truth": "There is a contradiction on how VPN access is provisioned. One source says it is granted by default to full-time employees, while another states it must be explicitly requested and approved."
    },
    {
        "id": "marketing_event_sponsorship",
        "domain": "Marketing",
        "doc1": "We are the Gold sponsor for the upcoming TechSummit 2025 conference.",
        "doc2": "Due to budget reallocation, we have downgraded our TechSummit 2025 sponsorship to the Silver tier.",
        "query": "What is our sponsorship tier for TechSummit 2025?",
        "ground_truth": "There is conflicting information about the sponsorship. One document states the company is a Gold sponsor, while another says it was downgraded to the Silver tier."
    },
    {
        "id": "product_support_hours",
        "domain": "Product/Support",
        "doc1": "Live customer support is available 24/7 for all enterprise clients.",
        "doc2": "Enterprise live customer support operates exclusively during standard business hours (9 AM - 5 PM EST).",
        "query": "When is live customer support available for enterprise clients?",
        "ground_truth": "There is a contradiction regarding support hours. One document promises 24/7 availability, while another states it only operates during standard business hours."
    }
]
