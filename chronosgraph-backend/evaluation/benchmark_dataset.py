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
    }
]
