"""Registry of every Canadian public-sector tender portal and how leadgen covers it.

status: "auto"   - ingested automatically from an official open-data feed
        "import" - no public feed / bot-protected / login-walled: use saved-search email alerts + CSV export
                   into imports/ (see README)
"""
PORTALS = [
    ("Federal", "CanadaBuys", "https://canadabuys.canada.ca", "auto", "Official open-data CSV, refreshed throughout the day"),
    ("Quebec", "SEAO", "https://seao.gouv.qc.ca", "auto", "OCDS JSON on Données Québec (weekly files)"),
    ("Ontario", "Ontario Tenders Portal (Jaggaer)", "https://ontariotenders.app.jaggaer.com", "import", "JavaScript app, no public feed"),
    ("British Columbia", "BC Bid", "https://www.bcbid.gov.bc.ca", "import", "Browser-check wall; open data has awards only"),
    ("Alberta", "Alberta Purchasing Connection", "https://purchasingconnection.ca", "import", "Free registration; email alerts"),
    ("Saskatchewan", "SaskTenders", "https://sasktenders.ca", "import", "No public feed"),
    ("Manitoba", "Manitoba Tenders (MERX)", "https://www.gov.mb.ca/tenders", "import", "Notices hosted on MERX"),
    ("New Brunswick", "NBON", "https://nbon-rpanb.gnb.ca", "import", "Portal only"),
    ("Nova Scotia", "NS Procurement Portal", "https://novascotia.ca/tenders", "import", "Awards published as open data, open bids are not"),
    ("Prince Edward Island", "PEI Tenders", "https://www.princeedwardisland.ca/tenders", "import", "Blocks automated access"),
    ("Newfoundland and Labrador", "Public Procurement Agency (MERX)", "https://www.merx.com/govnl", "import", "Hosted on MERX"),
    ("Yukon", "Yukon Bid Opportunities", "https://yukon.ca/en/bid-on-government-contract", "import", "Blocks automated access"),
    ("Northwest Territories", "NWT Contract Opportunities", "https://contracts.fin.gov.nt.ca", "import", "No public feed"),
    ("Nunavut", "Nunavut Tenders", "https://www.nunavuttenders.ca", "import", "Portal only"),
    ("Municipal/MASH", "Biddingo", "https://www.biddingo.com", "import", "Municipal, school board, hospital tenders"),
    ("Municipal/MASH", "Bids&Tenders", "https://www.bidsandtenders.com", "import", "Hosts many municipal buyers; Cloudflare-protected"),
    ("Multi-jurisdiction", "MERX", "https://www.merx.com", "import", "Paid aggregator; saved searches export to CSV"),
    ("Multi-jurisdiction", "BIDS Alert Canada", "https://bidsalert.com/canada/home", "import", "Paid aggregator with alerts"),
    ("Multi-jurisdiction", "Tenders On Time", "https://www.tendersontime.com/canada-tenders/", "import", "Paid global aggregator; export results to CSV"),
]
